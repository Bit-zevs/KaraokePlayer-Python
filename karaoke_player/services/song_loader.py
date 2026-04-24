from __future__ import annotations

from pathlib import Path

from karaoke_player.core.errors import SongLoadError
from karaoke_player.core.models import Song
from karaoke_player.infra.file_scanner import (
    AUDIO_EXTENSIONS,
    scan_audio_files,
    scan_song_directories,
)
from karaoke_player.infra.lrc_parser import parse_lrc_file


class SongLoader:
    def load_song(self, audio_path: Path, title: str | None = None) -> Song:
        if not audio_path.exists() or not audio_path.is_file():
            raise SongLoadError(f"Аудиофайл не найден: {audio_path}")
        if audio_path.suffix.lower() not in AUDIO_EXTENSIONS:
            raise SongLoadError(f"Неподдерживаемый формат аудио: {audio_path.suffix}")

        lyrics_path = audio_path.with_suffix(".lrc")
        lyrics = []
        if lyrics_path.exists():
            lyrics = parse_lrc_file(lyrics_path)
        else:
            lyrics_path = None

        return Song(
            title=title or audio_path.stem,
            audio_path=audio_path,
            lyrics_path=lyrics_path,
            lyrics=lyrics,
        )

    def load_song_directory(self, song_dir: Path) -> Song:
        if not song_dir.exists() or not song_dir.is_dir():
            raise SongLoadError(f"Папка песни не найдена: {song_dir}")

        audio_files = scan_audio_files(song_dir)
        if not audio_files:
            raise SongLoadError(f"В папке '{song_dir.name}' нет поддерживаемых аудиофайлов.")
        if len(audio_files) > 1:
            raise SongLoadError(
                f"Папка песни '{song_dir.name}' должна содержать ровно один аудиофайл."
            )

        audio_path = audio_files[0]

        lyrics_path = audio_path.with_suffix(".lrc")
        if not lyrics_path.exists():
            lrc_files = sorted(song_dir.glob("*.lrc"), key=lambda path: path.name.lower())
            lyrics_path = lrc_files[0] if lrc_files else None

        lyrics = parse_lrc_file(lyrics_path) if lyrics_path is not None else []

        return Song(
            title=song_dir.name,
            audio_path=audio_path,
            lyrics_path=lyrics_path,
            lyrics=lyrics,
        )

    def load_folder(self, folder: Path) -> list[Song]:
        if not folder.exists() or not folder.is_dir():
            raise SongLoadError(f"Папка не найдена: {folder}")

        songs: list[Song] = []

        song_directories = scan_song_directories(folder)
        if song_directories:
            for song_dir in song_directories:
                try:
                    songs.append(self.load_song_directory(song_dir))
                except SongLoadError:
                    continue
        else:
            for audio_path in scan_audio_files(folder):
                try:
                    songs.append(self.load_song(audio_path))
                except SongLoadError:
                    continue

        if not songs:
            raise SongLoadError(
                "Песни не найдены. Используйте папку с подпапками песен или аудиофайлами."
            )

        return songs

    def load_paths(self, paths: list[Path]) -> list[Song]:
        songs = [self.load_song(path) for path in paths]
        if not songs:
            raise SongLoadError("Не выбрано ни одной песни.")
        return songs
