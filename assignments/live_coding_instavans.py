'''
Write a Python class called StreamProcessor that accepts a stream of integers.
Implement a method add_reading(value) that maintains a sliding window of the last N observations.
Implement a method is_anomaly() that returns True if the latest value is more than 3 standard deviations away from the window mean.
The Constraint: You cannot use pandas or numpy. Use only the Python Standard Library.
The 'Expert' Twist: Ensure the solution is O(1) or O(k) for time complexity per insertion, rather than recalculating the entire list every time

'''
from math import sqrt
from collections import deque

class StreamProcessor:
    def __init__(self, window_size: int):
        self.window_size = window_size
        self.window = deque()
        self.sum = 0.0
        self.sum_sq = 0.0

    def add_reading(self, value: int) -> None:
        if len(self.window) == self.window_size:
            old = self.window.popleft()
            self.sum -= old
            self.sum_sq -= old * old

        self.window.append(value)
        self.sum += value
        self.sum_sq += value * value

    def mean(self):
        return self.sum / len(self.window)

    def std(self):
        n = len(self.window)
        if n < 2:
            return 0.0
        mean = self.sum / n
        variance = (self.sum_sq / n) - (mean * mean)
        return sqrt(max(variance, 0.0))

    def is_anomaly(self) -> bool:
        if len(self.window) < 2:
            return False

        x = self.window[-1]
        mu = self.mean()
        sigma = self.std()

        if sigma == 0:
            return False

        return abs(x - mu) > 3 * sigma
