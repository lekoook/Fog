#!/usr/bin/python3

import zmq # ZeroMQ
import time
import sys
sys.path.append("..")
import config
from lib.lsm6ds33 import LSM6DS33
from lib.lis3mdl import LIS3MDL

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

    while True:
        try:
            # Read IMU values
            ax, ay, az = accGyro.getAccelerometerRaw()
            gx, gy, gz = accGyro.getGyroscopeRaw()
            mx, my, mz = mag.getMagnetometerRaw()

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