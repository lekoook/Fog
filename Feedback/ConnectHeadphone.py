from BluetoothctlWrapper import Bluetoothctl
import time

if __name__ == "__main__":
    bl = Bluetoothctl()
    # lines = bl.get_device_info("D8:37:3B:1C:74:AD")
    # for l in lines:
    #     print(l)

    print(bl.isConnected("D8:37:3B:1C:74:AD"))
    bl.connect("D8:37:3B:1C:74:AD")
    # while True:
    #     success = bl.connect("D8:37:3B:1C:74:AD")
    #     print(success)
    #     if success:
    #         break
    #     time.sleep(1)
    # bl.start_scan()
    # print("Scanning for 10 seconds...")
    # for i in range(0, 10):
    #     print(i)
    #     time.sleep(1)

    # print(bl.get_discoverable_devices())