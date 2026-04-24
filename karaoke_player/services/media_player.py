from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class QtMediaPlayerAdapter(QObject):
    position_changed = Signal(int)
    duration_changed = Signal(int)
    state_changed = Signal(str)
    error_occurred = Signal(str)
    song_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._audio_output.setVolume(0.7)
        self._player.setAudioOutput(self._audio_output)

        self._player.positionChanged.connect(self.position_changed.emit)
        self._player.durationChanged.connect(self.duration_changed.emit)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.errorOccurred.connect(self._on_error)

    def set_source(self, path: Path) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(path.resolve())))

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def seek(self, position_ms: int) -> None:
        self._player.setPosition(max(position_ms, 0))

    def set_volume(self, volume: float) -> None:
        self._audio_output.setVolume(max(0.0, min(volume, 1.0)))

    def position(self) -> int:
        return self._player.position()

    def duration(self) -> int:
        return self._player.duration()

    def playback_state(self) -> str:
        return self._state_to_text(self._player.playbackState())

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.state_changed.emit(self._state_to_text(state))

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.song_finished.emit()

    def _on_error(self, *_args: object) -> None:
        message = self._player.errorString() or "Неизвестная ошибка воспроизведения."
        self.error_occurred.emit(message)

    @staticmethod
    def _state_to_text(state: QMediaPlayer.PlaybackState) -> str:
        mapping = {
            QMediaPlayer.PlaybackState.PlayingState: "playing",
            QMediaPlayer.PlaybackState.PausedState: "paused",
            QMediaPlayer.PlaybackState.StoppedState: "stopped",
        }
        return mapping.get(state, "stopped")
