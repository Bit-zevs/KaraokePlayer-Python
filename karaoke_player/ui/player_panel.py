from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class PlayerPanel(QFrame):
    play_pause_clicked = Signal()
    stop_clicked = Signal()
    previous_clicked = Signal()
    next_clicked = Signal()
    seek_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._slider_pressed = False
        self._position_ms = 0
        self._duration_ms = 0

        self.setObjectName("playerPanel")

        self.previous_button = self._build_button("⏮")
        self.play_pause_button = self._build_button("▶")
        self.stop_button = self._build_button("■")
        self.next_button = self._build_button("⏭")

        self.current_time_label = QLabel("00:00")
        self.current_time_label.setObjectName("timeValue")
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setObjectName("timeValueMuted")

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setObjectName("positionSlider")

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.current_time_label)
        controls_layout.addWidget(QLabel("/"))
        controls_layout.addWidget(self.total_time_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(self.position_slider)
        layout.addLayout(controls_layout)

        self.previous_button.clicked.connect(self.previous_clicked.emit)
        self.play_pause_button.clicked.connect(self.play_pause_clicked.emit)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)

        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)

    def set_duration(self, duration_ms: int) -> None:
        self._duration_ms = max(duration_ms, 0)
        self.position_slider.setRange(0, self._duration_ms)
        self._refresh_time_labels()

    def set_position(self, position_ms: int) -> None:
        self._position_ms = max(position_ms, 0)
        if not self._slider_pressed:
            self.position_slider.setValue(self._position_ms)
        self._refresh_time_labels()

    def set_playback_state(self, state: str) -> None:
        self.play_pause_button.setText("⏸" if state == "playing" else "▶")

    def _on_slider_pressed(self) -> None:
        self._slider_pressed = True

    def _on_slider_released(self) -> None:
        self._slider_pressed = False
        self.seek_requested.emit(self.position_slider.value())

    def _refresh_time_labels(self) -> None:
        shown_position = self.position_slider.value() if self._slider_pressed else self._position_ms
        self.current_time_label.setText(self._format_ms(shown_position))
        self.total_time_label.setText(self._format_ms(self._duration_ms))

    def _build_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("playerButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(42, 42)
        return button

    @staticmethod
    def _format_ms(value: int) -> str:
        seconds = max(value, 0) // 1000
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
