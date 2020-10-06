#!/usr/bin/python3

import zmq # ZeroMQ
import time
import sys
sys.path.append("..")
import config
from DataProvider.lib.lsm6ds33 import LSM6DS33
from DataProvider.lib.lis3mdl import LIS3MDL
from DataProvider.lib.MedianFilter import MedianFilter

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

if __name__ == "__main__":
    publisher = setupPub(config.DATA_SOCK)
    pubData(publisher, config.IMU_TOPIC)

    # Clean up
    context = zmq.Context.instance()
    context.destroy()