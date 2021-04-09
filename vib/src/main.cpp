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

#include <Arduino.h>
#include <SPI.h>
#include "Adafruit_BLE.h"
#include "Adafruit_BluefruitLE_SPI.h"
#include "Adafruit_BluefruitLE_UART.h"
#include "Adafruit_BLEGatt.h"

#include "BluefruitConfig.h"
#include "Vibrator.hpp"
#include "ClickButton.h"
#include "TimedBlink.h"

#if SOFTWARE_SERIAL_AVAILABLE
  #include <SoftwareSerial.h>
#endif

/*=========================================================================
    APPLICATION SETTINGS

    FACTORYRESET_ENABLE       Perform a factory reset when running this sketch
   
                              Enabling this will put your Bluefruit LE module
                              in a 'known good' state and clear any config
                              data set in previous sketches or projects, so
                              running this at least once is a good idea.
   
                              When deploying your project, however, you will
                              want to disable factory reset by setting this
                              value to 0.  If you are making changes to your
                              Bluefruit LE device via AT commands, and those
                              changes aren't persisting across resets, this
                              is the reason why.  Factory reset will erase
                              the non-volatile memory where config data is
                              stored, setting it back to factory default
                              values.
       
                              Some sketches that require you to bond to a
                              central device (HID mouse, keyboard, etc.)
                              won't work at all with this feature enabled
                              since the factory reset will clear all of the
                              bonding data stored on the chip, meaning the
                              central device won't be able to reconnect.
    MINIMUM_FIRMWARE_VERSION  Minimum firmware version to have some new features
    MODE_LED_BEHAVIOUR        LED activity, valid options are
                              "DISABLE" or "MODE" or "BLEUART" or
                              "HWUART"  or "SPI"  or "MANUAL"
    -----------------------------------------------------------------------*/
    #define FACTORYRESET_ENABLE         
    #define MINIMUM_FIRMWARE_VERSION    "0.6.6"
    #define MODE_LED_BEHAVIOUR          "MODE"
/*=========================================================================*/

// BLE GATT definitions
#define VIB_SERVICE 0xABD0
#define VIB_CHAR 0xABD1
#define BTN_CHAR 0xABD2
#define DATA_SIZE 1
#define BTN_DATA_SIZE 2
#define VIB_CHAR_DESC "Vibration"
#define BTN_CHAR_DESC "Button"
#define VIB_SRV_LOW (VIB_SERVICE & 0x00FF)
#define VIB_SRV_HIGH ((VIB_SERVICE & 0xFF00) >> 8)

#define LED_PIN 6
#define ACT_PIN 9
#define BUTTON_PIN 10
#define VIB_CMD_ON 49
#define VIB_CMD_OFF 0
#define VIB_PULSE_MS 150
#define VIB_PULSE_INTV_MS 75
#define VIB_SET_INTV_MS 350
#define VIB_COOLDOWN_INTV_MS (VIB_SET_INTV_MS * 3)
#define BLINK_DURATION 100
#define BUT_DEBOUNCE_MS 20
#define BUT_MULT_CLICK_MS 250
#define BUT_LONG_CLICK_MS 1000

// Create the bluefruit object, either software serial...uncomment these lines
/*
SoftwareSerial bluefruitSS = SoftwareSerial(BLUEFRUIT_SWUART_TXD_PIN, BLUEFRUIT_SWUART_RXD_PIN);

Adafruit_BluefruitLE_UART ble(bluefruitSS, BLUEFRUIT_UART_MODE_PIN,
                      BLUEFRUIT_UART_CTS_PIN, BLUEFRUIT_UART_RTS_PIN);
*/

/* ...or hardware serial, which does not need the RTS/CTS pins. Uncomment this line */
Adafruit_BluefruitLE_UART ble(Serial1, BLUEFRUIT_UART_MODE_PIN);
Adafruit_BLEGatt gatt(ble);

/* ...hardware SPI, using SCK/MOSI/MISO hardware SPI pins and then user selected CS/IRQ/RST */
//Adafruit_BluefruitLE_SPI ble(BLUEFRUIT_SPI_CS, BLUEFRUIT_SPI_IRQ, BLUEFRUIT_SPI_RST);

/* ...software SPI, using SCK/MOSI/MISO user-defined SPI pins and then user selected CS/IRQ/RST */
//Adafruit_BluefruitLE_SPI ble(BLUEFRUIT_SPI_SCK, BLUEFRUIT_SPI_MISO,
//                             BLUEFRUIT_SPI_MOSI, BLUEFRUIT_SPI_CS,
//                             BLUEFRUIT_SPI_IRQ, BLUEFRUIT_SPI_RST);

Vibrator vibrator(ACT_PIN, LED_PIN);
ClickButton button(BUTTON_PIN, LOW, CLICKBTN_PULLUP);
TimedBlink led(LED_PIN);
uint8_t vibServiceId = 0;
uint16_t vibCharId = 0;
uint16_t btnCharId = 0;
bool toVib = false;
bool bleConnected = false;
bool bleDisconnected = false;

void vibGattRx(int32_t chars_id, uint8_t data[], uint16_t len);
void bleConnectCb();
void bleDisconnectCb();
void blink(int times, int duration);

// A small helper
void error(const __FlashStringHelper*err) {
    Serial.println(err);
    while (1);
}

