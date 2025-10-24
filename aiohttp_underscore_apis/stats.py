from collections import deque
from dataclasses import dataclass, field
from time import time


class TimeAverage:
    def __init__(self) -> None:
        self._records: deque[tuple[float, float]] = deque()

    def record(self, duration: float):
        now = time()
        self._records.append((now, duration))
        self._cutoff(now - 15 * 60)

    def _cutoff(self, earlier_than):
        while self._records and self._records[0][0] < earlier_than:
            self._records.popleft()

    def calculate(self) -> tuple[float, float, float]:
        now = time()
        self._cutoff(now - 15 * 60)

        avg_1m, avg_5m, avg_15m = 0 + 0j, 0 + 0j, 0 + 0j
        ago_1m, ago_5m, ago_15m = now - 60, now - 300, now - 900

        for timestamp, duration in self._records:
            if timestamp >= ago_1m:
                avg_1m += duration + 1j
            if timestamp >= ago_5m:
                avg_5m += duration + 1j
            if timestamp >= ago_15m:
                avg_15m += duration + 1j

        return (
            avg_1m.real / avg_1m.imag if avg_1m.imag else float("nan"),
            avg_5m.real / avg_5m.imag if avg_5m.imag else float("nan"),
            avg_15m.real / avg_15m.imag if avg_15m.imag else float("nan"),
        )


@dataclass
class Counter:
    active: int = 0
    total: int = 0


@dataclass
class RouteStats:
    counter: Counter = field(default_factory=Counter)
    time_avg: TimeAverage = field(default_factory=TimeAverage)
