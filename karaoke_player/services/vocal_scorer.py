from __future__ import annotations

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, QTimer, Signal


class VocalScorer(QObject):
    score_changed = Signal(int, str)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._sample_rate = 44100
        self._block_size = 2048

        self._stream: sd.InputStream | None = None
        self._last_audio: np.ndarray | None = None

        self._total_checks = 0
        self._voice_checks = 0
        self._strong_voice_checks = 0
        self._score = 0

        self._timer = QTimer(self)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._analyze_voice)

    def load_notes(self, notes_path) -> None:
        """
        Оставлено для совместимости с controller.py.
        В этой простой версии .notes не нужны.
        """
        self.reset()

    def start(self) -> None:
        if self._stream is not None:
            return

        try:
            self._stream = sd.InputStream(
                channels=1,
                samplerate=self._sample_rate,
                blocksize=self._block_size,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._timer.start()

        except Exception as exc:
            self._stream = None
            self.error_occurred.emit(f"Не удалось включить микрофон: {exc}")

    def stop(self) -> None:
        self._timer.stop()

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None

    def reset(self) -> None:
        self._total_checks = 0
        self._voice_checks = 0
        self._strong_voice_checks = 0
        self._score = 0
        self.score_changed.emit(0, "Оценка пения: ждём голос")

    def set_position(self, position_ms: int) -> None:
        """
        Оставлено для совместимости с controller.py.
        Позиция песни тут не нужна.
        """
        pass

    def final_label(self) -> str:
        return f"Итоговая оценка: {self._score}/100 — {self._score_text(self._score)}"

    def _audio_callback(self, indata, frames, time, status) -> None:
        if status:
            return

        self._last_audio = indata[:, 0].copy()

    def _analyze_voice(self) -> None:
        if self._last_audio is None:
            return

        audio = self._last_audio.astype(np.float32)

        volume = float(np.sqrt(np.mean(audio * audio)))

        self._total_checks += 1

        if volume > 0.018:
            self._voice_checks += 1
            status = "голос есть"

            if volume > 0.045:
                self._strong_voice_checks += 1
                status = "хорошо слышно"
        else:
            status = "пойте громче"

        voice_part = self._voice_checks / max(1, self._total_checks)
        strong_part = self._strong_voice_checks / max(1, self._total_checks)

        self._score = int((voice_part * 0.75 + strong_part * 0.25) * 100)
        self._score = max(0, min(100, self._score))

        self.score_changed.emit(
            self._score,
            f"Оценка пения: {self._score}/100 — {status}",
        )

    @staticmethod
    def _score_text(score: int) -> str:
        if score >= 90:
            return "отлично"
        if score >= 70:
            return "хорошо"
        if score >= 45:
            return "нормально"
        if score > 0:
            return "слишком тихо"
        return "голос не найден"