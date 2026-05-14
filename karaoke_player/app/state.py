from __future__ import annotations

from dataclasses import dataclass, field

from karaoke_player.core.models import Song


@dataclass
class AppState:
    current_song: Song | None = None
    playback_state: str = "stopped"
    position_ms: int = 0
    duration_ms: int = 0
    active_lyric_index: int = -1
    playlist_titles: list[str] = field(default_factory=list)
    current_playlist_index: int = -1
