#!/usr/bin/python3

class IMUValue():
    def __init__(self, ax: int, ay: int, az: int, gx: int, gy: int, gz: int, mx: int, my: int, mz: int):
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.mx = mx
        self.my = my
        self.mz = mz
