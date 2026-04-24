from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from karaoke_player.app.state import AppState
from karaoke_player.core.errors import KaraokeError
from karaoke_player.core.playlist import PlaylistManager
from karaoke_player.core.sync import LyricsSynchronizer
from karaoke_player.services.media_player import QtMediaPlayerAdapter
from karaoke_player.services.song_loader import SongLoader

logger = logging.getLogger(__name__)


class AppController(QObject):
    playlist_changed = Signal(list, int)
    song_changed = Signal(object)
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_state_changed = Signal(str)
    active_lyric_changed = Signal(int)
    error_occurred = Signal(str)
    info_message = Signal(str)

    def __init__(self, loader: SongLoader, player: QtMediaPlayerAdapter) -> None:
        super().__init__()
        self._loader = loader
        self._player = player
        self._playlist = PlaylistManager()
        self.state = AppState()
        self._synchronizer = LyricsSynchronizer([])
        self._last_lyric_index = -1

        self._player.position_changed.connect(self._on_position_changed)
        self._player.duration_changed.connect(self._on_duration_changed)
        self._player.state_changed.connect(self._on_state_changed)
        self._player.error_occurred.connect(self._on_error)
        self._player.song_finished.connect(self.play_next)

    def load_folder(self, folder: Path) -> None:
        self._load_and_replace(lambda: self._loader.load_folder(folder))

    def load_files(self, files: list[Path]) -> None:
        self._load_and_replace(lambda: self._loader.load_paths(files))

    def select_song(self, index: int, autoplay: bool = True) -> None:
        song = self._playlist.select(index)
        if song is None:
            return

        self.state.current_song = song
        self.state.current_playlist_index = self._playlist.current_index
        self._synchronizer = LyricsSynchronizer(song.lyrics)
        self._last_lyric_index = -1

        self._player.stop()
        self._player.set_source(song.audio_path)
        self.song_changed.emit(song)
        self.playlist_changed.emit(self._playlist.titles(), self._playlist.current_index)
        self.active_lyric_changed.emit(-1)

        if autoplay:
            self.play()

    def play(self) -> None:
        if self.state.current_song is None:
            self.info_message.emit("Сначала откройте папку с песнями или аудиофайл.")
            return
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def toggle_play_pause(self) -> None:
        if self.state.playback_state == "playing":
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        self._player.stop()
        self.seek(0)

    def seek(self, position_ms: int) -> None:
        self._player.seek(position_ms)
        self._emit_active_lyric(position_ms)

    def play_next(self) -> None:
        next_song = self._playlist.next()
        if next_song is None:
            self.stop()
            return
        self.select_song(self._playlist.current_index, autoplay=True)

    def play_previous(self) -> None:
        previous_song = self._playlist.previous()
        if previous_song is None:
            self.seek(0)
            return
        self.select_song(self._playlist.current_index, autoplay=True)

    def _load_and_replace(self, loader_call) -> None:  # type: ignore[no-untyped-def]
        try:
            songs = loader_call()
        except KaraokeError as exc:
            logger.exception("Load failed")
            self.error_occurred.emit(str(exc))
            return

        self._playlist.set_songs(songs)
        self.state.playlist_titles = self._playlist.titles()
        self.state.current_playlist_index = self._playlist.current_index
        self.playlist_changed.emit(self._playlist.titles(), self._playlist.current_index)
        self.select_song(0, autoplay=False)

    def _on_position_changed(self, position_ms: int) -> None:
        self.state.position_ms = position_ms
        self.position_changed.emit(position_ms)
        self._emit_active_lyric(position_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.state.duration_ms = duration_ms
        self.duration_changed.emit(duration_ms)

    def _on_state_changed(self, state: str) -> None:
        self.state.playback_state = state
        self.playback_state_changed.emit(state)

    def _emit_active_lyric(self, position_ms: int) -> None:
        index = self._synchronizer.active_index(position_ms)
        if index != self._last_lyric_index:
            self._last_lyric_index = index
            self.state.active_lyric_index = index
            self.active_lyric_changed.emit(index)

    def _on_error(self, message: str) -> None:
        logger.error("Playback error: %s", message)
        self.error_occurred.emit(message)
