from BluetoothctlWrapper import Bluetoothctl
import time
import sys
sys.path.append("..")
import config

btctl = Bluetoothctl()

def isAudioConnected() -> bool:
    for dev in config.AUDIO_MACS:
        if btctl.isConnected(dev):
            return True
    return False

def connectAudio() -> bool:
    for dev in config.AUDIO_MACS:
        if btctl.connect(dev):
            print("Connected to %s (%s)" % (dev, btctl.getDeviceName(dev)))
            return True
    return False
if __name__ == "__main__":
    while True:
        if not isAudioConnected():
            if connectAudio():
                pass
        time.sleep(0.1)