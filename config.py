#!/usr/bin/python3

# DataProvider
DATA_SOCK       = "tcp://127.0.0.1:5556"
IMU_TOPIC       = "imu"
MF_WINDOW_SIZE  = 3
USE_MOCK_DATA   = True # Set to False to read and use actual IMU data.
MOCK_DATA_PATH  = "mock_data/sample.csv" # Relative to where DataPublisher.py is located.
LOG_FOLDER      = "logs/"
LOG_FILE_PREFIX = LOG_FOLDER + "dp_log_"