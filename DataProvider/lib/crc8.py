#!/bin/usr/python3
def crc8(data: bytes) -> int:
    """
    Calculates a 8-bits width CRC byte from given bytes.

    Code is taken from: https://stackoverflow.com/questions/51731313/cross-platform-crc8-function-c-and-python-parity-check
    Credited to: "Triz"

    Args:
        data (bytes): Bytes used to calculate the CRC byte.

    Returns:
        int: Integer representing the byte value.
    """
    crc = 0
    for i in range(len(data)):
        byte = data[i]
        for b in range(8):
            fb_bit = (crc ^ byte) & 0x01
            if fb_bit == 0x01:
                crc = crc ^ 0x18
            crc = (crc >> 1) & 0x7f
            if fb_bit == 0x01:
                crc = crc | 0x80
            byte = byte >> 1
    return crc
