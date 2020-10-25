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

// BLE GATT definitions
#define IMU_SERVICE 0xABC0
#define AX_CHAR 0xABC1
#define AY_CHAR 0xABC2
#define AZ_CHAR 0xABC3
#define GX_CHAR 0xABC4
#define GY_CHAR 0xABC5
#define GZ_CHAR 0xABC6
#define MX_CHAR 0xABC7
#define MY_CHAR 0xABC8
#define MZ_CHAR 0xABC9
#define IMU_SRV_LOW (IMU_SERVICE & 0x00FF)
#define IMU_SRV_HIGH ((IMU_SERVICE & 0xFF00) >> 8)


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

// A small helper
void error(const __FlashStringHelper*err) {
    Serial.println(err);
    while (1);
}

float value = 0;

/* The service information */
int32_t imuServiceId;
int32_t axCharId;
int32_t ayCharId;
int32_t azCharId;
int32_t gxCharId;
int32_t gyCharId;
int32_t gzCharId;
int32_t mxCharId;
int32_t myCharId;
int32_t mzCharId;
int32_t notifyCharId;

void setup(void)
{
    Serial.begin(115200);

    /* Initialise the module */
    Serial.print(F("Initialising the Bluefruit LE module: "));

    if ( !ble.begin(VERBOSE_MODE) )
    {
        error(F("Couldn't find Bluefruit, make sure it's in CoMmanD mode & check wiring?"));
    }
    Serial.println( F("OK!") );

    /* Perform a factory reset to make sure everything is in a known state */
    Serial.println(F("Performing a factory reset: "));
    if (! ble.factoryReset() )
    {
        error(F("Couldn't factory reset"));
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
        error(F("Could not add IMU Service"));
    }
    
    // Add the characteristics for all IMU data
    Serial.println(F("Adding the IMU data characteristic"));
    axCharId = gatt.addCharacteristic(AX_CHAR, GATT_CHARS_PROPERTIES_NOTIFY, 4, 4, BLE_DATATYPE_BYTEARRAY, "AX");
    if (axCharId == 0) 
    {
        error(F("Could not add AX characteristic"));
    }
    ayCharId = gatt.addCharacteristic(AY_CHAR, GATT_CHARS_PROPERTIES_NOTIFY, 4, 4, BLE_DATATYPE_BYTEARRAY, "AY");
    if (ayCharId == 0) 
    {
        error(F("Could not add AY characteristic"));
    }
    azCharId = gatt.addCharacteristic(AZ_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "AZ");
    if (azCharId == 0) 
    {
        error(F("Could not add AZ characteristic"));
    }
    gxCharId = gatt.addCharacteristic(GX_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "GX");
    if (gxCharId == 0) 
    {
        error(F("Could not add GX characteristic"));
    }
    gyCharId = gatt.addCharacteristic(GY_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "GY");
    if (gyCharId == 0) 
    {
        error(F("Could not add GY characteristic"));
    }
    gzCharId = gatt.addCharacteristic(GZ_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "GZ");
    if (gzCharId == 0) 
    {
        error(F("Could not add GZ characteristic"));
    }
    mxCharId = gatt.addCharacteristic(MX_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "MX");
    if (mxCharId == 0) 
    {
        error(F("Could not add MX characteristic"));
    }
    myCharId = gatt.addCharacteristic(MY_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "MY");
    if (myCharId == 0) 
    {
        error(F("Could not add MY characteristic"));
    }
    mzCharId = gatt.addCharacteristic(MZ_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "MZ");
    if (mzCharId == 0) 
    {
        error(F("Could not add MZ characteristic"));
    }

    // This characteristic serves as a notifier for clients know that all IMU data is ready.
    mzCharId = gatt.addCharacteristic(MZ_CHAR, GATT_CHARS_PROPERTIES_READ, 4, 4, BLE_DATATYPE_BYTEARRAY, "MZ");
    if (mzCharId == 0) 
    {
        error(F("Could not add MZ characteristic"));
    }

    /* Add the IMU Service to the advertising data */
    Serial.print(F("Adding IMU Service UUID to the advertising payload: "));
    uint8_t advdata[] { 0x02, 0x01, 0x06, 0x03, 0x02, IMU_SRV_HIGH, IMU_SRV_HIGH };
    ble.setAdvData( advdata, sizeof(advdata) );

    /* Reset the device for the new service setting changes to take effect */
    Serial.print(F("Performing a SW reset (service changes require a reset): "));
    ble.reset();

    Serial.println();
}

void loop(void)
{
    ble.update();
    uint8_t b[4];
    memcpy(&b, &value, 4);
    value++;

    uint8_t ax[4];
    float axf = 0;
    memcpy(&ax, &axf, 4);
    gatt.setChar(axCharId, ax, 4);
    
    uint8_t ay[4];
    float ayf = 1;
    memcpy(&ay, &ayf, 4);
    gatt.setChar(ayCharId, ay, 4);

    gatt.setChar(azCharId, b, 4);
    gatt.setChar(gxCharId, b, 4);
    gatt.setChar(gyCharId, b, 4);
    gatt.setChar(gzCharId, b, 4);
    gatt.setChar(mxCharId, b, 4);
    gatt.setChar(myCharId, b, 4);
    gatt.setChar(mzCharId, b, 4);

    /* Delay before next measurement update */
    delay(1000);
}
