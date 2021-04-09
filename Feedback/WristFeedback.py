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
DEVICE_NAME = "Adafruit Bluefruit LE"
# BLE services/characteristics to watch
VIB_SVC_UUID = "abd0"
VIB_CHAR_UUID = "abd1"
BTN_CHAR_UUID = "abd2"

# BLE Configurations
SCAN_TIMEOUT = 3 # seconds
SCAN_INTERVAL = 3 # seconds

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
        print(data)
        print(int.from_bytes(data, "little", signed=True))
        # self.processData(data)

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

    

class WristDeviceThread(threading.Thread):
    """
    Represents the thread that will connect to wrist device, listen for button presses and send vbration command via BLE.

    The thread will begin by attempting to connect via BLE and look for the corresponding services and characteristics.
    If valid services and characteristics are found, a subscription to notifications for button presses will be made.
    The handling should be handled by a NotificationHandler object.
    The thread also exposes a method to send activating or deactivating command for the vibration.

    """
    def __init__(self, notifHandler: NotificationHandler, connectedEvent: threading.Event):
        """
        Initialises ReceiveThread

        Args:
            notifHandler (NotificationHandler): This should contain the callback to handle any incoming button presses.
        """
        threading.Thread.__init__(self)
        self.notifHandler = notifHandler
        self.shutdown = threading.Event()
        self.connectedEvent = connectedEvent
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"
        self.vibChar = None
        self.device = None

    def run(self):
        deviceFound = False
        while not self.shutdown.isSet():
            try:
                if deviceFound:
                    self.device.waitForNotifications(0.1)
                else:
                    if self.setupDevice(DEVICE_NAME):
                        self.print("Device setup success.")
                        deviceFound = True
                    else:
                       self.print("Cannot set up device. Trying again in %d seconds." % SCAN_INTERVAL)
                       time.sleep(SCAN_INTERVAL)
                       continue
            except BTLEDisconnectError:
                self.print("Device disconnected.")
                deviceFound = False
            except KeyboardInterrupt:
                break

        # Cleanup
        if self.device is not None:
            self.device.disconnect()

    def setupDevice(self, deviceName: str) -> bool:
        scanEntry = self.scanDevice(deviceName)
        if scanEntry is None:
            return False
        else:
            self.device = Peripheral(scanEntry.addr, scanEntry.addrType)
            # Check that vibration service exists.
            if not self.checkVibSvc(self.device, VIB_SVC_UUID):
                return False
            # Check that vibration charactertistics exists.
            if not self.findVibChar(self.device, VIB_CHAR_UUID):
                return False
            # Subscrbibe to button press notifications if the characteristics exists.
            notifHandler = NotificationHandler()
            if not self.subButtonPress(self.device, BTN_CHAR_UUID, self.notifHandler):
                return False
            self.connectedEvent.set()
            return True

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
    
    def checkVibSvc(self, device: Peripheral, svcUuid: str) -> bool:
        # First check that the vibration service exists
        self.print("Finding wrist vibration service with UUID:", VIB_SVC_UUID)
        try:
            svc = device.getServiceByUUID(svcUuid)
        except BTLEException:
            self.print("Wrist vibration service can't be found.")
            return False
        self.print("Found wrist vibration service!")
        self.print(SEPARATOR)
        return True

    def findVibChar(self, device: Peripheral, vibCharUuid) -> bool:
        # Check that the charactertistic we are interested in exists.
        self.print("Finding vibration characteristic with UUID:", vibCharUuid)
        chars = device.getCharacteristics(uuid=vibCharUuid)
        if len(chars) == 0:
            self.print("Vibration characteristic can't be found. Exiting.")
            return False
        self.vibChar = chars[0]
        self.print("Found vibration characteristic!")
        self.print(SEPARATOR)
        return True

    def subButtonPress(self, device: Peripheral, charUuid: str, notifHandler: NotificationHandler) -> bool:
        # Check that the charactertistic we are interested in exists.
        self.print("Finding button press characteristic with UUID:", BTN_CHAR_UUID)
        chars = device.getCharacteristics(uuid=charUuid)
        if len(chars) == 0:
            self.print("Button press characteristic can't be found. Exiting.")
            return False
        self.print("Found button press characteristic!")
        self.print(SEPARATOR)

        # Now that we are sure both the service and characteristics exists, we subscribe to receive notifications whenever there is new data.
        self.print("Finding CCCD handle to subscribe to notifications:", BTN_CHAR_UUID)
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
            self.print("Can't find Client Charactertistic Configuration Descriptor for button press charateristic. Exiting.")
            return False
        
        # Turn on the notification
        cccd.write(NOTIF_ON, withResponse=True)

        # Set notification handler 
        device.withDelegate(notifHandler)
        self.print("Successfully subscribed!")
        self.print(SEPARATOR)
        return True

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
        recvData = WristDeviceThread(notifHandler, pubData.bleConnected)
        recvData.start()

        while threading.activeCount() > 0:
            time.sleep(0.01)

    except KeyboardInterrupt:
        pubData.shutdown.set()
        recvData.shutdown.set()
        pubData.join()
        recvData.join()
