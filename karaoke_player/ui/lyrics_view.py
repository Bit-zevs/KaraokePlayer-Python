from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from karaoke_player.core.models import LyricLine


def _mix_color(start: QColor, end: QColor, factor: float) -> QColor:
    factor = max(0.0, min(factor, 1.0))
    return QColor(
        round(start.red() + (end.red() - start.red()) * factor),
        round(start.green() + (end.green() - start.green()) * factor),
        round(start.blue() + (end.blue() - start.blue()) * factor),
    )


class AnimatedLyricLabel(QLabel):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._accent = 0.0
        self._inactive_size = 15.0
        self._active_size = 24.0

        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(60)
        self.setContentsMargins(10, 4, 10, 4)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.55)
        self.setGraphicsEffect(self._opacity_effect)
        self._refresh_style()

    def get_accent(self) -> float:
        return self._accent

    def set_accent(self, value: float) -> None:
        self._accent = max(0.0, min(value, 1.0))
        self._opacity_effect.setOpacity(0.55 + 0.45 * self._accent)
        self._refresh_style()

    accent = Property(float, get_accent, set_accent)

    def _refresh_style(self) -> None:
        text_color = _mix_color(QColor("#8E9BB5"), QColor("#F8FAFC"), self._accent)
        border_color = _mix_color(QColor("#20293A"), QColor("#7C3AED"), self._accent)
        bg_color = QColor(124, 58, 237, round(28 + 46 * self._accent))

        font = QFont(self.font())
        font.setPointSizeF(self._inactive_size + (self._active_size - self._inactive_size) * self._accent)
        font.setWeight(QFont.Weight.Medium if self._accent < 0.75 else QFont.Weight.DemiBold)
        self.setFont(font)

        self.setStyleSheet(
            "QLabel {"
            f"color: {text_color.name()};"
            f"background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, {bg_color.alpha()});"
            f"border: 1px solid {border_color.name()};"
            "border-radius: 18px;"
            "padding: 14px 18px;"
            "}"
        )


class LyricsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._line_widgets: list[AnimatedLyricLabel] = []
        self._line_animations: dict[AnimatedLyricLabel, QPropertyAnimation] = {}
        self._scroll_animation: QPropertyAnimation | None = None
        self._active_index = -1
        self._placeholder_mode = True

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(32, 28, 32, 28)
        self._layout.setSpacing(12)
        self._scroll_area.setWidget(self._content)

        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(self._scroll_area)

    def set_lyrics(self, lines: list[LyricLine]) -> None:
        self._clear_layout()
        self._line_widgets.clear()
        self._line_animations.clear()
        self._active_index = -1

        if not lines:
            self._placeholder_mode = True
            placeholder = AnimatedLyricLabel("No synchronized lyrics for this song.")
            placeholder.set_accent(0.25)
            self._layout.addStretch(1)
            self._layout.addWidget(placeholder)
            self._layout.addStretch(1)
            return

        self._placeholder_mode = False
        self._layout.addStretch(1)
        for line in lines:
            label = AnimatedLyricLabel(line.text or "…")
            self._line_widgets.append(label)
            self._layout.addWidget(label)
        self._layout.addStretch(1)

    def set_active_index(self, index: int) -> None:
        if self._placeholder_mode:
            return

        self._active_index = index
        for row, label in enumerate(self._line_widgets):
            target = self._target_accent(row, index)
            self._animate_accent(label, target)

        if 0 <= index < len(self._line_widgets):
            self._animate_scroll_to_widget(self._line_widgets[index])

    def _target_accent(self, row: int, active_index: int) -> float:
        if active_index < 0:
            return 0.0
        distance = abs(row - active_index)
        if distance == 0:
            return 1.0
        if distance == 1:
            return 0.4
        if distance == 2:
            return 0.15
        return 0.0

    def _animate_accent(self, label: AnimatedLyricLabel, target: float) -> None:
        current = label.get_accent()
        if abs(current - target) < 0.01:
            label.set_accent(target)
            return

        existing = self._line_animations.get(label)
        if existing is not None:
            existing.stop()

        animation = QPropertyAnimation(label, b"accent", self)
        animation.setDuration(220)
        animation.setStartValue(current)
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda key=label: self._line_animations.pop(key, None))
        self._line_animations[label] = animation
        animation.start()

    def _animate_scroll_to_widget(self, widget: QWidget) -> None:
        scroll_bar = self._scroll_area.verticalScrollBar()
        viewport_height = self._scroll_area.viewport().height()
        target_center = widget.y() + widget.height() // 2
        target_value = max(0, target_center - viewport_height // 2)

        if self._scroll_animation is not None:
            self._scroll_animation.stop()

        self._scroll_animation = QPropertyAnimation(scroll_bar, b"value", self)
        self._scroll_animation.setDuration(280)
        self._scroll_animation.setStartValue(scroll_bar.value())
        self._scroll_animation.setEndValue(target_value)
        self._scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_animation.start()

    def _clear_layout(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

