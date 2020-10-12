# Predictor

## lib/
This folder contains the modules to store the different IMU parameter values as one single class object (IMUValue.py). It also provides a data structure (DataBuffer.py) with specialised operations to store these IMU values.

## Feature.py
This script will attempt to receive values from IMU topic and then store them in a DataBuffer. 

## AsyncWearable.py
This script will run the feature extraction and FoG detection step in an asynchronous thread

## utils.py
This script holds the function definitiions for feature extraction

## lda_all.jobblib
This file holds the pre-trained linear discriminant analysis classifer object used for FoG detection

## rf_all.jobblib (Missing: Unable to upload) 
This file holds the pre-trained random forest classifer object used for FoG detection
