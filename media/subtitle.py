import re
from heapq import heappop, heappush
from os import fspath
from queue import Empty
from tkinter import Label, TclError

import av
from av.codec.codec import Properties
from av.subtitles.subtitle import AssSubtitle

from ._ass import styled_header
from .exception import MediaFileError


_ASS_COMMAND = re.compile(r"\{\\[^}]*\}")


def validate_text_stream(stream):
    codec = stream.codec_context.codec
    if not codec.properties & Properties.TEXT_SUB.value:
        raise MediaFileError(f"Subtitle codec '{codec.name}' is not a text subtitle codec.")


def decode_cues(packet, styled=False):
    if packet.pts is None or (packet.duration or 0) <= 0:
        return
    start = float(packet.pts * packet.time_base)
    end = float((packet.pts + packet.duration) * packet.time_base)
    for subtitle in packet.decode():
        if isinstance(subtitle, AssSubtitle):
            if styled:
                if subtitle.ass:
                    yield start, end, subtitle.ass
                continue
            # PyAV 15.0's dialogue accessor fails on some UTF-8 bytes.
            # FFmpeg's ASS events have eight fields before the dialogue text.
            raw_text = subtitle.text or subtitle.ass.split(b",", 8)[-1]
            text = raw_text.decode("utf-8", errors="replace")
            text = _ASS_COMMAND.sub("", text)
            text = text.replace(r"\N", "\n").replace(r"\n", "\n").replace(r"\h", "\u00a0")
            if text.strip():
                yield start, end, text


def read_subtitle_file(path):
    with av.open(fspath(path)) as container:
        if not container.streams.subtitles:
            raise MediaFileError("The subtitle file contains no subtitle stream.")
        stream = container.streams.subtitles[0]
        validate_text_stream(stream)
        header = styled_header(stream)
        cues = [cue for packet in container.demux(stream) for cue in decode_cues(packet, bool(header))]
        return header, cues


class SubtitleOverlay:
    def __init__(self, frame, queue):
        self._queue = queue
        self._pending = []
        self._active = []
        self._text = ""
        self._wraplength = None
        self._label = Label(frame, background="black", foreground="white", justify="center")

    def update(self, now):
        while True:
            try:
                heappush(self._pending, self._queue.get_nowait())
            except Empty:
                break
        self._active = [cue for cue in self._active if cue[1] > now]
        while self._pending and self._pending[0][0] <= now:
            cue = heappop(self._pending)
            if cue[1] > now:
                self._active.append(cue)
        self._show("\n".join(cue[2] for cue in self._active))

    def _show(self, text):
        if text:
            wraplength = max(1, self._label.master.winfo_width() - 12)
            if wraplength != self._wraplength or text != self._text:
                self._label.configure(text=text, wraplength=wraplength)
                self._wraplength = wraplength
        if text != self._text:
            if text:
                self._label.place(relx=0.5, rely=1, y=-4, anchor="s")
            else:
                try:
                    self._label.place_forget()
                except TclError:
                    pass  # The parent widget may already have been destroyed.
            self._text = text

    def reset(self):
        self._pending.clear()
        self._active.clear()
        self._show("")

    def close(self):
        try:
            self._label.destroy()
        except TclError:
            pass  # The parent widget may already have been destroyed.
