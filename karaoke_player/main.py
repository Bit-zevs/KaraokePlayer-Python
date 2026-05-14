from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from karaoke_player.app.controller import AppController
from karaoke_player.cli import normalize_input_paths, parse_args
from karaoke_player.infra.config_store import ConfigStore
from karaoke_player.infra.logging_setup import configure_logging
from karaoke_player.services.media_player import QtMediaPlayerAdapter
from karaoke_player.services.song_loader import SongLoader
from karaoke_player.ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(debug=args.debug)

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setStyle("Fusion")

    loader = SongLoader()
    player = QtMediaPlayerAdapter()
    controller = AppController(loader, player)
    window = MainWindow(controller, ConfigStore())
    window.show()

    folder, files = normalize_input_paths(args.paths)
    if folder is not None:
        controller.load_folder(folder)
    elif files:
        controller.load_files(files)

    return app.exec()
