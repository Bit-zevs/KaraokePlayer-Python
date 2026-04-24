from __future__ import annotations

from bisect import bisect_right

from .models import LyricLine


class LyricsSynchronizer:
    def __init__(self, lines: list[LyricLine]) -> None:
        self._lines = sorted(lines, key=lambda line: line.timestamp_ms)
        self._timestamps = [line.timestamp_ms for line in self._lines]

    @property
    def lines(self) -> list[LyricLine]:
        return self._lines

    def active_index(self, position_ms: int) -> int:
        if not self._timestamps:
            return -1
        index = bisect_right(self._timestamps, position_ms) - 1
        return index if index >= 0 else -1
