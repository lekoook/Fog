/*********************************************************************
 This is an example for our nRF51822 based Bluefruit LE modules

 Pick one up today in the adafruit shop!

 Adafruit invests time and resources providing this open source code,
 please support Adafruit and open-source hardware by purchasing
 products from Adafruit!

 MIT license, check LICENSE for more information
 All text above, and the splash screen below must be included in
 any redistribution
*********************************************************************/

/*
    Please note the long strings of data sent mean the *RTS* pin is
    required with UART to slow down data sent to the Bluefruit LE!  
*/

#include <Arduino.h>
#include <SPI.h>
#include "Adafruit_BLE.h"
#include "Adafruit_BluefruitLE_SPI.h"
#include "Adafruit_BluefruitLE_UART.h"
#include "Adafruit_BLEGatt.h"
#include "BluefruitConfig.h"
#include "checksum.h"
#include <Wire.h>
#include "LSM6.h"
#include "LIS3MDL.h"

// BLE GATT definitions
#define IMU_SERVICE 0xABC0
#define DATA_CHAR 0xABC1
#define DATA_CHAR_DESC "Data stream"
#define IMU_SRV_LOW (IMU_SERVICE & 0x00FF)
#define IMU_SRV_HIGH ((IMU_SERVICE & 0xFF00) >> 8)
#define DATA_MIN_SIZE 3
#define DATA_MAX_SIZE 20

// Message definitions
#define MSG_LEN 38 // Start byte + payload bytes + checksum byte
#define START_BYTE 0xFF
#define SAMPLE_RATE 50

// IMU definitions
#define G_ACCEL 9.80665
#define ACC_SENS 2.0 // +-2G
#define GYRO_SENS 245.0 // +-245DPS
#define MAG_SENS 4.0 // +-4Gauss

LSM6 lsm6;
const double ACCEL_CONST = ACC_SENS * G_ACCEL / (2 << 14);
const double GYRO_CONST = GYRO_SENS / (2 << 14);
LIS3MDL lis3mdl;
const double MAG_CONST = MAG_SENS / (2 << 14);
const uint16_t sampIntv = 1000 / SAMPLE_RATE; // In ms

// Function prototypes
uint8_t crc8(uint8_t* data, uint8_t len);
void packData(
    float ax, float ay, float az, 
    float gx, float gy, float gz, 
    float mx, float my, float mz, 
    uint8_t buffer[MSG_LEN]);
void sendMsg(int32_t charId, uint8_t msg[], uint16_t size);
void getImuValues(LSM6::vector<float> &accel, LSM6::vector<float> &gyro, LIS3MDL::vector<float> &mag);

// Create the bluefruit object, either software serial...uncomment these lines
/*
SoftwareSerial bluefruitSS = SoftwareSerial(BLUEFRUIT_SWUART_TXD_PIN, BLUEFRUIT_SWUART_RXD_PIN);

Adafruit_BluefruitLE_UART ble(bluefruitSS, BLUEFRUIT_UART_MODE_PIN,
                      BLUEFRUIT_UART_CTS_PIN, BLUEFRUIT_UART_RTS_PIN);
*/

/* ...or hardware serial, which does not need the RTS/CTS pins. Uncomment this line */
// Adafruit_BluefruitLE_UART ble(BLUEFRUIT_HWSERIAL_NAME, BLUEFRUIT_UART_MODE_PIN);

/* ...hardware SPI, using SCK/MOSI/MISO hardware SPI pins and then user selected CS/IRQ/RST */
Adafruit_BluefruitLE_SPI ble(BLUEFRUIT_SPI_CS, BLUEFRUIT_SPI_IRQ, BLUEFRUIT_SPI_RST);

/* ...software SPI, using SCK/MOSI/MISO user-defined SPI pins and then user selected CS/IRQ/RST */
//Adafruit_BluefruitLE_SPI ble(BLUEFRUIT_SPI_SCK, BLUEFRUIT_SPI_MISO,
//                             BLUEFRUIT_SPI_MOSI, BLUEFRUIT_SPI_CS,
//                             BLUEFRUIT_SPI_IRQ, BLUEFRUIT_SPI_RST);

Adafruit_BLEGatt gatt(ble);
uint8_t msgBuf[MSG_LEN] = { 0 };

/* The service information */
int32_t imuServiceId;
int32_t dataCharId;

