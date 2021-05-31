# Fog

This git repository contains all the code developed and used in the Gait Detection for Parkinson's Disease project.

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

### bluepy
bluepy is an open source Python library to connect to BLE Peripheral devices such as our Wrist Device. At the moment, this library is limited to connecting to BLE Peripheral devices only.

Link: https://github.com/IanHarvey/bluepy

### Other Python Dependencies for Machine Learning
1. `joblib`
2. `scipy`
3. `pandas`
4. `xlrd`
5. `sklearn`

    Note: Some dependencies may be missed out here. When running the Python scripts, be sure to look out for errors indicating the lack of dependencies and install accordingly.

## Components
### DataProvider
This components aims to read values from the 9-DOF IMU (Inertial Measurement Unit) and publishes them on to a ZMQ topic.

However, due to the nature of the circumstances during the project, only data collected from patients are used. `DataPublisher.py` contains code to read `csv` files containing these data and publish as if they were from the IMU.

This functionality is handled in the `DataPublisher.py` script.

### Predictor
This component aims to receive values from the 9-DOF IMU and applies the Machine Learning (ML) prediction model. The output of this model will then be published on a ZMQ topic. This functionality is handled in the `Predictor.py` script.

### Feedback
This component will subscribe to the output from `Predictor` component via the ZMQ topic. It uses this information to provide both the audio and vibratory feedback to the user.

In the case of the audio, the audio is played via the Raspberry Pi OS's audio output stream. The RPi is initially configured to connect to the wireless bone conduction headphone via Bluetooth. When audio is played on the OS's audio stream, the audio will be played on the headphone as well. This functionality is handled in the `Feedback.py` script.

In the case of the vibratory feedback, there are code written to connect to the `Wrist Device`'s BLE using the `bluepy` open sourced Python library. The Wrist Device has an onboard BLE module that allows BLE connection. This functionality is handled in the `WristFeedback.py` script.

### Wrist Device
The wrist device contains a [Adafruit Flora](link:https://www.adafruit.com/product/659) microcontroller along with a [Adafruit BLE module](link:https://learn.adafruit.com/adafruit-flora-bluefruit-le). This allows BLE capability on the Wrist Device. The firmware that runs on that microcontroller can be found in the `vib` folder. This folder contains a [PlatformIO](link:https://platformio.org/) project structure and can be built and uploaded with any software IDE with a PlatformIO extension or just PlatformIO running in a Terminal. See PlatformIO guides for more information.

### Other components
There are several other folders containing software as well. 

`8Feat_Predictor`, `9Feat_Predictor` and `OptFeat_Predictor` are other variants of the ML model that were experimented with.

`remote_imu` is another PlatformIO project for the [Adafruit Feather M0 Bluefruit LE](link:https://www.adafruit.com/product/2995) microcontroller. Experimental code were written to collect data from the same IMU used in the Central Device and then shared via BLE. 

`RemoteIMU.py` script found in `DataProvider` folder contains code to connect to `remote_imu`'s microcontroller. This two sets of code are supposed to work in tandem.

`config.py` is a single Python script that contains all the application parameters for the entire repository. It is supposed to be a centralized collection of these parameters to facilitate the ease in changing configuration.

## How to run
### With actual hardware (RPi + IMU)
1. First, navigate to `DataProvider` folder:

    `cd path/to/Fog/DataProvider/`

2. Then run:

    `sudo python3 DataPublisher.py`

    You should see the IMU data being read and published. \
    Note: `sudo` may or may not be needed in order to run SMBus on your system.

3. Next on a separate terminal, navigate to `Predictor` folder:

    `cd path/to/Fog/Predictor/`

4. Then run:

5. `python3 Feature.py`

6. Lastly on two other separate terminals, navigate to the `Feedback` folder.

7. On each of those two terminals, run:

    `python3 Feedback.py`

    and

    `python3 WristFeedback.py`

    Note: If you face issues with root privileges try running with a `sudo` in front of the commands.
