#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

import time
import zmq
import sys
sys.path.append("..")
import config
from random import randrange
from DataProvider.lib.MedianFilter import MedianFilter


context = zmq.Context()
pub = context.socket(zmq.PUB)
pub.bind(config.DATA_SOCK)

axmf = MedianFilter(5)
aymf = MedianFilter(5)
azmf = MedianFilter(5)
gxmf = MedianFilter(5)
gymf = MedianFilter(5)
gzmf = MedianFilter(5)
mxmf = MedianFilter(5)
mymf = MedianFilter(5)
mzmf = MedianFilter(5)

while True:
    ax = randrange(1, 100)
    ay = randrange(1, 100)
    az = randrange(1, 100)
    gx = randrange(1, 100)
    gy = randrange(1, 100)
    gz = randrange(1, 100)
    mx = randrange(1, 100)
    my = randrange(1, 100)
    mz = randrange(1, 100)

    ax = axmf.filt(ax)
    ay = aymf.filt(ay)
    az = azmf.filt(az)
    gx = gxmf.filt(gx)
    gy = gymf.filt(gy)
    gz = gzmf.filt(gz)
    mx = mxmf.filt(mx)
    my = mymf.filt(my)
    mz = mzmf.filt(mz)

    print("sending %i %i %i %i %i %i %i %i %i" % (ax, ay, az, gx, gy ,gz, mx, my, mz))
    pub.send_string("%s %i %i %i %i %i %i %i %i %i" % (config.IMU_TOPIC, ax, ay, az, gx, gy ,gz, mx, my, mz))

    time.sleep(0.020) # 50hz
