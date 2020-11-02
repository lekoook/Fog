#!/bin/usr/python3
from bluepy.btle import *
from queue import Queue, Empty
import zmq
import threading
import builtins
import traceback
import sys
import csv
import os
import glob
import pandas as pd
sys.path.append("..")
import config
from DataProvider.lib.crc8 import crc8

# User Configurations
FEATHER_NAME = config.BLE_DEV_NAME
# BLE services/characteristics to watch
DATA_SVC_UUID = config.BLE_DATA_SVC_UUID
DATA_CHAR_UUID = config.BLE_DATA_CHAR_UUID

# BLE Configurations
SCAN_TIMEOUT = config.BLE_SCAN_TIMEOUT

# BLE specfifications default values
ADT_COMPLETE_NAME = 0x09
UUID_CCCD = "00002902"
NOTIF_ON = b"\x01\x00" # Also turns off indication
NOTIF_OFF = b"\x00\x00" # Also turns off indication

# Message values
START_BYTE = b"\xff"
MSG_LEN = 38
FIELD_LEN = 4 # Float is 4 bytes

# Exit codes
SUCCESS = 0
DEVICE_NOT_FOUND = 1
DATA_SERVICE_NOT_FOUND = 2
DATA_CHARACTERISTIC_NOT_FOUND = 3
CCCD_NOT_FOUND = 4

SEPARATOR = "----------"
COMBINED_DATA_FILE = "remote_combined.csv"

class NotificationHandler(DefaultDelegate):     
    """
    This child class inherits the DefaultDelegate parent class that will be used as a notification handler for incoming BLE data.

    """
    def __init__(self):
        """
        Initialises NotificationHandler

        """
        DefaultDelegate.__init__(self)
        self.buffer = bytes()
        self.queue = Queue()
                                                  
    def handleNotification(self, cHandle, data):  
        """
        Callback that will be called whenever notification for the subscribed characteristic has arrived, indicating new incoming data.

        Args:
            cHandle (int): An integer representing the BLE attribute handle for which the data is coming from.
            data (bytes): New incoming data.
        """
        self.processData(data)

    def processData(self, data: bytes):
        """
        Processes any new incoming data into the buffer.

        If a complete message has been received, the data in the message will be extracted and place in the queue.

        Args:
            data (bytes): New incoming data.
        """
        self.buffer += data

        # If this is true, it means that we are seeing the start of a FULL message.
        if (self.buffer.startswith(START_BYTE)) and (len(self.buffer) >= MSG_LEN):
            while (self.buffer.startswith(START_BYTE)) and (len(self.buffer) >= MSG_LEN):
                msg = self.buffer[0:MSG_LEN] # Retrieve the rest of the full message.
                self.buffer = self.buffer[MSG_LEN:] # Keep the rest of the buffer.
                self.processMsg(msg) # Process message.

        # If we reached here, it means that either there are leading bytes at the front that does not belong to any message 
        # (there was no START_BYTE or we have never received the START_BYTE, only received some parts of that message)
        # OR we have seen the START_BYTE but the full message hasn't arrived completely yet. So we wait for more data to come in.
        else:
            sPos = self.buffer.find(START_BYTE) # Find the index position of the FIRST START_BYTE
            if sPos > 0:
                self.buffer = self.buffer[sPos:] # Keep the buffer, starting from the first START_BYTE until the end. Essentially removing leading bytes if there are any.

    def processMsg(self, msg: bytes):
        """
        Processes the message to extract it's contents (data).

        Args:
            msg (bytes): Message to extract data from.
        """
        crc = crc8(msg[:MSG_LEN-1])
        if crc != msg[MSG_LEN-1]:
            return # Error in bytes, disregard this data set

        values = []
        # Disregard the START_BYTE
        for i in range(1, MSG_LEN-1, FIELD_LEN):
            value = msg[i:i+FIELD_LEN]
            value = struct.unpack('f', value)[0]
            values.append(value)
        self.queue.put(values)

    def getValue(self) -> list:
        """
        Retrieves a single value from the queue buffer.

        Returns:
            list: List containing IMU values: [ax, ay, az, gx, gy, gz, mx, my, mz]
        """
        try:
            return self.queue.get(block=False)
        except Empty:
            return None

    

