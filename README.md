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

## Components
### DataProvider
This components aims to read values from the 9-DOF IMU (Inertial Measurement Unit) and publishes them on to a ZMQ socket topic.

Note: Currently, it only publishes raw data and no filters or preprocessing are implemented.

### Predictor
This component aims to receive values from the 9-DOF IMU and applies the prediction model.