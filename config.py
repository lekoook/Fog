#!/usr/bin/python3

# DataProvider
DATA_SOCK           = "tcp://127.0.0.1:5556"
IMU_TOPIC           = "imu"
USE_MOCK_DATA       = True # Set to False to read and use actual IMU data.
MOCK_DATA_FOLDER    = "mock_data"
MOCK_DATA_PATHS     = [
                        "sample_1.csv"
                        ] # Relative to where DataPublisher.py is located. Give multiple file names in this list to concaternate them as one. 
LOG_FOLDER          = "logs/"
LOG_FILE_PREFIX     = LOG_FOLDER + "dp_log_"
# DataProvider filters
USE_MEDIAN_FILTER   = True
MF_WINDOW_SIZE      = 3