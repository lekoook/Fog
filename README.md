# Fog

There are two components:

## Prerequisites
To use the python scripts, you will need the following python module(s) installed:

### Python 3.6+
See Python's downloads [page](https://www.python.org/downloads/) on downloads and installation.

### PyZMQ
PyZMQ is a Python implementation of the ZeroMQ asynchronous messaging library. ZeroMQ allows messages to be passed between two python process (different scripts).

To install on `pip3`:

`pip3 install pyzmq`

### SMBus
SMBus is a bus protocol that is a subset of I2C protocol. The sensor interface library uses SMBus to communicate with the sensors.

To install on `pip3`:

`pip3 install smbus`

### joblib
### scipy
### pandas
### xlrd
### sklearn

## Components
### DataProvider
This components aims to read values from the 9-DOF IMU (Inertial Measurement Unit) and publishes them on to a ZMQ socket topic.

Note: Currently, it only publishes raw data and no filters or preprocessing are implemented.

### Predictor
This component aims to receive values from the 9-DOF IMU and applies the prediction model.

## How to run
### With actual hardware (RPi + IMU)
First, navigate to DataProvider:

`cd path/to/Fog/DataProvider/`

Then, run DataProvider:

`sudo python3 DataPublisher.py`

You should see the IMU data being read and published. \
Note: `sudo` may or may not be needed in order to run SMBus on your system.

Next on a separate terminal, navigate to Predictor:

`cd path/to/Fog/Predictor/`

Then, run Predictor:

`python3 Feature.py`

If you have ran `DataProvider` correctly, you should now see that `Predictor` is printing the same values being published by `DataProvider`.

### Without actual hardware (your PC)
Since your PC may not have direct communication with the IMU, you won't be able to read IMU values. Here, the difference from the actual hardware section is just running a python script that **mocks** reading and then publishing of IMU values.

First, navigate to repository root:

`cd path/to/Fog/`

Then, run the mock publisher:

`python3 publisher.py`

You should see the fake (randomised) IMU data being read and published. \
Note: Unlike the actual hardware, you shouldn't need `sudo` here.

Next on a separate terminal, navigate to Predictor:

`cd path/to/Fog/Predictor/`

Then, run Predictor:

`python3 Feature.py`

If you have ran the mock publisher correctly, you should now see that `Predictor` is printing the same values being published by the mock publisher.