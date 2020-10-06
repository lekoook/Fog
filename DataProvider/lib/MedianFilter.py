#!/usr/bin/python3

from collections import deque
from statistics import median

class MedianFilter():
    """
    This class represents a Median filter.
    """

    def __init__(self, windowSize: int, initials: [float]=[]):
        if windowSize % 2 is 0:
            raise ValueError("Window size must be odd value")
        self.buffer = deque(initials[0 : windowSize], maxlen=windowSize)
        for i in range(len(self.buffer), windowSize):
            self.buffer.append(0)
    
    def filt(self, new: float) -> float:
        """
        Filters the specified new value based on previous values.

        Args:
            new (float): New value to filter.

        Returns:
            float: Filtered value based on previous 'windowSize' number of elements.
        """
        self.buffer.popleft()
        self.buffer.append(new)
        return median(self.buffer)
