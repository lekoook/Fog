#!/bin/usr/python3

'''
# Final FoG Prediction Module Build #
Updated on 04/04/2021
Updated by Glen Goh
== Inputs ==
Recieves inputs from DataProvider Module via the IMU topic addressed in DATA_SOCK in the config File
Data Recieved from DataProvider: 
Left_Foot_Ang_Vel (X/Y/Z) ; Left_Foot_Acceleration (X/Y/Z) ;
Right_Foot_Ang_Vel (X/Y/Z) ; Right_Foot_Acceleration (X/Y/Z) ; 
Ground Truth (if available)
== Outputs == 
Sends prediction outputs to Feedback Module to drive biofeedback via Predict topic addressed in PREDICT_SOCK in the config File
Data sent to Feedback: 
Walk predicted    :  Data sent = 0
Pre-FoG predicted :  Data sent = 0.5
FoG predicted     :  Data sent = 1
'''

#Importing Essential librarys
from time import sleep
from time import time
from joblib import load
from queue import Queue
import numpy as np
import pandas as pd
import time
import sys
import zmq
import threading
import time
import math
import config
from lib.constants import *
import lib.utils as utils
sys.path.append("..")

# Obtaining constant values from Config File
Win_Size = config.WIN_SIZE
Test_Rate = config.TEST_RATE
Sample_Rate = config.SAMPLE_RATE
STEP_SIZE = int(Sample_Rate / Test_Rate)

#Data Buffer for incoming sensor data
buffer = Queue()

#Publisher function setup
def setupPub(pubAddr: str) -> zmq.Socket:
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(pubAddr)

    return publisher

#Data Reading Thread (Reads IMU data from IMU topic)
class readThread(threading.Thread):
    def __init__(self, sockAddr: str, topic: str):  
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        #  Socket to talk to server
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect(sockAddr)
        # Set socket options to subscribe
        self.sub.setsockopt_string(zmq.SUBSCRIBE, topic)

    def run(self):
        while not self.shutdown.isSet():
            string = self.sub.recv_string()
            topic,lwx,lwy,lwz,lax,lay,laz,rwx,rwy,rwz,rax,ray,raz,gt = string.split()
            #Inserts incoming IMU data into buffer
            buffer.put((lwx,lwy,lwz,lax,lay,laz,rwx,rwy,rwz,rax,ray,raz,gt))

#FoG State Classification Thread (Predicts FoG state from IMU data)            
class detectionThread(threading.Thread):
    def __init__(self, clf, pubSock: str, pubTopic: str):
        threading.Thread.__init__(self)
        self.shutdown   = threading.Event()
        self.publisher  = setupPub(pubSock)
        self.pubTopic   = pubTopic
        # Container for gait observation window
        self.window     = []
        # Staging offline trained classifier and scaler function 
        self.scl_D    = load(config.SCL_D_JOBLIB_PATH)
        self.clf_D    = load(config.MLP_D_JOBLIB_PATH)
        self.scl_P    = load(config.SCL_P_JOBLIB_PATH)
        self.clf_P    = load(config.MLP_P_JOBLIB_PATH)
        
    def run(self):
        #Clock variable to maintain 0.1s cycle
        t = time.time()
        #Repeating prediction code
        while not self.shutdown.isSet():
            #Running Prediction Cycle at 10Hz
            if time.time() >= t and buffer.qsize() >= STEP_SIZE:
                #obtain start time of prediction cycle
                k1 = time.time()

                #Updating window with new values from buffer
                for i in range(STEP_SIZE):
                    lwx,lwy,lwz,lax,lay,laz,rwx,rwy,rwz,rax,ray,raz,gt = buffer.get()
                    self.window.append([float(lwx),float(lwy),float(lwz),
                                        float(lax),float(lay),float(laz),
                                        float(rwx),float(rwy),float(rwz),
                                        float(rax),float(ray),float(raz)])
                    if i == (STEP_SIZE-1):
                        truth = gt

                #Running Feature extraction and state prediction
                if len(self.window) >= Win_Size:

                    #Feature Extraction Step
                    Dect_features = []
                    Pred_features = []
                    Pred_features, Dect_features = utils.extract_sepfeat(self.window)

                    #Predicting Pre-FoG state
                    sample = np.empty(shape=(1, 16))
                    sample[0] = np.array(Pred_features)
                    scaled_test = self.scl_P.transform(sample)
                    PreFoG_Label = self.clf_P.predict(scaled_test)

                    #Predicting FoG state
                    sample = np.empty(shape=(1, 16))
                    sample[0] = np.array(Dect_features)
                    scaled_test = self.scl_D.transform(sample)
                    Dect_Label = self.clf_D.predict(scaled_test)

                    #Combining Prediction and Detection outputs into a Single Output
                    if PreFoG_Label == 0 and Dect_Label == 0: 
                        predicted_label = 0
                    elif PreFoG_Label == 2 and Dect_Label == 0: 
                        predicted_label = 0.5
                    elif Dect_Label == 1:
                        predicted_label = 1
                    else:
                        predicted_label = 0

                    #Sending Predicted output to Feedback Module
                    self.publisher.send_string("%s %f" % (self.pubTopic, predicted_label))

                    #Cleaning up window for next computation cycle
                    del self.window[:STEP_SIZE]

                    # Obtaining computational time performance  
                    Total_time = time.time() - k1
                    # Print output and total computational time of prediction cycle                                    
                    print(Total_time, 's : Predicted =', predicted_label, '| Actual =', truth )

                t += (1/Test_Rate) #add 100ms for 10Hz detection rate


if __name__ == "__main__":
    try:
        print("FoG Detection Started in", config.PREDICT_MODE, "Mode")
        rt = readThread(config.DATA_SOCK, config.IMU_TOPIC)
        dt = detectionThread(config.PREDICT_MODE, config.PREDICT_SOCK, config.PREDICT_TOPIC)              
        rt.start()
        dt.start()
        
        # Let's keep the main thread running to catch ctrl-c terminations.
        while threading.activeCount() > 0:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        rt.shutdown.set()
        dt.shutdown.set()
        rt.join()
        dt.join()

        # Clean up
        context = zmq.Context.instance()
        context.destroy()      
