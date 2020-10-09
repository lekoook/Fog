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
            publisher.send_string("%s %i %i %i %i %i %i %i %i %i" % (topic, ax, ay, az, gx, gy ,gz, mx, my, mz))
            print("'%s': %i %i %i %i %i %i %i %i %i" % (topic, ax, ay, az, gx, gy ,gz, mx, my, mz))

            time.sleep(0.020) # 50hz
        except KeyboardInterrupt:
            break

def pubMock(publisher: zmq.Socket, topic: str, filePath: str):
    #set working directory
    os.chdir(config.MOCK_DATA_FOLDER)
    
    #find all csv files in the folder
    all_filenames = []
    dir_files = os.listdir()
    for f in config.MOCK_DATA_PATHS:
        if f in dir_files:
            all_filenames.append(f)
    print(all_filenames)

    #combine all files in the list
    combined_csv = pd.concat([pd.read_csv(f, header=None) for f in all_filenames ])
    #export to csv
    if os.path.isfile("combined.csv"):
        os.remove("combined.csv")
    combined_csv.to_csv("combined.csv", index=False, encoding='utf-8-sig', header=None)
    stream = open("combined.csv", newline='')
    csvFile = csv.reader(stream, delimiter=',')

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
            r = next(csvFile)
            ax = float(r[1])
            ay = float(r[2])
            az = float(r[3])
            gx = float(r[4])
            gy = float(r[5])
            gz = float(r[6])
            mx = float(r[7])
            my = float(r[8])
            mz = float(r[9])

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
            publisher.send_string("%s %i %i %i %i %i %i %i %i %i" % (topic, ax, ay, az, gx, gy ,gz, mx, my, mz))
            print("'%s': %i %i %i %i %i %i %i %i %i" % (topic, ax, ay, az, gx, gy ,gz, mx, my, mz))

            time.sleep(0.020) # 50hz
        except (KeyboardInterrupt, StopIteration) as e:
            break

    # Clean up
    os.remove("combined.csv")

if __name__ == "__main__":
    setupLog()
    publisher = setupPub(config.DATA_SOCK)
    if config.USE_MOCK_DATA:
        logging.info("Using MOCK data")
        pubMock(publisher, config.IMU_TOPIC, config.MOCK_DATA_PATHS)
    else:
        logging.info("Using REAL data")
        pubData(publisher, config.IMU_TOPIC)

    # Clean up
    context = zmq.Context.instance()
    context.destroy()