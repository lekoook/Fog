#include "Vibrator.hpp"

Vibrator::Vibrator(int vibratorPin, int ledPin)
{
    _vibratorPin = vibratorPin;
    _ledPin = ledPin;
}

Vibrator::~Vibrator()
{
}

void Vibrator::update()
{
    if (_currentPulses > 0)
    {
        if (_isPulsing && (millis() - _pulseStartTime >= (uint32_t)pulseDurationMs))
        {
            _isPulsing = false;
            _currentPulses -= 1;
            _pulseIntervalStartTime = millis();
            digitalWrite(_vibratorPin, LOW);
            digitalWrite(_ledPin, LOW);

            if (_currentPulses == 0)
            {
                _setIntervalStartTime = millis();
                if (_sets == 0)
                {
                    digitalWrite(_ledPin, _ledInitialState);
                }
            }
        }
        else if (!_isPulsing && (millis() - _pulseIntervalStartTime >= (uint32_t)pulseIntervalDurationMs))
        {
            if (_currentPulses > 0)
            {
                _isPulsing = true;
                _pulseStartTime = millis();
                digitalWrite(_vibratorPin, HIGH);
                digitalWrite(_ledPin, HIGH);
            }
        }
    }
    else
    {
        if (_setIntervalStartTime > 0)
        {
            if (_sets > 0)
            {
                if (millis() - _setIntervalStartTime >= (uint32_t)setIntervalDurationMs)
                {
                    _setIntervalStartTime = 0;
                }
            }
            else
            {
                if (millis() - _setIntervalStartTime >= (uint32_t)cooldownDurationMs)
                {
                    _setIntervalStartTime = 0;
                }
            }
        }
        else if (_sets > 0)
        {
            _sets -= 1;
            _isPulsing = true;
            _currentPulses =_pulses;
            _pulseStartTime = millis();
            digitalWrite(_vibratorPin, HIGH);
            digitalWrite(_ledPin, HIGH);
        }
        else if (_sets == 0)
        {
            _reset();
        }
    }
}

void Vibrator::cancel()
{
    if (_sets > 0 || _pulses > 0)
    {
        _reset();
        digitalWrite(_vibratorPin, LOW);
        digitalWrite(_ledPin, _ledInitialState);
    }
}

void Vibrator::actuate(uint8_t sets, uint8_t pulses)
{
    // Only set parameters if the previous ones are done.
    if (_sets == 0 && _pulses == 0 && sets > 0 && pulses > 0)
    {
        _ledInitialState = digitalRead(_ledPin);
        _sets = sets;
        _pulses = pulses;
        _currentPulses = 0;
        _isPulsing = false;
        _setIntervalStartTime = 0;
    }
}

void Vibrator::_reset()
{
    _sets = 0;
    _pulses = 0;
    _currentPulses = 0;
    _isPulsing = false;
}