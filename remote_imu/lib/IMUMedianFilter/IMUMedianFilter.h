#ifndef IMU_MEDIAN_FILTER_H_
#define IMU_MEDIAN_FILTER_H_

#include "CircularBuffer.h"
#include "IMUValue.h"
#include "assert.h"

template<size_t windowSize>
class IMUMedianFilter
{
private:
    CircularBuffer<int16_t, windowSize> axBuffer;
    CircularBuffer<int16_t, windowSize> ayBuffer;
    CircularBuffer<int16_t, windowSize> azBuffer;
    CircularBuffer<int16_t, windowSize> gxBuffer;
    CircularBuffer<int16_t, windowSize> gyBuffer;
    CircularBuffer<int16_t, windowSize> gzBuffer;
    CircularBuffer<int16_t, windowSize> mxBuffer;
    CircularBuffer<int16_t, windowSize> myBuffer;
    CircularBuffer<int16_t, windowSize> mzBuffer;
    
    void appendBuffer(IMUValue value)
    {
        axBuffer.put(value.accelVect.x);
        ayBuffer.put(value.accelVect.y);
        azBuffer.put(value.accelVect.z);
        gxBuffer.put(value.gyroVect.x);
        gyBuffer.put(value.gyroVect.y);
        gzBuffer.put(value.gyroVect.z);
        mxBuffer.put(value.magVect.x);
        myBuffer.put(value.magVect.y);
        mzBuffer.put(value.magVect.z);
    }

    int16_t findMedian(int16_t array[], int16_t len)
    {
        int16_t arr[len];
        for (int i = 0; i < len; i++)
        {
            arr[i] = array[i];
        }
        int16_t count = len;

        randomSeed(millis());
        bool found = false;
        int16_t left[len];
        int16_t right[len];
        int16_t pivot = 0;
        int16_t middle = (count % 2 == 0) ? count / 2 - 1 : count / 2;

        while (!found)
        {
            int16_t leftCount = 0;
            int16_t rightCount = 0;
            int pivotIdx = random() % count;
            pivot = arr[pivotIdx];

            // Split into left right partition
            for (int i = 0; i < count; i++)
            {
                if (i == pivotIdx)
                {
                    continue;
                }

                if (arr[i] <= pivot)
                {
                    left[leftCount] = arr[i];
                    leftCount++;
                }
                else
                {
                    right[rightCount] = arr[i];
                    rightCount++;
                }
            }

            if (middle == leftCount)
            {
                found = true;
            }
            else if (middle + 1 <= leftCount)
            {
                for (int i = 0; i < leftCount; i++)
                {
                    arr[i] = left[i];
                }
                count = leftCount;
            }
            else
            {
                for (int i = 0; i < rightCount; i++)
                {
                    arr[i] = right[i];
                }
                count = rightCount;
                middle = middle - leftCount - 1;
            }
        }
        return pivot;
    }

public:
    IMUMedianFilter()
    {
        static_assert(windowSize % 2 != 0, "Window size must be odd number");
    }

    IMUValue filter(IMUValue current)
    {
        appendBuffer(current);

        int len = this->axBuffer.size();
        int16_t axBuffer[len];
        int16_t ayBuffer[len];
        int16_t azBuffer[len];
        int16_t gxBuffer[len];
        int16_t gyBuffer[len];
        int16_t gzBuffer[len];
        int16_t mxBuffer[len];
        int16_t myBuffer[len];
        int16_t mzBuffer[len];
        this->axBuffer.getArray(axBuffer);
        this->ayBuffer.getArray(ayBuffer);
        this->azBuffer.getArray(azBuffer);
        this->gxBuffer.getArray(gxBuffer);
        this->gyBuffer.getArray(gyBuffer);
        this->gzBuffer.getArray(gzBuffer);
        this->mxBuffer.getArray(mxBuffer);
        this->myBuffer.getArray(myBuffer);
        this->mzBuffer.getArray(mzBuffer);
        int16_t axm = findMedian(axBuffer, len);
        int16_t aym = findMedian(ayBuffer, len);
        int16_t azm = findMedian(azBuffer, len);
        int16_t gxm = findMedian(gxBuffer, len);
        int16_t gym = findMedian(gyBuffer, len);
        int16_t gzm = findMedian(gzBuffer, len);
        int16_t mxm = findMedian(mxBuffer, len);
        int16_t mym = findMedian(myBuffer, len);
        int16_t mzm = findMedian(mzBuffer, len);

        return IMUValue(axm, aym, azm, gxm, gym, gzm, mxm, mym, mzm);
    }


};

#endif // IMU_MEDIAN_FILTER_H_