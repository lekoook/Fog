#!/bin/usr/python3
from bluepy.btle import *
from queue import Queue, Empty
import threading
import builtins
import traceback
import sys
sys.path.append("..")
from DataProvider.lib.crc8 import crc8

# User Configurations
FEATHER_NAME = "Adafruit Bluefruit LE"
# BLE services/characteristics to watch
DATA_SVC_UUID = "abc0"
DATA_CHAR_UUID = "abc1"

# BLE Configurations
SCAN_TIMEOUT = 3

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
    def __init__(self, notifHandler: NotificationHandler):
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        self.bleConnected = threading.Event()
        self.notifHandler = notifHandler
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"

    def run(self):
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
                self.print(value)

    def print(self, *objs, **kwargs):
        builtins.print(self.printPrefix, *objs, **kwargs)

if __name__ == "__main__":
    notifHandler = NotificationHandler()

    try:
        pubData = PublishThread(notifHandler)
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
