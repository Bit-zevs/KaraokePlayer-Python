from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="karaoke-player",
        usage="python -m karaoke_player [пути ...] [--debug]",
        description="Настольный караоке-плеер с синхронизированным LRC-текстом.",
        add_help=False,
    )
    parser._positionals.title = "Позиционные аргументы"
    parser._optionals.title = "Опции"

    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Папка библиотеки, папки песен или отдельные аудиофайлы. "
            "Если ничего не указано, используется папка ./songs в корне проекта."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить подробное логирование.",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Показать эту справку и выйти.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def default_songs_dir() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "songs"


def normalize_input_paths(raw_paths: list[str]) -> tuple[Path | None, list[Path]]:
    if not raw_paths:
        return default_songs_dir(), []

    paths = [Path(value).expanduser().resolve() for value in raw_paths]

    if len(paths) == 1 and paths[0].is_dir():
        return paths[0], []

    return None, paths
