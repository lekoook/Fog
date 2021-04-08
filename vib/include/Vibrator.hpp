#ifndef VIBRATOR_H_
#define VIBRATOR_H_

#include <Arduino.h>

class Vibrator
{
private:
    int _vibratorPin = -1;
    int _ledPin = -1;
    int _ledInitialState = 0;
    int _sets = 0;
    int _pulses = 0;
    int _currentPulses = 0;
    bool _isPulsing = false;
    uint32_t _pulseStartTime = 0;
    uint32_t _pulseIntervalStartTime = 0;
    uint32_t _setIntervalStartTime = 0;

    /**
     * @brief Reset the parameters.
     * 
     */
    void _reset();
    
public:
    int pulseDurationMs = 0;
    int pulseIntervalDurationMs = 0;
    int setIntervalDurationMs = 0;
    int cooldownDurationMs = 0;

    /**
     * @brief Construct a new Vibrator object.
     * 
     * @param vibratorPin Pin number to actuate the vibrator. Defaults to logic high.
     * @param ledPin Pin number to flash LED. Defaults to logic high.
     */
    Vibrator(int vibratorPin, int ledPin);

    /**
     * @brief Destroy the Vibrator object.
     * 
     */
    ~Vibrator();

    /**
     * @brief Processes the actuation and time tracking.
     * 
     */
    void update();

    /**
     * @brief Cancel any actuation set previously.
     * 
     */
    void cancel();

    /**
     * @brief Sets the number of sets and pulses to actuate. A set contains the specified number of pulses.
     * 
     * @param sets The number of sets of pulses to actuate.
     * @param pulses The number of pulses to actuate in each set.
     */
    void actuate(uint8_t sets, uint8_t pulses);
};

#endif