/**************************************************************************/
/*!
    @brief  Sets up the HW an the BLE module (this function is called
            automatically on startup)
*/
/**************************************************************************/
void setup(void)
{
    ///// Initialise peripherals /////
    pinMode(ACT_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    vibrator.pulseDurationMs = VIB_PULSE_MS;
    vibrator.pulseIntervalDurationMs = VIB_PULSE_INTV_MS;
    vibrator.setIntervalDurationMs = VIB_SET_INTV_MS;
    vibrator.cooldownDurationMs = VIB_COOLDOWN_INTV_MS;
    button.debounceTime   = BUT_DEBOUNCE_MS;   // Debounce timer in ms
    button.multiclickTime = BUT_MULT_CLICK_MS;  // Time limit for multi clicks
    button.longClickTime  = BUT_LONG_CLICK_MS; // time until "held-down clicks" register
    led.blink(BLINK_DURATION, 400);
    ///// Initialise peripherals END /////
    
    ///// Initialise BLE module /////
    if (!ble.begin(VERBOSE_MODE))
    {
        error(F("Couldn't find Bluefruit, make sure it's in CoMmanD mode & check wiring?"));
    }
    blink(1, BLINK_DURATION);

    #ifdef FACTORYRESET_ENABLE
    /* Perform a factory reset to make sure everything is in a known state */
    while (!ble.factoryReset())
    {
        Serial.println(F("Couldn't factory reset"));
    }
    #endif

    /* Disable command echo from Bluefruit */
    ble.echo(false);

    // Add vibration service.
    while (vibServiceId == 0)
    {
        vibServiceId = gatt.addService(VIB_SERVICE);
        Serial.println(F("Could not add vibration Service"));
        delay(100);
    }

    // Add characteristic for vibration.
    while (vibCharId == 0)
    {
        vibCharId = gatt.addCharacteristic(VIB_CHAR, GATT_CHARS_PROPERTIES_WRITE, DATA_SIZE, 
            DATA_SIZE, BLE_DATATYPE_INTEGER, VIB_CHAR_DESC);
        Serial.println(F("Could not add vibration characteristic"));
        delay(100);
    }

    // Add characteristic for button presses.
    while (btnCharId == 0)
    {
        btnCharId = gatt.addCharacteristic(BTN_CHAR, GATT_CHARS_PROPERTIES_NOTIFY, BTN_DATA_SIZE, 
            BTN_DATA_SIZE, BLE_DATATYPE_BYTEARRAY, BTN_CHAR_DESC);
        Serial.println(F("Could not add button characteristic"));
        delay(100);
    }

    // Subscribe to incoming callback for vibration charactertistic.
    ble.setBleGattRxCallback(vibCharId, vibGattRx);

    // Advertise the vibration service to any central devices.
    uint8_t advdata[] { 0x02, 0x01, 0x06, 0x03, 0x02, VIB_SRV_HIGH, VIB_SRV_LOW };
    ble.setAdvData(advdata, sizeof(advdata));

    /* Reset the device for the new service setting changes to take effect */
    ble.reset();
    
    // LED Activity command is only supported from 0.6.6
    if (ble.isVersionAtLeast(MINIMUM_FIRMWARE_VERSION) )
    {
        // Change Mode LED Activity
        ble.sendCommandCheckOK("AT+HWModeLED=" MODE_LED_BEHAVIOUR);
    }

    ble.verbose(false);  // debug info is a little annoying after this point!
    
    ble.setConnectCallback(bleConnectCb);
    ble.setDisconnectCallback(bleDisconnectCb);
    ///// Initialise BLE module END /////
}

/**************************************************************************/
/*!
    @brief  Constantly poll for new command or response data
*/
/**************************************************************************/
void loop(void)
{
    button.Update();

    if (button.clicks != 0)
    {
        int16_t clicks = button.clicks;
        uint8_t data[BTN_DATA_SIZE] = { 0 };
        for (int i = 0; i < BTN_DATA_SIZE; i++)
        {
            data[i] = (uint8_t)((clicks >> (i * 8) & 0xFF));
        }
        gatt.setChar(btnCharId, data, BTN_DATA_SIZE);
    }
    

    ble.update();
    if (!ble.isConnected())
    {
        delay(10); // Wait for some time before next check.
        led.blink();
        return;
    }

    if (toVib)
    {
        Serial.println ("activate");
        vibrator.actuate(2, 2);
    }
    vibrator.update();
    
    delay(10);
}

/**
 * @brief Callback when data has arrived at the specified characteristic.
 * 
 * @param charsId Characteristic ID in which this callback happens for.
 * @param data Data in the characteristic.
 * @param len Length of data.
 */
void vibGattRx(int32_t charsId, uint8_t data[], uint16_t len)
{
    // Serial.print(F("[VIB] (" ));
    // Serial.print(charsId);
    // Serial.print("): ");
    
    if (charsId == vibCharId)
    {  
        // Serial.write(data, len);
        // Serial.println(data[0]);

        uint8_t cmd = data[0]; // The length must be at least 1.
        toVib = (cmd == VIB_CMD_ON);
    }
}

/**
 * @brief Callback when BLE connects.
 * 
 */
void bleConnectCb()
{
    led.blinkOff();
    digitalWrite(LED_PIN, HIGH);
}

/**
 * @brief Callback when BLE disconnects.
 * 
 */
void bleDisconnectCb()
{
    toVib = false;
    vibrator.cancel();
    led.blink(BLINK_DURATION, 400);
}

/**
 * @brief Blinks the LED a specified number of times and return to original state. (Blocking)
 * 
 * @param times Number of times to blink.
 * @param duration The duration (milliseconds) for ON and OFF state.
 */
void blink(int times, int duration)
{
    int initial = digitalRead(LED_PIN);
    for (int i = 0; i < times; i++)
    {
        digitalWrite(LED_PIN, HIGH);
        delay(duration);
        digitalWrite(LED_PIN, LOW);
        delay(duration);
    }
    digitalWrite(LED_PIN, initial); // Restore initial state.
}