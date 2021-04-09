#!/bin/usr/python3
import zmq
from bluepy.btle import *
from queue import Queue, Empty
import threading
import builtins
import traceback
import sys
sys.path.append("..")
import config
from DataProvider.lib.crc8 import crc8

# Constants
POLL_TIMEOUT = 100 # milliseconds

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

wristDevice = None

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
        presses = int.from_bytes(data, "little", signed=True)
        self.queue.put(presses);

    def getValue(self) -> int:
        """
        Retrieves a single value from the queue buffer.

        Returns:
            button: Value indicating how many times the button was pressed. Negative indicates the last press was a long held press.
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
        self.fogOn = threading.Event()
        self.fogOn.clear()
        self.fogOff = threading.Event()
        self.fogOff.clear()
        self.connectedEvent = connectedEvent
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"
        self.vibChar = None
        self.device = None

    def run(self):
        deviceFound = False
        while not self.shutdown.isSet():
            time.sleep(0.1) # 10 Hz loop
            try:
                if deviceFound:
                    self.device.waitForNotifications(0.1)
                    if self.fogOn.isSet():
                        self.fogOn.clear()
                        self.print("Activate vibration")
                        self.vibChar.write(bytes("1", encoding="utf-8"))
                    if self.fogOff.isSet():
                        self.fogOff.clear()
                        self.print("Deactivate vibration")
                        self.vibChar.write(bytes("2", encoding="utf-8"))
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
        ch = chars[0] # Assuming the characteristic is the only element.
        self.print("Finding CCCD handle to subscribe to notifications:", BTN_CHAR_UUID)
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

    def activateVib(self):
        self.fogOn.set()

    def deactivateVib(self):
        self.fogOff.set()

    def print(self, *objs, **kwargs):
        builtins.print(self.printPrefix, *objs, **kwargs)

class PublishThread(threading.Thread):
    def __init__(self, notifHandler: NotificationHandler, btnAddr: str, btnTopic: str):
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        self.bleConnected = threading.Event()
        self.notifHandler = notifHandler
        self.printPrefix = "[" + self.__class__.__name__ + "]:\t"
        self.btnAddr = btnAddr
        self.btnTopic = btnTopic
        self.publisher = None

    def run(self):
        # Set up the button press publisher.
        self.setupPub();
        
        # Don't do anything until the BLE has connected successfully.
        connected = False
        self.print("Waiting for BLE")
        while not self.shutdown.isSet():
            time.sleep(0.1) # 10 Hz loop
            connected = self.bleConnected.wait(0.5)
            if connected:
                self.print("BLE connected!")
                break

        while not self.shutdown.isSet():
            time.sleep(0.1) # 10 Hz loop
            value = self.notifHandler.getValue()
            if value is not None:
                self.print("Button pressed: %d" % value)
                self.publisher.send_string("%s %d" % (self.btnTopic, value))

    def setupPub(self):
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        publisher.bind(self.btnAddr)
        self.publisher = publisher

    def print(self, *objs, **kwargs):
        builtins.print(self.printPrefix, *objs, **kwargs)

class ReadStateThread(threading.Thread):
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
        global wristDevice
        fogOn = False
        prevFogOn = False
        while not self.shutdown.isSet():
            sockEvents = self.sub.poll(POLL_TIMEOUT, zmq.POLLIN)
            if (sockEvents & zmq.POLLIN) > 0:
                string = self.sub.recv_string()
                t, state = string.split()
                fogOn = float(state) > 0.0
                if wristDevice is not None:
                    if fogOn and not prevFogOn:
                        wristDevice.activateVib()
                    if not fogOn and prevFogOn:
                        wristDevice.deactivateVib()
                prevFogOn = fogOn

        # Clean up
        context = zmq.Context.instance()
        context.destroy()

if __name__ == "__main__":
    notifHandler = NotificationHandler()

    try:
        pubData = PublishThread(notifHandler, config.BTN_SOCK, config.BTN_TOPIC)
        pubData.start()
        wristDevice = WristDeviceThread(notifHandler, pubData.bleConnected)
        wristDevice.start()
        readFog = ReadStateThread(config.PREDICT_SOCK, config.PREDICT_TOPIC)
        readFog.start()

        while threading.activeCount() > 0:
            time.sleep(0.01)

    except KeyboardInterrupt:
        pubData.shutdown.set()
        wristDevice.shutdown.set()
        readFog.shutdown.set()
        pubData.join()
        wristDevice.join()
        readFog.join()
