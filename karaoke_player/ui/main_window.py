from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from karaoke_player.app.controller import AppController
from karaoke_player.core.models import Song
from karaoke_player.infra.config_store import ConfigStore
from karaoke_player.ui.lyrics_view import LyricsView
from karaoke_player.ui.player_panel import PlayerPanel


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController, config_store: ConfigStore) -> None:
        super().__init__()
        self.controller = controller
        self.config_store = config_store
        self.config = self.config_store.load()

        self.setWindowTitle("Karaoke Player")
        self.resize(1200, 760)

        self.playlist_widget = QListWidget()
        self.song_title_label = QLabel("Open a folder or audio file")
        self.song_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_title_label.setWordWrap(True)

        self.song_meta_label = QLabel("Your synced lyrics will appear here")
        self.song_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lyrics_view = LyricsView()
        self.player_panel = PlayerPanel()

        self._build_ui()
        self._build_menu()
        self._bind_events()
        self._setup_shortcuts()
        self._apply_theme()

    def _build_ui(self) -> None:
        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(18, 18, 18, 18)
        outer_layout.setSpacing(14)

        playlist_card = QFrame()
        playlist_card.setObjectName("sidebarCard")
        playlist_layout = QVBoxLayout(playlist_card)
        playlist_layout.setContentsMargins(16, 16, 16, 16)
        playlist_layout.setSpacing(12)

        playlist_title = QLabel("Playlist")
        playlist_title.setObjectName("sectionTitle")
        playlist_hint = QLabel("Pick a song and sing along")
        playlist_hint.setObjectName("sectionHint")

        self.playlist_widget.setObjectName("playlistWidget")
        self.playlist_widget.setSpacing(8)
        self.playlist_widget.setAlternatingRowColors(False)
        self.playlist_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.playlist_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        playlist_layout.addWidget(playlist_title)
        playlist_layout.addWidget(playlist_hint)
        playlist_layout.addWidget(self.playlist_widget, stretch=1)

        header_card = QFrame()
        header_card.setObjectName("headerCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(6)

        now_playing_label = QLabel("Now playing")
        now_playing_label.setObjectName("sectionHint")
        self.song_title_label.setObjectName("songTitleLabel")
        self.song_meta_label.setObjectName("songMetaLabel")

        header_layout.addWidget(now_playing_label)
        header_layout.addWidget(self.song_title_label)
        header_layout.addWidget(self.song_meta_label)

        lyrics_card = QFrame()
        lyrics_card.setObjectName("lyricsCard")
        lyrics_layout = QVBoxLayout(lyrics_card)
        lyrics_layout.setContentsMargins(0, 0, 0, 0)
        lyrics_layout.addWidget(self.lyrics_view)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)
        right_layout.addWidget(header_card)
        right_layout.addWidget(lyrics_card, stretch=1)
        right_layout.addWidget(self.player_panel)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        splitter.addWidget(playlist_card)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 860])

        outer_layout.addWidget(splitter)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        open_folder_action = QAction("Open folder", self)
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        open_files_action = QAction("Open files", self)
        open_files_action.triggered.connect(self.open_files)
        file_menu.addAction(open_files_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _bind_events(self) -> None:
        self.playlist_widget.currentRowChanged.connect(self._on_playlist_row_changed)

        self.player_panel.play_pause_clicked.connect(self.controller.toggle_play_pause)
        self.player_panel.stop_clicked.connect(self.controller.stop)
        self.player_panel.previous_clicked.connect(self.controller.play_previous)
        self.player_panel.next_clicked.connect(self.controller.play_next)
        self.player_panel.seek_requested.connect(self.controller.seek)

        self.controller.playlist_changed.connect(self._update_playlist)
        self.controller.song_changed.connect(self._update_song)
        self.controller.position_changed.connect(self.player_panel.set_position)
        self.controller.duration_changed.connect(self.player_panel.set_duration)
        self.controller.playback_state_changed.connect(self.player_panel.set_playback_state)
        self.controller.active_lyric_changed.connect(self.lyrics_view.set_active_index)
        self.controller.error_occurred.connect(self._show_error)
        self.controller.info_message.connect(self.statusBar().showMessage)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Space"), self, activated=self.controller.toggle_play_pause)
        QShortcut(
            QKeySequence(Qt.Key.Key_Right),
            self,
            activated=lambda: self.controller.seek(self.player_panel.position_slider.value() + 5000),
        )
        QShortcut(
            QKeySequence(Qt.Key.Key_Left),
            self,
            activated=lambda: self.controller.seek(self.player_panel.position_slider.value() - 5000),
        )

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #0B1120;
                color: #E5E7EB;
            }
            QMenuBar {
                background: #0F172A;
                color: #E5E7EB;
                border-bottom: 1px solid #1E293B;
            }
            QMenuBar::item {
                padding: 8px 12px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #172036;
                border-radius: 8px;
            }
            QMenu {
                background: #111827;
                color: #E5E7EB;
                border: 1px solid #1F2937;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 18px;
                border-radius: 8px;
            }
            QMenu::item:selected {
                background: #1E293B;
            }
            QStatusBar {
                background: #0F172A;
                color: #CBD5E1;
                border-top: 1px solid #1E293B;
            }
            QSplitter::handle {
                background: transparent;
            }
            QFrame#sidebarCard, QFrame#headerCard, QFrame#lyricsCard, QFrame#playerPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111827, stop:1 #0F172A);
                border: 1px solid #1E293B;
                border-radius: 22px;
            }
            QLabel#sectionTitle {
                font-size: 22px;
                font-weight: 700;
                color: #F8FAFC;
            }
            QLabel#sectionHint {
                font-size: 13px;
                color: #94A3B8;
            }
            QLabel#songTitleLabel {
                font-size: 30px;
                font-weight: 800;
                color: #F8FAFC;
            }
            QLabel#songMetaLabel {
                font-size: 14px;
                color: #A5B4FC;
            }
            QListWidget#playlistWidget {
                background: transparent;
                border: none;
                outline: 0;
                padding-right: 4px;
            }
            QListWidget#playlistWidget::item {
                background: #111827;
                border: 1px solid #1F2937;
                border-radius: 14px;
                padding: 14px 16px;
                margin: 2px 0;
                color: #D6DCE8;
            }
            QListWidget#playlistWidget::item:selected {
                background: #1D2942;
                border: 1px solid #7C3AED;
                color: #FFFFFF;
            }
            QListWidget#playlistWidget::item:hover {
                background: #172036;
            }
            QPushButton#playerButton {
                background: #172036;
                border: 1px solid #23304A;
                border-radius: 21px;
                color: #F8FAFC;
                font-size: 18px;
                font-weight: 700;
            }
            QPushButton#playerButton:hover {
                background: #1F2A44;
                border: 1px solid #7C3AED;
            }
            QPushButton#playerButton:pressed {
                background: #283757;
            }
            QLabel#timeValue {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#timeValueMuted {
                color: #94A3B8;
                font-size: 14px;
                font-weight: 600;
            }
            QSlider#positionSlider::groove:horizontal {
                background: #1F2937;
                height: 8px;
                border-radius: 4px;
            }
            QSlider#positionSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C3AED, stop:1 #A855F7);
                border-radius: 4px;
            }
            QSlider#positionSlider::handle:horizontal {
                background: #F8FAFC;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 6px 0 6px 0;
            }
            QScrollBar::handle:vertical {
                background: #273449;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #334155;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                border: none;
                height: 0;
            }
            QMessageBox {
                background: #111827;
            }
            """
        )

    def open_folder(self) -> None:
        start_dir = self.config.get("last_folder", str(Path.home()))
        folder = QFileDialog.getExistingDirectory(self, "Open folder", start_dir)
        if not folder:
            return
        self.config["last_folder"] = folder
        self.config_store.save(self.config)
        self.controller.load_folder(Path(folder))

    def open_files(self) -> None:
        start_dir = self.config.get("last_folder", str(Path.home()))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open audio files",
            start_dir,
            "Audio files (*.mp3 *.wav *.ogg *.flac *.m4a)",
        )
        if not files:
            return
        self.config["last_folder"] = str(Path(files[0]).parent)
        self.config_store.save(self.config)
        self.controller.load_files([Path(file) for file in files])

    def _update_playlist(self, titles: list[str], current_index: int) -> None:
        self.playlist_widget.blockSignals(True)
        self.playlist_widget.clear()
        for title in titles:
            item = QListWidgetItem(title)
            self.playlist_widget.addItem(item)
        if 0 <= current_index < len(titles):
            self.playlist_widget.setCurrentRow(current_index)
        self.playlist_widget.blockSignals(False)
        self.song_meta_label.setText(f"{len(titles)} song{'s' if len(titles) != 1 else ''} loaded")

    def _update_song(self, song: Song) -> None:
        self.song_title_label.setText(song.display_name)
        self.song_meta_label.setText("Synchronized lyrics ready" if song.lyrics else "Audio loaded without synced lyrics")
        self.lyrics_view.set_lyrics(song.lyrics)
        self.statusBar().showMessage(f"Loaded: {song.display_name}", 3000)

    def _on_playlist_row_changed(self, index: int) -> None:
        if index >= 0:
            self.controller.select_song(index, autoplay=True)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)
        self.statusBar().showMessage(message, 5000)
