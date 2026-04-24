from pathlib import Path

from karaoke_player.services.song_loader import SongLoader


def test_load_song_with_matching_lrc(tmp_path: Path) -> None:
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio")
    lyrics = tmp_path / "track.lrc"
    lyrics.write_text("[00:01.00]Hello", encoding="utf-8")

    song = SongLoader().load_song(audio)

    assert song.title == "track"
    assert song.lyrics_path == lyrics
    assert len(song.lyrics) == 1
    assert song.lyrics[0].text == "Hello"


def test_load_folder_returns_supported_audio_files(tmp_path: Path) -> None:
    (tmp_path / "a.mp3").write_bytes(b"a")
    (tmp_path / "b.wav").write_bytes(b"b")
    (tmp_path / "note.txt").write_text("ignore", encoding="utf-8")

    songs = SongLoader().load_folder(tmp_path)

    assert [song.title for song in songs] == ["a", "b"]
