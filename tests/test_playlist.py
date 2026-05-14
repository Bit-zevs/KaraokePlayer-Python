from pathlib import Path

from karaoke_player.core.models import Song
from karaoke_player.core.playlist import PlaylistManager


def _song(name: str) -> Song:
    return Song(title=name, audio_path=Path(f"{name}.mp3"))


def test_playlist_navigation() -> None:
    playlist = PlaylistManager()
    playlist.set_songs([_song("one"), _song("two"), _song("three")])

    assert playlist.current().title == "one"
    assert playlist.next().title == "two"
    assert playlist.previous().title == "one"
    assert playlist.select(2).title == "three"
    assert playlist.next() is None
