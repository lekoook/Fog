#!/bin/usr/python3

# Asynchronous Feature Extraction and FoG Detection Module
# Updated on 11/10/2020
# Updated by Glen Goh

from time import sleep
from time import time
from joblib import load
from queue import Queue
from scipy import signal

import time
import sys
import zmq
import threading
import time
import math
import numpy as np
import pandas as pd

import lib.utils as utils
sys.path.append("..")
import config
from lib.constants import *

# Constants
Win_Size = config.WIN_SIZE
Test_Rate = config.TEST_RATE
Sample_Rate = config.SAMPLE_RATE
STEP_SIZE = int(Sample_Rate / Test_Rate)

#Bandpass Filter Constants
fs = 1000
lp = 1/(0.5*fs)
hp = 12/(0.5*fs)

#Data Buffer for incoming sensor data
buffer = Queue()

def setupPub(pubAddr: str) -> zmq.Socket:
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(pubAddr)

    return publisher

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
            t, lax, lay, laz, rax, ray ,raz, gt = string.split()
            buffer.put((lax, lay, laz, rax, ray ,raz, gt))

            
class detectionThread(threading.Thread):
    def __init__(self, clf, pubSock: str, pubTopic: str):
        threading.Thread.__init__(self)
        self.shutdown   = threading.Event()
        self.publisher  = setupPub(pubSock)
        self.pubTopic   = pubTopic
        self.sos        = signal.butter(1, [lp,hp], 'bandpass',  output='sos')
        self.windowL    = []
        self.windowR    = []
        self.cadence    = []
        if clf == "LDA":
            self.clf    = load(config.LDA_JOBLIB_PATH)
        elif clf == "RF" :
            self.clf    = load(config.RF_JOBLIB_PATH)
        
    def run(self):
        t = time.time()
        df = pd.DataFrame()
        results = []
        squaresL = []; sumsquaresL = 0
        squaresR = []; sumsquaresR = 0
        Prev_Peak = 0
        GroundTruth = 0
        while not self.shutdown.isSet():
            if time.time() >= t and buffer.qsize() >= STEP_SIZE:
                #Updating window with new values
                for i in range(STEP_SIZE):
                    lax, lay, laz, rax, ray ,raz, gt = buffer.get()
                    self.windowL.append([float(lax),float(lay),float(laz)])
                    self.windowR.append([float(rax),float(ray),float(raz)])
                    self.cadence.append(float(laz)) 
                    squaresL.append(float(laz)*float(laz))
                    sumsquaresL += squaresL[-1]
                    squaresR.append(float(raz)*float(raz))
                    sumsquaresR += squaresR[-1]
                    if i == (STEP_SIZE-1):
                        GroundTruth = gt #Classifier was trained with last FoG as label

                #Running Prediction
                if len(self.windowL) >= Win_Size:
                    track = time.time()
                    #Cadence Tracking
                    filtered_data = signal.sosfilt(self.sos, self.cadence)
                    Peaks, properties = signal.find_peaks(filtered_data)
                    slope = (len(Peaks) - Prev_Peak)/2
                    Prev_Peak = len(Peaks)
                    #Feature Extraction Step 
                    features_window = []
                    sample = np.empty(shape=(1, 6))
                    #left_Feet FeatExt
                    features_window.append(math.sqrt(sumsquaresL/Win_Size))
                    features_window.append(utils.extract_std_welford(self.windowL, 2))
                    features_window.append(utils.extract_fi_one_side(self.windowL, 0, LB_LOW , LB_HIGH, FB_LOW, FB_HIGH))
                    #right_Feet FeatExt
                    features_window.append(math.sqrt(sumsquaresR/Win_Size))
                    features_window.append(utils.extract_std_welford(self.windowR, 2))
                    features_window.append(utils.extract_fi_one_side(self.windowR, 0, LB_LOW , LB_HIGH, FB_LOW, FB_HIGH))
                    #Generating Features
                    #features_window.append((RMS_L+RMS_R)/2)
                    #features_window.append((STD_L+STD_R)/2)
                    #features_window.append((FI_L+FI_R)/2)
                    #FoG detection Step
                    sample[0] = np.array(features_window)
                    predicted_label = self.clf.predict(sample)
                    #Next Window Preparation Step
                    sumsquaresL -= sum(squaresL[:STEP_SIZE])
                    sumsquaresR -= sum(squaresR[:STEP_SIZE])
                    del self.windowL[:STEP_SIZE]
                    del self.windowR[:STEP_SIZE]
                    del self.cadence[:STEP_SIZE]
                    del squaresL[:STEP_SIZE]
                    del squaresR[:STEP_SIZE]
                    
                    #Print Prediction output
                    elapse = time.time() - track
                    print("Time Taken:", elapse) 
                    #print("Cadence Slope:", slope)
                    print("Predicted value:", predicted_label[0], "| Actual Value:", GroundTruth )
                    results.append({'Compute_Time':elapse, 'predict':predicted_label[0], 'truth':GroundTruth})
                    #Publishing FoG Prediction 
                    self.publisher.send_string("%s %i" % (self.pubTopic, predicted_label[0]))


                t += (1/Test_Rate) #add 100ms for 10Hz detection rate
        
        df = pd.DataFrame(results)
        df.to_csv("./Results/result.csv", index=None, header=True)
        print("Data Exported")

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
  