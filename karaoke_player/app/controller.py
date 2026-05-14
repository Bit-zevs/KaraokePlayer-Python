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
from karaoke_player.services.vocal_scorer import VocalScorer

logger = logging.getLogger(__name__)


class AppController(QObject):
    playlist_changed = Signal(list, int)
    song_changed = Signal(object)
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_state_changed = Signal(str)
    active_lyric_changed = Signal(int)
    active_word_changed = Signal(int, int)
    score_changed = Signal(int, str)
    network_state_ready = Signal(dict)
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
        self._last_word: tuple[int, int] = (-1, -1)
        self._network_apply = False

        self._vocal_scorer = VocalScorer()
        self._vocal_scorer.score_changed.connect(self.score_changed)
        self._vocal_scorer.error_occurred.connect(self.error_occurred)

        self._player.position_changed.connect(self._on_position_changed)
        self._player.duration_changed.connect(self._on_duration_changed)
        self._player.state_changed.connect(self._on_state_changed)
        self._player.error_occurred.connect(self._on_error)
        self._player.song_finished.connect(self._on_song_finished)

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
        self._last_word = (-1, -1)

        self._vocal_scorer.reset()
        self._vocal_scorer.load_notes(song.notes_path)

        self._player.stop()
        self._player.set_source(song.audio_path)

        self.song_changed.emit(song)
        self.playlist_changed.emit(self._playlist.titles(), self._playlist.current_index)
        self.active_lyric_changed.emit(-1)
        self.active_word_changed.emit(-1, -1)
        self._emit_network_state()

        if autoplay:
            self.play()

    def select_song_by_title(self, title: str, autoplay: bool = False) -> bool:
        for index, song_title in enumerate(self._playlist.titles()):
            if song_title == title:
                self.select_song(index, autoplay=autoplay)
                return True

        return False

    def play(self) -> None:
        if self.state.current_song is None:
            self.info_message.emit("Сначала откройте папку с песнями или аудиофайл.")
            return

        self._vocal_scorer.start()
        self._player.play()
        self._emit_network_state()

    def pause(self) -> None:
        self._vocal_scorer.stop()
        self._player.pause()
        self._emit_network_state()

    def toggle_play_pause(self) -> None:
        if self.state.playback_state == "playing":
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        self._vocal_scorer.stop()
        self._player.stop()
        self.seek(0)
        self.score_changed.emit(0, self._vocal_scorer.final_label())
        self._emit_network_state()

    def seek(self, position_ms: int) -> None:
        self._player.seek(position_ms)
        self._vocal_scorer.set_position(position_ms)
        self._emit_active_lyric(position_ms)
        self._emit_network_state()

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

    def apply_network_state(self, payload: dict) -> None:
        """Apply playback state received from the network host."""

        if self._network_apply:
            return

        self._network_apply = True

        try:
            title = str(payload.get("title", ""))
            position_ms = int(payload.get("position_ms", 0))
            state = str(payload.get("playback_state", "stopped"))

            if title and (
                self.state.current_song is None
                or self.state.current_song.display_name != title
            ):
                if not self.select_song_by_title(title, autoplay=False):
                    self.info_message.emit(
                        f"По сети играет '{title}', но этой песни нет в вашем плейлисте."
                    )
                    return

            if abs(self._player.position() - position_ms) > 900:
                self._player.seek(position_ms)
                self._vocal_scorer.set_position(position_ms)

            if state == "playing" and self.state.current_song is not None:
                self._vocal_scorer.start()
                self._player.play()
            elif state == "paused":
                self._vocal_scorer.stop()
                self._player.pause()
            elif state == "stopped":
                self._vocal_scorer.stop()
                self._player.stop()

        finally:
            self._network_apply = False

    def network_snapshot(self) -> dict:
        return {
            "title": self.state.current_song.display_name
            if self.state.current_song
            else "",
            "position_ms": self._player.position(),
            "duration_ms": self._player.duration(),
            "playback_state": self.state.playback_state,
        }

    def _load_and_replace(self, loader_call) -> None:
        try:
            songs = loader_call()
        except KaraokeError as exc:
            logger.exception("Load failed")
            self.error_occurred.emit(str(exc))
            return

        self._playlist.set_songs(songs)
        self.state.playlist_titles = self._playlist.titles()
        self.state.current_playlist_index = self._playlist.current_index

        self.playlist_changed.emit(
            self._playlist.titles(),
            self._playlist.current_index,
        )
        self.select_song(0, autoplay=False)

    def _on_position_changed(self, position_ms: int) -> None:
        self.state.position_ms = position_ms
        self.position_changed.emit(position_ms)

        self._vocal_scorer.set_position(position_ms)

        self._emit_active_lyric(position_ms)
        self._emit_network_state()

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.state.duration_ms = duration_ms
        self.duration_changed.emit(duration_ms)

    def _on_state_changed(self, state: str) -> None:
        self.state.playback_state = state
        self.playback_state_changed.emit(state)
        self._emit_network_state()

    def _on_song_finished(self) -> None:
        self._vocal_scorer.stop()
        self.score_changed.emit(0, self._vocal_scorer.final_label())
        self.play_next()

    def _emit_active_lyric(self, position_ms: int) -> None:
        index = self._synchronizer.active_index(position_ms)

        if index != self._last_lyric_index:
            self._last_lyric_index = index
            self.state.active_lyric_index = index
            self.active_lyric_changed.emit(index)

        word_line, word_index = self._synchronizer.active_word_index(position_ms)

        if (word_line, word_index) != self._last_word:
            self._last_word = (word_line, word_index)
            self.active_word_changed.emit(word_line, word_index)

    def _emit_network_state(self) -> None:
        if not self._network_apply:
            self.network_state_ready.emit(self.network_snapshot())

    def _on_error(self, message: str) -> None:
        logger.error("Playback error: %s", message)
        self.error_occurred.emit(message)