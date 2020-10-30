#include "IMUValue.h"

IMUValue::IMUValue() : accelVect(VectorInt16()), gyroVect(VectorInt16())
{}

IMUValue::IMUValue(int16_t accelX, int16_t accelY, int16_t accelZ, int16_t gyroX, int16_t gyroY, int16_t gyroZ, int16_t magX, int16_t magY, int16_t magZ)
{
    accelVect.x = accelX;
    accelVect.y = accelY;
    accelVect.z = accelZ;
    gyroVect.x = gyroX;
    gyroVect.y = gyroY;
    gyroVect.z = gyroZ;
    magVect.x = magX;
    magVect.y = magY;
    magVect.z = magZ;
}

IMUValue::IMUValue(VectorInt16 accelVect, VectorInt16 gyroVect, VectorInt16 magVect)
    : accelVect(accelVect), gyroVect(gyroVect), magVect(magVect)
{}

VectorFloat IMUValue::getAccelMs2()
{
    float x = accelVect.x * ACCEL_CONST;
    float y = accelVect.y * ACCEL_CONST;
    float z = accelVect.z * ACCEL_CONST;
    return VectorFloat(x, y, z);
}

VectorFloat IMUValue::getGyroDegSec()
{
    float x = gyroVect.x * GYRO_CONST;
    float y = gyroVect.y * GYRO_CONST;
    float z = gyroVect.z * GYRO_CONST;
    return VectorFloat(x, y, z);
}

VectorFloat IMUValue::getGauss()
{
    float x = magVect.x * MAG_CONST;
    float y = magVect.y * MAG_CONST;
    float z = magVect.z * MAG_CONST;
    return VectorFloat(x, y, z);
}