from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class LyricLine:
    timestamp_ms: int
    text: str


@dataclass(slots=True)
class Song:
    title: str
    audio_path: Path
    lyrics_path: Path | None = None
    lyrics: list[LyricLine] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.title or self.audio_path.stem
