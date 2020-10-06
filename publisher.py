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


context = zmq.Context()
pub = context.socket(zmq.PUB)
pub.bind(config.DATA_SOCK)

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

    print("sending %i %i %i %i %i %i %i %i %i" % (ax, ay, az, gx, gy ,gz, mx, my, mz))
    pub.send_string("%s %i %i %i %i %i %i %i %i %i" % (config.IMU_TOPIC, ax, ay, az, gx, gy ,gz, mx, my, mz))

    time.sleep(0.020) # 50hz
