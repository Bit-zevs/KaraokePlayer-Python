class KaraokeError(Exception):
    """Base application error."""


class SongLoadError(KaraokeError):
    """Raised when a song cannot be loaded."""


class LyricsParseError(KaraokeError):
    """Raised when LRC lyrics cannot be parsed."""