void setup(void)
{
    Serial.begin(115200);

    /* Initialise the module */
    Serial.print(F("Initialising the Bluefruit LE module: "));

    if ( !ble.begin(VERBOSE_MODE) )
    {
        Serial.println(F("Couldn't find Bluefruit, make sure it's in CoMmanD mode & check wiring?"));
    }
    Serial.println( F("OK!") );

    /* Perform a factory reset to make sure everything is in a known state */
    Serial.println(F("Performing a factory reset: "));
    if (! ble.factoryReset() )
    {
        Serial.println(F("Couldn't factory reset"));
    }

    /* Disable command echo from Bluefruit */
    ble.echo(false);

    /* Print Bluefruit information */
    // Serial.println("Requesting Bluefruit info:");
    // ble.info();

    /* Add the IMU Service definition */
    /* Service ID should be 1 */
    Serial.println(F("Adding IMU Service (UUID = 0xABC0): "));
    imuServiceId = gatt.addService(IMU_SERVICE);
    if (imuServiceId == 0) 
    {
        Serial.println(F("Could not add IMU Service"));
    }
    
    // Add the characteristics for all IMU data
    Serial.println(F("Adding the IMU data stream characteristic"));
    dataCharId = gatt.addCharacteristic(DATA_CHAR, GATT_CHARS_PROPERTIES_NOTIFY, DATA_MIN_SIZE, 
        DATA_MAX_SIZE, BLE_DATATYPE_BYTEARRAY, DATA_CHAR_DESC);
    if (dataCharId == 0) 
    {
        Serial.println(F("Could not add IMU data stream characteristic"));
    }

    /* Add the IMU Service to the advertising data */
    Serial.print(F("Adding IMU Service UUID to the advertising payload: "));
    uint8_t advdata[] { 0x02, 0x01, 0x06, 0x03, 0x02, IMU_SRV_HIGH, IMU_SRV_HIGH };
    ble.setAdvData( advdata, sizeof(advdata) );

    /* Reset the device for the new service setting changes to take effect */
    Serial.print(F("Performing a SW reset (service changes require a reset): "));
    ble.reset();

    Serial.println();

    Wire.begin();
    // Enable LSM6DS33
    Serial.println("Initialising LSM6");
    if (!lsm6.init())
    {
        Serial.println("Failed to detect and initialize LSM6");
    }
    lsm6.enableDefault();

    // Enable LIS3MDL
    Serial.println("Initialising LIS3MDL");
    if (!lis3mdl.init())
    {
        Serial.println("Failed to detect and initialize LIS3MDL");
    }
    lis3mdl.enableDefault();
}

void loop(void)
{
    ble.update();

    // Get LSM6 data.
    LSM6::vector<float> accel;
    LSM6::vector<float> gyro;
    LIS3MDL::vector<float> mag;
    getImuValues(accel, gyro, mag);

    // Publish on characteristics.
    packData(accel.x, accel.y, accel.z, gyro.x, gyro.y, gyro.z, mag.x, mag.y, mag.z, msgBuf);
    sendMsg(dataCharId, msgBuf, MSG_LEN);

    /* Delay before next measurement update */
    delay(sampIntv);
}

/**
 * @brief Calculates a 8-bits width CRC byte given some bytes data.
 * 
 * @details Code taken from: https://stackoverflow.com/questions/51731313/cross-platform-crc8-function-c-and-python-parity-check 
 * Credited to: "Triz"
 * 
 * @param data Bytes array to calculate CRC from.
 * @param len Number of bytes in array.
 * @return uint8_t Calculated CRC byte.
 */
uint8_t crc8(uint8_t* data, uint8_t len)
{
    uint8_t crc=0;
    for (uint8_t i=0; i<len;i++)
    {
        uint8_t inbyte = data[i];
        for (uint8_t j=0;j<8;j++)
        {
            uint8_t mix = (crc ^ inbyte) & 0x01;
            crc >>= 1;
            if (mix)
            {
            crc ^= 0x8C;
            } 
            inbyte >>= 1;
        }
    }
   return crc;
}

/**
 * @brief Packs all data fields into the given buffer.
 * 
 * @param ax X-axis acceleration.
 * @param ay Y-axis acceleration.
 * @param az Z-axis acceleration.
 * @param gx X-axis angular velocity.
 * @param gy Y-axis angular velocity.
 * @param gz Z-axis angular velocity.
 * @param mx X-axis gauss.
 * @param my Y-axis gauss.
 * @param mz Z-axis gauss.
 * @param buffer Buffer to store packed data.
 */
void packData(
    float ax, float ay, float az, 
    float gx, float gy, float gz, 
    float mx, float my, float mz, 
    uint8_t buffer[MSG_LEN])
{
    buffer[0] = START_BYTE;

    // Data fields
    memcpy(&buffer[1], &ax, 4);
    memcpy(&buffer[5], &ay, 4);
    memcpy(&buffer[9], &az, 4);
    memcpy(&buffer[13], &gx, 4);
    memcpy(&buffer[17], &gy, 4);
    memcpy(&buffer[21], &gz, 4);
    memcpy(&buffer[25], &mx, 4);
    memcpy(&buffer[29], &my, 4);
    memcpy(&buffer[33], &mz, 4);

    // Generate CRC, we do not include the CRC byte place.
    buffer[37] = crc8(buffer, MSG_LEN-1);
}

/**
 * @brief Sends the given message out via a characteristic. Message will be fragmented if the total size is larger than the max allowable characteristic field size.
 * 
 * @param charId Charactertistic ID to send via.
 * @param msg Message to send.
 * @param size Length of message in bytes.
 */
void sendMsg(int32_t charId, uint8_t msg[], uint16_t size)
{
    int16_t idx = 0;
    while (idx + DATA_MAX_SIZE < size)
    {
        gatt.setChar(charId, &msg[idx], DATA_MAX_SIZE);
        idx += DATA_MAX_SIZE;
    }
    gatt.setChar(charId, &msg[idx], size - idx);
}

void getImuValues(LSM6::vector<float> &accel, LSM6::vector<float> &gyro, LIS3MDL::vector<float> &mag)
{
    lsm6.read();
    lis3mdl.read();
    LSM6::vector<int16_t> acc = lsm6.a;
    LSM6::vector<int16_t> gyr = lsm6.g;
    LIS3MDL::vector<int16_t> magn = lis3mdl.m;
    accel.x = acc.x * ACCEL_CONST;
    accel.y = acc.y * ACCEL_CONST;
    accel.z = acc.z * ACCEL_CONST;
    gyro.x = gyr.x * GYRO_CONST;
    gyro.y = gyr.y * GYRO_CONST;
    gyro.z = gyr.z * GYRO_CONST;
    mag.x = magn.x * MAG_CONST;
    mag.y = magn.y * MAG_CONST;
    mag.z = magn.z * MAG_CONST;
}