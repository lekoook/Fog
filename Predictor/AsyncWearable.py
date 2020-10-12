
# Asynchronous Feature Extraction and FoG Detection Module
# Updated on 11/10/2020
# Updated by Glen Goh

from time import sleep
from time import time
from joblib import load
#from constants import *
from queue import Queue

import time
import utils
import numpy as np
import pandas as pd

import sys
import zmq
import threading
import time

# Constants
LEFT_ACCX_INDEX = 0
LEFT_ACCZ_INDEX = 2
WIN_SIZE = 100
SAMPLE_RATE = 50
TEST_RATE = 10
STEP_SIZE = SAMPLE_RATE / TEST_RATE
# Thresholds for Freezing Index in Hz
LB_LOW = 0.5 # Lower bound of locomotion band index
LB_HIGH = 3 # Upper bound of locomotion band index
FB_LOW = 3 # Lower bound of freeze band index
FB_HIGH = 8 # Upper bound of freeze band index

#Data Buffer for incoming sensor data
buffer = Queue()

class readThread(threading.Thread):
    def __init__(self):  
        threading.Thread.__init__(self)

        #  Socket to talk to server
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect("tcp://localhost:5556")

        # Set socket options to subscribe
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "imu")

    def run(self):
        while True:
            string = self.sub.recv_string()
            #print(string) 
            t, ax, ay, az, gx, gy ,gz, mx, my, mz = string.split()
            buffer.put((ax, ay, az, gx, gy ,gz, mx, my, mz))

            
class detectionThread(threading.Thread):
    def __init__(self, clf):
        threading.Thread.__init__(self)
        self.window = []
        if clf == "LDA":
            self.clf = load('/home/pi/Fog-master/Predictor/lda_all.joblib')
        else :
            self.clf = load('/home/pi/Fog-master/Predictor/rf_all.joblib')
        
    def run(self):
        t = time.time()
        while True:
            if time.time() >= t and buffer.qsize() >= STEP_SIZE:
                for i in range(int(STEP_SIZE)+1):
                    ax, ay, az, gx, gy ,gz, mx, my, mz = buffer.get() #need to confirm of subscriber parses as string or value
                    self.window.append([float(ax),float(ay),float(az)])
                #print(len(self.window))
                    #print("%s %s %s %s %s %s %s %s %s" % (ax, ay, az, gx, gy ,gz, mx, my, mz))
                if len(self.window) >= WIN_SIZE:
                    track = time.time()
                    features_window = []
                    sample = np.empty(shape=(1, 3))
                    #Feature Extraction Step 
                    features_window.append(utils.extract_rms(self.window, LEFT_ACCZ_INDEX))
                    features_window.append(utils.extract_std(self.window, LEFT_ACCZ_INDEX))
                    features_window.append(utils.extract_fi_one_side(self.window, LEFT_ACCX_INDEX, LB_LOW , LB_HIGH, FB_LOW, FB_HIGH))
                    #FoG detection Step
                    sample[0] = np.array(features_window)
                    predicted_label = self.clf.predict(sample)
                    elapse = time.time() - track 
                    print("Time Taken:", elapse) 
                    print(predicted_label)
                    print("FoG Prediction:", "FoG" if predicted_label else "No FoG")
                    #Next Window Preparation Step
                    del self.window[:10]

                t += (1/TEST_RATE) #add 100ms for 10Hz detection rate

                
                
#Code Main
print("FoG Detection Started in RF Mode")
rt = readThread()
dt = detectionThread("RF")                
                
rt.start()
dt.start()

rt.join()
dt.join()            
                
                
                
                
                
                
                