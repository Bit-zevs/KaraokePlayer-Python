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

    def active_word_index(self, position_ms: int) -> tuple[int, int]:

        line_index = self.active_index(position_ms)
        if line_index < 0:
            return -1, -1

        words = self._lines[line_index].words
        if not words:
            return line_index, -1

        exact_points = [word.timestamp_ms for word in words]
        if any(point is not None for point in exact_points):
            valid_points = [point if point is not None else -1 for point in exact_points]
            index = bisect_right(valid_points, position_ms) - 1
            return line_index, max(0, min(index, len(words) - 1))

        line_start = self._lines[line_index].timestamp_ms
        if line_index + 1 < len(self._lines):
            line_end = self._lines[line_index + 1].timestamp_ms
        else:
            line_end = line_start + max(1800, len(words) * 450)

        duration = max(1, line_end - line_start)
        progress = max(0.0, min(0.999, (position_ms - line_start) / duration))
        return line_index, min(int(progress * len(words)), len(words) - 1)