#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

import time
import zmq
from random import randrange


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

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
    socket.send_string("1 %i %i %i %i %i %i %i %i %i" % (ax, ay, az, gx, gy ,gz, mx, my, mz))

    time.sleep(0.020) # 50hz
