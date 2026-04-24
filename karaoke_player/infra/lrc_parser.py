from __future__ import annotations

import re
from pathlib import Path

from karaoke_player.core.errors import LyricsParseError
from karaoke_player.core.models import LyricLine

_TIME_TAG_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]")
_METADATA_RE = re.compile(r"^\[(ti|ar|al|by|offset):", re.IGNORECASE)


def parse_lrc_text(text: str) -> list[LyricLine]:
    lines: list[LyricLine] = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if _METADATA_RE.match(stripped):
            continue

        matches = list(_TIME_TAG_RE.finditer(stripped))
        if not matches:
            continue

        lyric_text = _TIME_TAG_RE.sub("", stripped).strip()

        for match in matches:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            fraction = match.group(3) or "0"
            milliseconds = _fraction_to_ms(fraction)
            timestamp_ms = minutes * 60_000 + seconds * 1_000 + milliseconds
            lines.append(LyricLine(timestamp_ms=timestamp_ms, text=lyric_text))

    if not lines:
        raise LyricsParseError("Файл текста не содержит корректных строк с таймкодами.")

    lines.sort(key=lambda line: line.timestamp_ms)
    return lines


def parse_lrc_file(path: Path) -> list[LyricLine]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise LyricsParseError(f"Не удалось прочитать файл текста: {path}") from exc

    return parse_lrc_text(text)


def _fraction_to_ms(value: str) -> int:
    if len(value) == 1:
        return int(value) * 100
    if len(value) == 2:
        return int(value) * 10
    return int(value[:3])
