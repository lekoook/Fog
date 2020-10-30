#ifndef IMUVALUE_H_
#define IMUVALUE_H_

#include <Arduino.h>
#include "helper_3dmath.h"

// IMU definitions
#define G_ACCEL 9.80665f
#define ACC_SENS 2.0f // +-2G
#define GYRO_SENS 245.0f // +-245DPS
#define MAG_SENS 4.0f // +-4Gauss
#define ACCEL_CONST (ACC_SENS * G_ACCEL / 32768.0) // max of 16 bits signed int is 32767. +1 to account for negative range.
#define GYRO_CONST (GYRO_SENS / 32768.0)
#define MAG_CONST (MAG_SENS / 32768.0)

class IMUValue
{
// private:
    // /**
    //  * constant = 9.80665 (gravitational acceleration) 
    //  *      * 2.0 (accelerometer sensitivity = +-2g) 
    //  *      / 32768.0 (max of int16_t, +1 to account for negative range)
    //  */
    // const double ACCEL_CONST = ACC_SENS * G_ACCEL / (2 << 14);
    // /**
    //  * constant = 245.0 (gyroscope sensitivity = +-245 degree per second) 
    //  *      / 32768.0 (max of int16_t, +1 to account for negative range)
    //  */
    // const double GYRO_CONST = GYRO_SENS / (2 << 14);
    // /**
    //  * constant =4.0 (magnetometre sensitivity = +-4.0 gauss) 
    //  *      / 32768.0 (max of int16_t, +1 to account for negative range)
    //  */
    // const double MAG_CONST = MAG_SENS / (2 << 14);

public:
    VectorInt16 accelVect;
    VectorInt16 gyroVect;
    VectorInt16 magVect;

    /**
     * @brief Construct a new IMUValue object with all fields and nested fields zero initialised.
     * 
     */
    IMUValue();

    /**
     * @brief Construct a new IMUValue object initialised with the specified parameter values.
     * 
     * @param accelX Acceleration in X axis.
     * @param accelY Acceleration in Y axis.
     * @param accelZ Acceleration in Z axis.
     * @param gyroX Angular velocity about X axis.
     * @param gyroY Angular velocity about Y axis.
     * @param gyroZ Angular velocity about Z axis.
     * @param magX Gauss along X axis.
     * @param magY Gauss along Y axis.
     * @param magZ Gauss along Z axis.
     */
    IMUValue(int16_t accelX, int16_t accelY, int16_t accelZ, int16_t gyroX, int16_t gyroY, int16_t gyroZ, int16_t magX, int16_t magY, int16_t magZ);

    /**
     * @brief Construct a new IMUValue object initialised with the specified parameter values.
     * 
     * @param accelVect Acceleration in XYZ axes.
     * @param gyroVect Angular velocity in XYZ axes.
     * @param magVect Gauss along XYZ axes.
     */
    IMUValue(VectorInt16 accelVect, VectorInt16 gyroVect, VectorInt16 magVect);
    
    /**
     * @brief Returns the calculated acceleration values in units of metre per second squared.
     * 
     * @return VectorFloat Contains the values in XYZ axes.
     */
    VectorFloat getAccelMs2();

    /**
     * @brief Returns the calculated angular velocity values in units of degrees per second.
     * 
     * @return VectorFloat Contains the values about XYZ axes. 
     */
    VectorFloat getGyroDegSec();

    /**
     * @brief Returns the calculated magnetic field values in units of gauss.
     * 
     * @return VectorFloat Contains the values along XYZ axes. 
     */
    VectorFloat getGauss();
};

#endif // IMUVALUE_H_