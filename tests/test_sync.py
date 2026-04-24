from karaoke_player.core.models import LyricLine
from karaoke_player.core.sync import LyricsSynchronizer


def test_active_index_changes_with_position() -> None:
    sync = LyricsSynchronizer(
        [
            LyricLine(1000, "first"),
            LyricLine(3000, "second"),
            LyricLine(5000, "third"),
        ]
    )

    assert sync.active_index(0) == -1
    assert sync.active_index(1000) == 0
    assert sync.active_index(2500) == 0
    assert sync.active_index(3000) == 1
    assert sync.active_index(9999) == 2
