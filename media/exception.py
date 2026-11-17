"""Exceptions raised for unsupported sources and playback control order."""

class MediaFileError(Exception):
    """A selected track is unavailable or its subtitle format is unsupported."""
    pass

class WrongOrderError(Exception):
    """A playback control was called in an invalid state."""
    pass

class ModeError(Exception):
    """An unsupported input/output mode or operation was requested."""
    pass