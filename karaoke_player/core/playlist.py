from __future__ import annotations

from dataclasses import dataclass, field

from .models import Song


@dataclass
class PlaylistManager:
    songs: list[Song] = field(default_factory=list)
    current_index: int = -1

    def set_songs(self, songs: list[Song]) -> None:
        self.songs = list(songs)
        self.current_index = 0 if self.songs else -1

    def titles(self) -> list[str]:
        return [song.display_name for song in self.songs]

    def is_empty(self) -> bool:
        return not self.songs

    def current(self) -> Song | None:
        if 0 <= self.current_index < len(self.songs):
            return self.songs[self.current_index]
        return None

    def select(self, index: int) -> Song | None:
        if 0 <= index < len(self.songs):
            self.current_index = index
            return self.songs[index]
        return None

    def next(self) -> Song | None:
        if self.current_index + 1 < len(self.songs):
            self.current_index += 1
            return self.songs[self.current_index]
        return None

    def previous(self) -> Song | None:
        if self.current_index > 0:
            self.current_index -= 1
            return self.songs[self.current_index]
        return None
