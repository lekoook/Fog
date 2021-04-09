#!/usr/bin/python3

from collections import deque
# TODO: Protect with locks
class DataBuffer():
    """
    Wrapper over collections.deque to allow specific data structure operations.

    This data structure allows you push items to the back and then pop them from the front again. Essentially behaving like a First-In-First-Out (FIFO) buffer.

    Additionally, it also provides you a way to look at 'n' number of oldest items without removing them.
    """
    def __init__(self):
        self.buffer = deque()

    def __len__(self):
        return len(self.buffer)

    def push(self, item):
        """
        Pushes an item in.

        Args:
            item : Item to push
        """
        self.buffer.append(item)

    def pop(self):
        """
        Pops the oldest item.

        Returns:
            Oldest item. If the buffer was empty to begin with, returns 'None'.
        """

        try:
            v = self.buffer.popleft()
            return v
        except IndexError:
            return None

    def peek(self, n=1) -> list:
        """
        Peeks with removing the first 'n' items in the buffer, starting from the oldest item.

        Args:
            n (int, optional): Specifies the number of items to peek. Defaults to 1.

        Returns:
            list: Contains all the peeked items, starting from the oldest, ending with the newest item.
        """

        if len(self.buffer) >= n and n >= 1:
            result = []
            for i in range(0, n):
                self.buffer.rotate(-i)
                result.append(self.buffer[0])

            self.buffer.rotate(n - 1)
            return result