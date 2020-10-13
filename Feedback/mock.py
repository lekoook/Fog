#!/usr/bin/python3

import zmq # ZeroMQ
import time
import sys
import os
sys.path.append("..")
import config

def setupPub(pubAddr: str) -> zmq.Socket:
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(pubAddr)

    return publisher

def pubData(publisher: zmq.Socket, topic: str):
    while True:
        for i in range(100):
            publisher.send_string("%s 1" % topic)
            time.sleep(0.10) # 10hz
        for i in range(100):
            publisher.send_string("%s 0" % topic)
            time.sleep(0.10) # 10hz


if __name__ == "__main__":
    publisher = setupPub(config.PREDICT_SOCK)
    pubData(publisher, config.PREDICT_TOPIC)

    # Clean up
    context = zmq.Context.instance()
    context.destroy()
