#!/usr/bin/python3

import zmq # ZeroMQ
import time
import datetime
import sys
import logging
import csv
import os
import glob
import pandas as pd
sys.path.append("..")
import config
from DataProvider.lib.lsm6ds33 import LSM6DS33
from DataProvider.lib.lis3mdl import LIS3MDL
from DataProvider.lib.MedianFilter import MedianFilter

def setupLog():
    if not os.path.isdir(config.LOG_FOLDER):
        os.makedirs(config.LOG_FOLDER) 

    now = datetime.datetime.now()
    logging.basicConfig(
        filename=config.LOG_FILE_PREFIX 
        + now.strftime("%d%m%Y_%H%M%S%f"))

def setupPub(pubAddr: str) -> zmq.Socket:
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(pubAddr)

    return publisher

def pubData(publisher: zmq.Socket, topic: str):
    # Create IMU objects
    accGyro = LSM6DS33()
    accGyro.enableLSM()
    mag = LIS3MDL()
    mag.enableLIS()

    if config.USE_MEDIAN_FILTER:
        # Median Filters
        axF = MedianFilter(config.MF_WINDOW_SIZE)
        ayF = MedianFilter(config.MF_WINDOW_SIZE)
        azF = MedianFilter(config.MF_WINDOW_SIZE)
        gxF = MedianFilter(config.MF_WINDOW_SIZE)
        gyF = MedianFilter(config.MF_WINDOW_SIZE)
        gzF = MedianFilter(config.MF_WINDOW_SIZE)
        mxF = MedianFilter(config.MF_WINDOW_SIZE)
        myF = MedianFilter(config.MF_WINDOW_SIZE)
        mzF = MedianFilter(config.MF_WINDOW_SIZE)

    while True:
        try:
            # Read IMU values
            ax, ay, az = accGyro.getAccelerometerRaw()
            gx, gy, gz = accGyro.getGyroscopeRaw()
            mx, my, mz = mag.getMagnetometerRaw()

            if config.USE_MEDIAN_FILTER:
                # Go through median filters
                ax = int(axF.filt(ax))
                ay = int(ayF.filt(ay))
                az = int(azF.filt(az))
                gx = int(gxF.filt(gx))
                gy = int(gyF.filt(gy))
                gz = int(gzF.filt(gz))
                mx = int(mxF.filt(mx))
                my = int(myF.filt(my))
                mz = int(mzF.filt(mz))

            # Publish onto topic
            #publisher.send_string("%s %i %i %i %i %i %i %i %i %i" % (topic, ax, ay, az, gx, gy ,gz, mx, my, mz))
            publisher.send_string("%s %i %i %i %i %i %i %i %i %i %i %i %i %i" % (topic, gx, gy, gz, ax, ay, az, gx, gy, gz, ax, ay, az, 0))
            print("'%s': %i %i %i %i %i %i %i %i %i" % (topic, ax, ay, az, gx, gy ,gz, mx, my, mz))

            time.sleep(0.020) # 50hz
        except KeyboardInterrupt:
            break

def pubMock(publisher: zmq.Socket, topic: str, filePath: str):

    left_data = []
    right_data = []
    
    for root, dirs, files in os.walk(config.MOCK_DATA_FOLDER, topdown=False):
        for folder in dirs:
            cwd = os.getcwd() + "/"
            os.chdir(cwd + os.path.join(root, folder))
            print(os.getcwd())
            print("Testing on trial data:", folder)

            #Getting left and right data readings
            for file in os.listdir():
                if 's2.csv' in file:
                    left_data.append(file)
                if 's3.csv' in file:
                    right_data.append(file)

            #combine all files in the list
            left_csv = pd.concat([pd.read_csv(f, header=None, skiprows = 1) for f in left_data])
            right_csv = pd.concat([pd.read_csv(f, header=None, skiprows = 1) for f in right_data])
            #export to csv
            if os.path.isfile("left_data.csv"):
                os.remove("left_data.csv")
            if os.path.isfile("right_data.csv"):
                os.remove("right_data.csv")            
            left_csv.to_csv("left_data.csv", index=False, encoding='utf-8-sig', header=None)
            right_csv.to_csv("right_data.csv", index=False, encoding='utf-8-sig', header=None)

            #Creating L and R feet data streams        
            L_stream = open("left_data.csv", newline='')
            L_csvFile = csv.reader(L_stream, delimiter=',')

            R_stream = open("right_data.csv", newline='')
            R_csvFile = csv.reader(R_stream, delimiter=',')
           

            # Wait for Predictor to be ready for data
            context = zmq.Context()
            client = context.socket(zmq.REQ)
            client.connect(config.PREDICT_READY_SOCK)
            request = "Ready?".encode()
            print("Waiting for Predictor to be ready...")
            client.send(request)
            
            if (client.poll() & zmq.POLLIN) != 0:
                reply = client.recv().decode()
                if reply == "Yes":
                    print("Predictor is ready!")
                
            if config.WAIT_FOR_USER:
                userInput = input("Press something to start...")

            print("Publishing data")
            while True:
                try:
                    # Read IMU values from left and right data stream from CSV files
                    l = next(L_csvFile)
                    r = next(R_csvFile)
                    lwx = float(l[1]); lwy = float(l[2]); lwz = float(l[3])
                    lax = float(l[4]); lay = float(l[5]); laz = float(l[6])
                    rwx = float(r[1]); rwy = float(r[2]); rwz = float(r[3])
                    rax = float(r[4]); ray = float(r[5]); raz = float(r[6])
                    gt = float(r[10])

                    # Publish onto topic
                    publisher.send_string("%s %i %i %i %i %i %i %i %i %i %i %i %i %i" % (topic, lwx,lwy,lwz,lax,lay,laz, rwx,rwy,rwz,rax,ray,raz, gt))
                    #print("%s %i %i %i %i %i %i %i %i %i %i %i %i %i" % (topic, lwx,lwy,lwz,lax,lay,laz, rwx,rwy,rwz,rax,ray,raz, gt))

                    time.sleep(0.020) # 50hz
                except (KeyboardInterrupt, StopIteration) as e:
                    break

            # Clean up
            os.remove("left_data.csv")
            os.remove("right_data.csv")

if __name__ == "__main__":
    setupLog()
    publisher = setupPub(config.DATA_SOCK)
    if config.USE_MOCK_DATA:
        logging.info("Using MOCK data")
        pubMock(publisher, config.LOCAL_IMU_TOPIC, config.MOCK_DATA_PATHS)
    else:
        logging.info("Using REAL data")
        pubData(publisher, config.LOCAL_IMU_TOPIC)

    # Clean up
    context = zmq.Context.instance()
    context.destroy()
