#!/bin/usr/python3

# import RPi.GPIO as GPIO
import zmq
import threading
import time
import sys
import os
import builtins
from BluetoothctlWrapper import Bluetoothctl
sys.path.append("..")
import config

# Constants
POLL_TIMEOUT = 100 # milliseconds

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
            sockEvents = self.sub.poll(POLL_TIMEOUT, zmq.POLLIN)

            if (sockEvents & zmq.POLLIN) > 0:
                string = self.sub.recv_string()
                t, state = string.split()
                state = float(state)
                if state == 0.0:
                    isFog = False
                else:
                    isFog = True

        # Clean up
        context = zmq.Context.instance()
        context.destroy()

class PlayAudioTh(threading.Thread):
    """
    This thread will blink the LED according to the current FoG state.

    Args:
        threading (Thread): threading.Thread object.
    """
    LED_PIN = 23 # Broadcom pin 23 is pin 16 on RPi pinout

    def __init__(self):
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        self.bctl = Bluetoothctl()
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.LED_PIN, GPIO.OUT) 
        # GPIO.output(self.LED_PIN, GPIO.LOW)

    def run(self):
        global isFog
        currIsFog = False
        prevIsFog = False
        stopSoundPath = os.getcwd() + "/" + config.SOUNDS_FOLDER + config.STOP_SOUND_PATH
        stopCmd = "aplay -D speaker " + stopSoundPath # Play on speaker
        #stopCmd = "aplay -D mid " + stopSoundPath # Play on headphone

        while not self.shutdown.isSet():
            try:
                # Check if the headphone is connected, if not attempt to connect until it can connected.
                if not self.isHeadphoneConnected():
                    self.print("Headphone is disconnected")
                    self.setupHeadphone()
                    
                currIsFog = isFog
                #if isFog and not GPIO.input(self.LED_PIN):
                if currIsFog and not prevIsFog:
                    self.print("On")
                    
                if currIsFog:
                    # Turn LED for 1 second and turn off again.
                    #GPIO.output(self.LED_PIN, GPIO.HIGH)
                    os.system(stopCmd)
                    time.sleep(1)
                
                #if not isFog and GPIO.input(self.LED_PIN):
                if not currIsFog and prevIsFog:
                    # GPIO.output(self.LED_PIN, GPIO.LOW)
                    self.print("Off")
                
                prevIsFog = currIsFog
                time.sleep(0.1)
            except KeyboardInterrupt:
                break

    def setupHeadphone(self):
        self.print("Attempting to connect to headphone: ", config.HEADPH_MAC)
        while not self.bctl.connect(config.HEADPH_MAC):
            time.sleep(0.5)
        self.print("Headphone %s is now connected" % config.HEADPH_MAC)

    def isHeadphoneConnected(self):
        return self.bctl.isConnected(config.HEADPH_MAC)

    def print(self, *objs, **kwargs):
        builtins.print(self.printPrefix, *objs, **kwargs)

if __name__ == "__main__":
    try:
        readState = ReadStateTh(config.PREDICT_SOCK, config.PREDICT_TOPIC)
        audio = PlayAudioTh()
        readState.start()
        audio.start()

        # Let's keep the main thread running to catch ctrl-c terminations.
        while threading.activeCount() > 0:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        readState.shutdown.set()
        audio.shutdown.set()
        readState.join()
        audio.join()
        
