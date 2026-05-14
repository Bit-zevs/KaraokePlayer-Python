from __future__ import annotations

from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}


def scan_audio_files(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []

    files = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return sorted(files, key=lambda path: path.name.lower())


def scan_song_directories(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []

    directories = [path for path in folder.iterdir() if path.is_dir()]
    return sorted(directories, key=lambda path: path.name.lower())