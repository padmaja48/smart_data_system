"""
iterators.py - Custom iterator classes implementing the iterator protocol.

Demonstrates:
- Custom __iter__ and __next__ methods
- Iterator pattern with state management
- Fixed-capacity circular buffer
- Float-step range iteration (like range() but with float steps)
"""


class DatasetRowIterator:
    """
    Custom iterator that goes through a dataset row by row.
    Implements the iterator protocol using __iter__ and __next__.
    """

    def __init__(self, data):
        self._data = data
        self._index = 0

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._data):
            raise StopIteration
        row = self._data[self._index]
        self._index += 1
        return row

    def __len__(self):
        return len(self._data)


class CircularBufferIterator:
    """
    Fixed-capacity circular buffer with iterator protocol.
    When full, new items push out old items (FIFO).
    Useful for keeping a log of recent events without unbounded growth.
    """

    def __init__(self, capacity=50):
        self.capacity = capacity
        self._buffer = []
        self._index = 0

    def append(self, item):
        """Add an item to the buffer. Oldest item is dropped if full."""
        if len(self._buffer) < self.capacity:
            self._buffer.append(item)
        else:
            self._buffer[self._index] = item
        self._index = (self._index + 1) % self.capacity

    def __iter__(self):
        """Return an iterator over the current buffer contents."""
        return iter(list(self._buffer))

    def __len__(self):
        return len(self._buffer)

    def __repr__(self):
        return f"<CircularBufferIterator size={len(self._buffer)}/{self.capacity}>"


class RangeStepIterator:
    """
    Float-step range iterator — like range() but with float steps.
    range(1, 5, 0.5) yields 1.0, 1.5, 2.0, 2.5, 3.0, ..., 4.5
    """

    def __init__(self, start, stop, step=1):
        if step == 0:
            raise ValueError("step cannot be zero")
        self.start = start
        self.stop = stop
        self.step = step
        self._current = start

    def __iter__(self):
        self._current = self.start
        return self

    def __next__(self):
        if self.step > 0 and self._current >= self.stop:
            raise StopIteration
        if self.step < 0 and self._current <= self.stop:
            raise StopIteration
        
        value = self._current
        self._current += self.step
        return value

    def __len__(self):
        """Return number of items that would be yielded."""
        if self.step > 0:
            count = max(0, (self.stop - self.start) / self.step)
        else:
            count = max(0, (self.start - self.stop) / abs(self.step))
        return int(count)
