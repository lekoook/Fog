#!/usr/bin/python3

import zmq
import threading
import time
import signal
import sys
sys.path.append("..")
import config
from Predictor.lib.IMUValue import IMUValue
from Predictor.lib.DataBuffer import DataBuffer

dataBuffer = DataBuffer()

class ReadIMUTh(threading.Thread):
    """
    This thread attempts to read any incoming available IMU values into the given DataBuffer.

    Args:
        threading (Thread): threading.Thread object.
    """

    def __init__(self, subAddr: str, topic: str, buffer: DataBuffer):
        """
        Initialization.

        Args:
            subAddr (str): Socket address for subscription.
            topic (str): Topic to subscribe to.
            buffer (DataBuffer): DataBuffer to store the read values in.
        """

        threading.Thread.__init__(self)

        self.shutdown = threading.Event()
        self.buffer = buffer

        #  Socket to talk to publisher
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect(subAddr)

        # Set socket options to subscribe to IMU topic
        self.sub.setsockopt_string(zmq.SUBSCRIBE, topic)

    def run(self):
        while not self.shutdown.isSet():
            try:
                string = self.sub.recv_string() # TODO: Use zmq.select() to prevent the use of blocking call.
                t, ax, ay, az, gx, gy ,gz, mx, my, mz = string.split()
                value = IMUValue(ax, ay, az, gx, gy ,gz, mx, my, mz)
                self.buffer.push(value)
            except KeyboardInterrupt:
                break

        # Clean up
        context = zmq.Context.instance()
        context.destroy()

class ReadBufferTh(threading.Thread):
    """
    This is an example thread to read values from the given DataBuffer.

    Args:
        threading (Thread): threading.Thread object.
    """
    def __init__(self, buffer: DataBuffer):  
        """
        Initialization.

        Args:
            buffer (DataBuffer): DataBuffer to read from.
        """

        threading.Thread.__init__(self)

        self.shutdown = threading.Event()
        self.buffer = buffer

    def run(self):
        while not self.shutdown.isSet():
            v = self.buffer.pop()
            if v is not None: # If the buffer is empty, the return value would be 'None'
                print("%s %s %s %s %s %s %s %s %s" % (v.ax, v.ay, v.az, v.gx, v.gy ,v.gz, v.mx, v.my, v.mz))

if __name__ == "__main__":
    try:
        readImu = ReadIMUTh(config.DATA_SOCK, config.LOCAL_IMU_TOPIC, dataBuffer)
        readBuf = ReadBufferTh(dataBuffer)
        readImu.start()
        readBuf.start()

        # Let's keep the main thread running to catch ctrl-c terminations.
        while threading.activeCount() > 0:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        readImu.shutdown.set()
        readBuf.shutdown.set()
        readImu.join()
        readBuf.join()
