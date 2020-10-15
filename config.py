#!/usr/bin/python3

# DataProvider
DATA_SOCK           = "tcp://127.0.0.1:5556"
IMU_TOPIC           = "imu"
USE_MOCK_DATA       = True # Set to False to read and use actual IMU data.
MOCK_DATA_FOLDER    = "mock_data"
MOCK_DATA_PATHS     = [
                        "FoG-S-003_2_t1_s2.csv"
                        ] # Relative to where DataPublisher.py is located. Give multiple file names in this list to concaternate them as one. 
LOG_FOLDER          = "logs/"
LOG_FILE_PREFIX     = LOG_FOLDER + "dp_log_"
# DataProvider filters
USE_MEDIAN_FILTER   = True
MF_WINDOW_SIZE      = 3

# Predictor
PREDICT_SOCK        = "tcp://127.0.0.1:5557"
PREDICT_TOPIC       = "ps"
WIN_SIZE            = 100
SAMPLE_RATE         = 50
TEST_RATE           = 10
LDA_JOBLIB_PATH     = "./lib/lda_all.joblib"
RF_JOBLIB_PATH      = "./lib/rf_all.joblib"

# Feedback
SOUNDS_FOLDER       = "sounds/"
STOP_SOUND_PATH     = "stop.wav"