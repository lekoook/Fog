#
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

import sys
import zmq
import threading
import time

class readThread(threading.Thread):
    def __init__(self):  
        threading.Thread.__init__(self)

        #  Socket to talk to server
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:5556")

        # Set socket options to subscribe
        zip_filter = "1"
        self.socket.setsockopt_string(zmq.SUBSCRIBE, zip_filter)

    def run(self):
        while True:
            string = self.socket.recv_string()
            t, ax, ay, az, gx, gy ,gz, mx, my, mz = string.split()
            print("%s %s %s %s %s %s %s %s %s" % (ax, ay, az, gx, gy ,gz, mx, my, mz))

class countingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.counter = 0

    def run(self):
        while True:
            print("Counting %i" %(self.counter))
            self.counter += 1
            time.sleep(1)


rt = readThread()
rt2 = readThread()
ot = countingThread()
rt.start()
rt2.start()
ot.start()
rt.join()
rt2.join()
ot.join()

#  Socket to talk to server
# context = zmq.Context()
# socket = context.socket(zmq.SUB)
# socket.connect("tcp://localhost:5556")

# # Subscribe to zipcode, default is NYC, 10001
# zip_filter = sys.argv[1] if len(sys.argv) > 1 else "10001"

# # Python 2 - ascii bytes to unicode str
# if isinstance(zip_filter, bytes):
#     zip_filter = zip_filter.decode('ascii')
# zip_filter = "1"
# socket.setsockopt_string(zmq.SUBSCRIBE, zip_filter)

# Process 5 updates
# while True:
#     string = socket.recv_string()
#     t, ax, ay, az, gx, gy ,gz, mx, my, mz = string.split()
#     print("%s %s %s %s %s %s %s %s %s" % (ax, ay, az, gx, gy ,gz, mx, my, mz))