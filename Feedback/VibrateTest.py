import zmq
import sys
sys.path.append("..")
import config

if __name__ == '__main__':
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(config.PREDICT_SOCK)
    
    while True:
        try:
            userInput = input("'1' to activate. Anything else to deactivate: ")
            if userInput == "1":
                print("Activate")
                publisher.send_string("%s %f" % (config.PREDICT_TOPIC, 0.5))
            else:
                print("Deactivate")
                publisher.send_string("%s %f" % (config.PREDICT_TOPIC, 0.0))
        except KeyboardInterrupt:
            break

    print("exit")