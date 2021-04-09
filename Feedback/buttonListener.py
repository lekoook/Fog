import zmq
import threading
import time
import sys
sys.path.append("..")
import config

# Constants
POLL_TIMEOUT = 100 # milliseconds

class ReadStateTh(threading.Thread):
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
        while not self.shutdown.isSet():
            sockEvents = self.sub.poll(POLL_TIMEOUT, zmq.POLLIN)

            if (sockEvents & zmq.POLLIN) > 0:
                string = self.sub.recv_string()
                t, buttonPresses = string.split()
                buttonPresses = int(buttonPresses)
                print(buttonPresses)

        # Clean up
        context = zmq.Context.instance()
        context.destroy()

if __name__ == "__main__":
    try:
        readState = ReadStateTh(config.BTN_SOCK, config.BTN_TOPIC)
        readState.start()

        # Let's keep the main thread running to catch ctrl-c terminations.
        while threading.activeCount() > 0:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        readState.shutdown.set()
        readState.join()