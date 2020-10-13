#!/bin/usr/python3

import RPi.GPIO as GPIO
import zmq
import threading
import time
import sys
sys.path.append("..")
import config

# State flag to indicate if FoG is occuring.
isFog = False

class ReadStateTh(threading.Thread):
    """
    This thread attempts to read any incoming predicted state.

    Args:
        threading (Thread): threading.Thread object.
    """

    def __init__(self, subAddr: str, topic: str):
        """
        Initialization.

        Args:
            subAddr (str): Socket address for subscription.
            topic (str): Topic to subscribe to.
        """

        threading.Thread.__init__(self)

        self.shutdown = threading.Event()

        # Socket to talk to publisher
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect(subAddr)

        # Set socket options to subscribe to IMU topic
        self.sub.setsockopt_string(zmq.SUBSCRIBE, topic)

    def run(self):
        global isFog

        while not self.shutdown.isSet():
            string = self.sub.recv_string()
            t, state = string.split()
            if state is "0":
                isFog = False
            else:
                isFog = True

        # Clean up
        context = zmq.Context.instance()
        context.destroy()

class BlinkTh(threading.Thread):
    """
    This thread will blink the LED according to the current FoG state.

    Args:
        threading (Thread): threading.Thread object.
    """
    LED_PIN = 23 # Broadcom pin 23 is pin 16 on RPi pinout

    def __init__(self):
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.LED_PIN, GPIO.OUT) 
        GPIO.output(self.LED_PIN, GPIO.LOw)

    def run(self):
        global isFog

        while not self.shutdown.isSet():
            if isFog:
                # Turn LED for 1 second and turn off again.
                GPIO.output(self.LED_PIN, GPIO.HIGH)
                print("On")
                time.sleep(1)
            else:
                GPIO.output(self.LED_PIN, GPIO.LOW)
                print("Off")

if __name__ == "__main__":
    try:
        readState = ReadStateTh(config.PREDICT_SOCK, config.PREDICT_TOPIC)
        blink = BlinkTh()
        readState.start()
        blink.start()

        # Let's keep the main thread running to catch ctrl-c terminations.
        while threading.activeCount() > 0:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        readState.shutdown.set()
        blink.shutdown.set()
        readState.join()
        blink.join()
        