class ReceiveThread(threading.Thread):
    """
    Represents the thread that will connect to Bluefruit Feather and listen for incoming data via BLE.

    The thread will begin by attempting to connect via BLE and look for the corresponding services and characteristics.
    If valid services and characteristics are found, a subscription to notifications will be made.
    The handling should be handled by a NotificationHandler object.

    """
    def __init__(self, notifHandler: NotificationHandler, connectedEvent: threading.Event):
        """
        Initialises ReceiveThread

        Args:
            notifHandler (NotificationHandler): This should contain the callback to handle any incoming data.
        """
        threading.Thread.__init__(self)
        self.notifHandler = notifHandler
        self.shutdown = threading.Event()
        self.connectedEvent = connectedEvent
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"

    def run(self):
        scanEntry = self.scanDevice(FEATHER_NAME)
        
        if scanEntry is None:
            self.print("Cannot find device, is it turned on and receiving connections?")
            exit(DEVICE_NOT_FOUND)
        
        device = Peripheral(scanEntry.addr, scanEntry.addrType)
        notifHandler = NotificationHandler()
        self.subNotification(device, DATA_SVC_UUID, DATA_CHAR_UUID, self.notifHandler)
        self.connectedEvent.set()

        while not self.shutdown.isSet():
            try:
                device.waitForNotifications(1)
            except KeyboardInterrupt:
                break

        # Cleanup
        device.disconnect()

    def scanDevice(self, targetName: str) -> ScanEntry:
        self.print("Scanning for", targetName)
        scanner = Scanner()
        scanner.scan(SCAN_TIMEOUT)
        for d in scanner.getDevices():
            if d.getValueText(ADT_COMPLETE_NAME) == targetName:
                self.print("Found", targetName)
                self.print("Address:", d.addr)
                return d
        self.print(SEPARATOR)
        return None

    def subNotification(self, device: Peripheral, svcUuid: str, charUuid: str, notifHandler: NotificationHandler):
        # First check that the data stream service exists
        self.print("Finding IMU data stream service with UUID:", DATA_SVC_UUID)
        try:
            svc = device.getServiceByUUID(svcUuid)
        except BTLEException:
            self.print("Data stream service can't be found. Exiting.")
            exit(DATA_SERVICE_NOT_FOUND)
        self.print("Found IMU data stream service!")
        self.print(SEPARATOR)
        
        # Check that the charactertistic we are interested in exists.
        self.print("Finding IMU data characteristic with UUID:", DATA_CHAR_UUID)
        chars = device.getCharacteristics(uuid=charUuid)
        if len(chars) == 0:
            self.print("Data stream characteristic can't be found. Exiting.")
            exit(DATA_CHARACTERISTIC_NOT_FOUND)
        self.print("Found IMU data stream characteristic!")
        self.print(SEPARATOR)

        # Now that we are sure both the service and characteristics exists, we subscribe to receive notifications whenever there is new data.
        self.print("Finding CCCD handle to subscribe to notifications:", DATA_CHAR_UUID)
        ch = chars[0] # Assuming the characteristic is the only element.
        charFound = False
        cccd = None
        for d in device.getDescriptors():
            if d.uuid == ch.uuid and not charFound:
                charFound = True

            if charFound:
                # Find the first Client Charactertistic Configuration Descriptor (CCCD) that corresponds to this charateristic
                if UUID_CCCD in str(d.uuid):
                    cccd = d
                    break

        if cccd is None:
            self.print("Can't find Client Charactertistic Configuration Descriptor for data stream charateristic. Exiting.")
            exit(CCCD_NOT_FOUND)
        
        # Turn on the notification
        cccd.write(NOTIF_ON, withResponse=True)

        # Set notification handler 
        device.withDelegate(notifHandler)
        self.print("Successfully subscribed!")
        self.print(SEPARATOR)

    def print(self, *objs, **kwargs):
        builtins.print(self.printPrefix, *objs, **kwargs)

class PublishThread(threading.Thread):
    def __init__(self, notifHandler: NotificationHandler, publishAddr: str, pubTopic: str, useMock: bool):
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        self.bleConnected = threading.Event()
        self.notifHandler = notifHandler
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"
        self.pubAddr = publishAddr
        self.pubTopic = pubTopic
        self.publisher = None
        self.useMock = useMock
        self.mockReader = None

    def run(self):
        self.setupPub()

        if self.useMock:
            # Concatenate all specified mock data for use later.
            self.mockReader = self.concatData()

        # Don't do anything until the BLE has connected successfully.
        connected = False
        self.print("Waiting for BLE")
        while not self.shutdown.isSet():
            connected = self.bleConnected.wait(0.5)
            if connected:
                self.print("BLE connected!")
                break

        while not self.shutdown.isSet():
            value = self.notifHandler.getValue()
            
            if value is not None:
                if self.useMock:
                    value = next(self.mockReader)
                    s = "%s %s %s %s %s %s %s %s %s %s" % (self.pubTopic, value[1], value[2], value[3], value[4], value[5], value[6], value[7], value[8], value[9])
                else:
                    s = "%s %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f" % (self.pubTopic, value[0], value[1], value[2], value[3], value[4], value[5], value[6], value[7], value[8])
                self.publisher.send_string(s)
                self.print(s)

        # Clean up
        if self.useMock:
            os.remove(COMBINED_DATA_FILE)
    
    def concatData(self) -> csv.reader:
        #set working directory
        os.chdir(config.REMOTE_MOCK_FOLDER)

        #find all csv files in the folder
        all_filenames = []
        dir_files = os.listdir()
        for f in config.REMOTE_MOCK_PATHS:
            if f in dir_files:
                all_filenames.append(f)
        self.print("Using Mock Data:", all_filenames)

        #combine all files in the list
        ## Note: Xavier the dataset files all have header so will need to account for that. I removed the header in the
        ## test data in mock_data to test first
        combined_csv = pd.concat([pd.read_csv(f, header=None) for f in all_filenames ])
        #export to csv
        if os.path.isfile(COMBINED_DATA_FILE):
            os.remove(COMBINED_DATA_FILE)
        combined_csv.to_csv(COMBINED_DATA_FILE, index=False, encoding='utf-8-sig', header=None)
        stream = open(COMBINED_DATA_FILE, newline='')
        csvFile = csv.reader(stream, delimiter=',')

        return csvFile

    def setupPub(self):
        self.print("Setting up publisher to:", self.pubAddr)
        context = zmq.Context()
        self.publisher = context.socket(zmq.PUB)
        self.publisher.bind(self.pubAddr)

    def print(self, *objs, **kwargs):
        builtins.print(self.printPrefix, *objs, **kwargs)

if __name__ == "__main__":
    notifHandler = NotificationHandler()

    try:
        pubData = PublishThread(notifHandler, config.DATA_SOCK, config.REMOTE_IMU_TOPIC, config.REMOTE_USE_MOCK)
        pubData.start()
        recvData = ReceiveThread(notifHandler, pubData.bleConnected)
        recvData.start()

        while threading.activeCount() > 0:
            time.sleep(0.01)

    except KeyboardInterrupt:
        pubData.shutdown.set()
        recvData.shutdown.set()
        pubData.join()
        recvData.join()
