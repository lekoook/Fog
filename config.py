#!/usr/bin/python3

# DataProvider
DATA_SOCK           = "tcp://127.0.0.1:5556"
LOCAL_IMU_TOPIC     = "local_imu"
REMOTE_IMU_TOPIC    = "remote_imu"
WAIT_FOR_USER       = True
USE_MOCK_DATA       = True # Set to False to read and use actual IMU data.
MOCK_DATA_FOLDER    = "mock_data"
MOCK_DATA_PATHS     = [
                        "FoG-T-141_2_t1_s1.csv",
                        "FoG-T-141_2_t1_s2.csv",
                        "FoG-T-141_2_t1_s3.csv"
                        ] # Relative to where DataPublisher.py is located. Give multiple file names in this list to concaternate them as one. 
LOG_FOLDER          = "logs/"
LOG_FILE_PREFIX     = LOG_FOLDER + "dp_log_"
# DataProvider filters
USE_MEDIAN_FILTER   = True
MF_WINDOW_SIZE      = 3
REMOTE_USE_MOCK     = True
REMOTE_MOCK_FOLDER  = "mock_data"
REMOTE_MOCK_PATHS   = [
                        "FoG-S-003_2_t1_s2.csv",
                        "sample_1.csv"
                        ]
                        
# Remote IMU BLE configuration parameters
BLE_DEV_NAME        = "Adafruit Bluefruit LE"   # Name of device of interest
BLE_DATA_SVC_UUID   = "abc0"    # UUID for data stream service
BLE_DATA_CHAR_UUID  = "abc1"    # UUID for data stream characteristic
BLE_SCAN_TIMEOUT    = 3     # Scan duration (seconds)
BLE_RESCAN_INTS     = 1.0   # Seconds between scan attempts
BLE_CONN_ATTEMPTS   = 5     # Number of connection attempts before rescanning
BLE_RECONN_INTS     = 1.0   # Seconds between connection attempts

# Predictor
PREDICT_SOCK        = "tcp://127.0.0.1:5557"
PREDICT_READY_SOCK  = "tcp://127.0.0.1:5559"
PREDICT_TOPIC       = "ps"
PREDICT_MODE        = "MLP"
WIN_SIZE            = 100
SAMPLE_RATE         = 50
TEST_RATE           = 10
LDA_JOBLIB_PATH     = "./lib/lda_all.joblib"
RF_JOBLIB_PATH      = "./lib/rf_all.joblib"
SCL_D_JOBLIB_PATH   = "./lib/SCL_D.bin"
MLP_D_JOBLIB_PATH   = "./lib/MLP_D.joblib"
SCL_P_JOBLIB_PATH   = "./lib/SCL_P.bin"
MLP_P_JOBLIB_PATH   = "./lib/MLP_P.joblib"

# Feedback
BTN_SOCK            = "tcp://127.0.0.1:5558"
BTN_TOPIC           = "button"
SOUNDS_FOLDER       = "sounds/"
STOP_SOUND_PATH     = "stop.wav"
SPEAKER_MAC         = "D8:37:3B:1C:74:AD" # JBL Go 3 speaker
HEADPHONE_MAC       = "20:74:CF:5E:9F:76" # AfterShokz Titanium headphone
AUDIO_MACS          = [HEADPHONE_MAC, SPEAKER_MAC] # The ealrlier items have higher priority

