"""Render ASS/SSA subtitle events with the optional system libass library."""

import ctypes as c
from ctypes.util import find_library
from functools import lru_cache
from queue import Empty
from sys import platform

from PIL import Image


class _AssImage(c.Structure):
    pass


_AssImagePointer = c.POINTER(_AssImage)
_AssImage._fields_ = [
    ("width", c.c_int), ("height", c.c_int), ("stride", c.c_int),
    ("bitmap", c.c_void_p), ("color", c.c_uint32),
    ("x", c.c_int), ("y", c.c_int), ("next", _AssImagePointer),
]


@lru_cache(maxsize=1)
def ass_library():
    handle, number, string = c.c_void_p, c.c_int, c.c_char_p
    names = (find_library("ass"),)
    if platform == "win32":
        names += ("libass-9.dll", "libass.dll")
    for name in names:
        if name:
            try:
                lib = c.CDLL(name)
                break
            except OSError:
                continue
    else:
        return None
    signatures = {
        "ass_library_init": (handle,),
        "ass_library_done": (None, handle),
        "ass_renderer_init": (handle, handle),
        "ass_renderer_done": (None, handle),
        "ass_set_frame_size": (None, handle, number, number),
        "ass_set_fonts": (None, handle, string, string, number, string, number),
        "ass_new_track": (handle, handle),
        "ass_free_track": (None, handle),
        "ass_process_codec_private": (None, handle, string, number),
        "ass_process_chunk": (None, handle, string, number, c.c_longlong, c.c_longlong),
        "ass_flush_events": (None, handle),
        "ass_render_frame": (_AssImagePointer, handle, handle, c.c_longlong, c.POINTER(number)),
    }
    for symbol, (result, *args) in signatures.items():
        fn = getattr(lib, symbol, None)
        if fn is None:
            return None
        fn.restype, fn.argtypes = result, args
    return lib


def styled_header(stream):
    codec = stream.codec_context
    if codec.name in ("ass", "ssa") and codec.extradata and ass_library() is not None:
        return codec.extradata
    return None


class AssOverlay:
    def __init__(self, header, queue):
        self._queue = queue
        self._lib = ass_library()
        self._library = self._lib.ass_library_init()
        self._renderer = None
        self._track = None
        self._size = None
        self.image = None
        try:
            if not self._library:
                raise RuntimeError("Could not initialize libass.")
            self._renderer = self._lib.ass_renderer_init(self._library)
            self._track = self._lib.ass_new_track(self._library)
            if not self._renderer or not self._track:
                raise RuntimeError("Could not allocate the ASS renderer or track.")
            self._lib.ass_set_fonts(self._renderer, None, b"sans-serif", 1, None, 1)
            self._lib.ass_process_codec_private(self._track, header, len(header))
        except Exception:
            self.close()
            raise

    def update(self, now, size):
        while True:
            try:
                start, end, event = self._queue.get_nowait()
            except Empty:
                break
            start_ms = round(start * 1000)
            duration_ms = round(end * 1000) - start_ms
            self._lib.ass_process_chunk(self._track, event, len(event), start_ms, duration_ms)

        resized = self._size != size
        if resized:
            self._lib.ass_set_frame_size(self._renderer, *size)
            self._size = size
        changed = c.c_int()
        layer = self._lib.ass_render_frame(self._renderer, self._track, round(now * 1000), c.byref(changed))
        if not resized and not changed.value:
            return False
        self.image = None
        while layer:
            bitmap = layer.contents
            if bitmap.width and bitmap.height:
                if self.image is None:
                    self.image = Image.new("RGBA", size)
                self.image.alpha_composite(_tile(bitmap), (bitmap.x, bitmap.y))
            layer = bitmap.next
        return True

    def reset(self):
        self._lib.ass_flush_events(self._track)
        self.image = None
        # A seek can reinsert the same event at the same time. libass may
        # report unchanged layers even though the composited image was cleared.
        self._size = None

    def close(self):
        self.image = None
        if self._track:
            self._lib.ass_free_track(self._track)
            self._track = None
        if self._renderer:
            self._lib.ass_renderer_done(self._renderer)
            self._renderer = None
        if self._library:
            self._lib.ass_library_done(self._library)
            self._library = None


def _tile(layer):
    # The last row is only guaranteed to hold its visible pixels.
    length = layer.stride * (layer.height - 1) + layer.width
    data = c.string_at(layer.bitmap, length)
    size = (layer.width, layer.height)
    alpha = Image.frombytes("L", size, data, "raw", "L", layer.stride, 1)
    red, green, blue, transparency = layer.color.to_bytes(4, "big")
    tile = Image.new("RGBA", size, (red, green, blue))
    tile.putalpha(alpha.point(lambda coverage: coverage * (255 - transparency) // 255))
    return tile
