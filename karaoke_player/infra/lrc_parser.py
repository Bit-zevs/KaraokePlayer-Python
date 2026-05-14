from __future__ import annotations

import re
from pathlib import Path

from karaoke_player.core.errors import LyricsParseError
from karaoke_player.core.models import LyricLine, LyricWord

_TIME_TAG_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]")
_WORD_TIME_RE = re.compile(r"<(?P<m>\d{1,2}):(?P<s>\d{2})(?:[.:](?P<f>\d{1,3}))?>")
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

        lyric_part = _TIME_TAG_RE.sub("", stripped).strip()
        plain_text, words = _parse_words(lyric_part)

        for match in matches:
            timestamp_ms = _time_match_to_ms(match)
            lines.append(
                LyricLine(
                    timestamp_ms=timestamp_ms,
                    text=plain_text,
                    words=tuple(words),
                )
            )

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


def _parse_words(lyric_part: str) -> tuple[str, list[LyricWord]]:
    word_tags = list(_WORD_TIME_RE.finditer(lyric_part))
    if not word_tags:
        plain = lyric_part.strip()
        return plain, list(LyricWord(word) for word in plain.split())

    words: list[LyricWord] = []
    for index, tag in enumerate(word_tags):
        start = tag.end()
        end = word_tags[index + 1].start() if index + 1 < len(word_tags) else len(lyric_part)
        chunk = lyric_part[start:end]
        timestamp_ms = _word_match_to_ms(tag)
        next_timestamp = _word_match_to_ms(word_tags[index + 1]) if index + 1 < len(word_tags) else None

        for word in chunk.split():
            words.append(
                LyricWord(
                    text=word,
                    timestamp_ms=timestamp_ms,
                    end_ms=next_timestamp,
                )
            )
            timestamp_ms = None

    plain = " ".join(word.text for word in words).strip()
    return plain, words


def _time_match_to_ms(match: re.Match[str]) -> int:
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    fraction = match.group(3) or "0"
    return minutes * 60_000 + seconds * 1_000 + _fraction_to_ms(fraction)


def _word_match_to_ms(match: re.Match[str]) -> int:
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    fraction = match.group("f") or "0"
    return minutes * 60_000 + seconds * 1_000 + _fraction_to_ms(fraction)


def _fraction_to_ms(value: str) -> int:
    if len(value) == 1:
        return int(value) * 100
    if len(value) == 2:
        return int(value) * 10
    return int(value[:3])