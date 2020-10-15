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
POLL_TIMEOUT = 100 # milliseconds

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
            sockEvents = self.sub.poll(POLL_TIMEOUT, zmq.POLLIN)
            
            if (sockEvents & zmq.POLLIN) > 0:
                string = self.sub.recv_string() 
                t, ax, ay, az, gx, gy ,gz, mx, my, mz = string.split()
                buffer.put((ax, ay, az, gx, gy ,gz, mx, my, mz))
            
class detectionThread(threading.Thread):
    def __init__(self, clf, pubSock: str, pubTopic: str):
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        self.publisher = setupPub(pubSock)
        self.pubTopic = pubTopic
        self.window = []
        self.cadence = []
        if clf == "LDA":
            self.clf = load(config.LDA_JOBLIB_PATH)
        else :
            self.clf = load(config.RF_JOBLIB_PATH)
        
    def run(self):
        t = time.time()
        
        sos = signal.butter(1, [lp,hp], 'bandpass',  output='sos')
        Prev_Peak = 0
        while not self.shutdown.isSet():
            if time.time() >= t and buffer.qsize() >= STEP_SIZE:
                #Updating window with new values
                for i in range(STEP_SIZE):
                    ax, ay, az, gx, gy ,gz, mx, my, mz = buffer.get()
                    self.window.append([float(ax),float(ay),float(az)])
                    self.cadence.append(float(az))
                #Running Prediction
                if len(self.window) >= Win_Size:
                    track = time.time()
                    #Cadence Tracking
                    filtered_data = signal.sosfilt(sos, self.cadence)
                    Peaks, properties = signal.find_peaks(filtered_data)
                    slope = (len(Peaks) - Prev_Peak)/2
                    Prev_Peak = len(Peaks)
                    #Feature Extraction Step 
                    features_window = []
                    sample = np.empty(shape=(1, 3))
                    features_window.append(utils.extract_rms(self.window, 2))
                    features_window.append(utils.extract_std(self.window, 2))
                    features_window.append(utils.extract_fi_one_side(self.window, 0, LB_LOW , LB_HIGH, FB_LOW, FB_HIGH))
                    #FoG detection Step
                    sample[0] = np.array(features_window)
                    predicted_label = self.clf.predict(sample)
                    
                    #Print Prediction output
                    print("Time Taken:", time.time() - track) 
                    print("Cadence Slope:", slope)
                    #print(predicted_label[0])
                    print("FoG Prediction:", "FoG\n" if predicted_label else "No FoG\n")
                    #Publishing FoG Prediction 
                    self.publisher.send_string("%s %i" % (self.pubTopic, predicted_label[0]))
                    #Next Window Preparation Step
                    del self.window[:STEP_SIZE]
                    del self.cadence[:STEP_SIZE]

                t += (1/Test_Rate) #add 100ms for 10Hz detection rate


if __name__ == "__main__":
    try:
        print("FoG Detection Started in RF Mode")
        rt = readThread(config.DATA_SOCK, config.IMU_TOPIC)
        dt = detectionThread("LDA", config.PREDICT_SOCK, config.PREDICT_TOPIC)                
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

                    



                
                
                
                
                
                
                