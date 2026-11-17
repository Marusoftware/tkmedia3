"""Lower-level video output for an already loaded stream.

Applications normally use `media.Media.play` to construct this renderer.
"""

from .exception import WrongOrderError
from PIL import ImageTk
from queue import Empty
from math import ceil
from tkinter import TclError
from ._ass import AssOverlay
from .picture import _set_widget_image
from .subtitle import SubtitleOverlay

class Video():
    """Present buffered video frames using the shared playback clock.

    Use `media.Media` for source loading and coordinated playback.
    """
    def __init__(self, stream, mode="w"):
        """Attach to a loaded stream and its playback clock.

        `stream` is the internal stream owned by a Media instance. The supported
        output mode is `"w"`.
        """
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.stopwatch=self.ffmpeg.stopwatch
        self.state="stop"
        self.old_frame=None
        self.old_frame2=None
        self.tkimage=None
        self._pending_frame=None
        self._after_id=None
        self._canvas_item = None
        self._subtitles = None
        self._ass = None
    def play(self, frame, frame_type):
        """Schedule drawing in `frame`, a Tkinter Label or Canvas.

        `frame_type` is `"label"` or `"canvas"`. The stream must already
        be loaded. Call on the Tkinter thread and run its main loop.
        """
        if not self.ffmpeg.loader["loaded"]: raise WrongOrderError("Stream is not loaded.")
        if frame_type not in ("label", "canvas"):
            raise ValueError("frame_type must be 'label' or 'canvas'")
        if self.played:
            self.close()
        self.frame=frame
        self.frame_type=frame_type
        subtitle_queue = getattr(self.ffmpeg, "_subtitleQ", None)
        if subtitle_queue is not None:
            if self.ffmpeg._ass_header is not None:
                self._ass = AssOverlay(self.ffmpeg._ass_header, subtitle_queue)
            else:
                self._subtitles = SubtitleOverlay(frame, subtitle_queue)
        self.state="play"
        self._schedule(0)
        self.played=True
    def _cancel(self):
        if self._after_id is not None:
            try:
                self.frame.after_cancel(self._after_id)
            except TclError:
                pass  # The widget may already have been destroyed.
            self._after_id=None
    def _schedule(self, milliseconds):
        self._cancel()
        if self._subtitles is not None or self._ass is not None:
            milliseconds = min(milliseconds, 20)
        self._after_id=self.frame.after(milliseconds, self._play)
    def reset(self):
        """Discard the pending frame and callback when the timeline changes."""
        self._cancel()
        if self._subtitles is not None:
            self._subtitles.reset()
        if self._ass is not None:
            had_overlay = self._ass.image is not None
            self._ass.reset()
            if had_overlay and self.old_frame is not None:
                try:
                    self._draw_frame(self.old_frame)
                except TclError:
                    pass  # The widget may already have been destroyed.
        if self._pending_frame is not None:
            self._pending_frame[1].close()
            self._pending_frame=None

    def _draw_frame(self, image):
        self.old_frame2 = self.tkimage
        overlay = self._ass.image if self._ass is not None else None
        if overlay is not None:
            with image.copy() as composed:
                composed.paste(overlay, mask=overlay.getchannel("A"))
                self.tkimage = ImageTk.PhotoImage(composed, master=self.frame)
        else:
            self.tkimage = ImageTk.PhotoImage(image, master=self.frame)
        self._canvas_item = _set_widget_image(
            self.frame, self.frame_type, self.tkimage, self._canvas_item)

    def _refresh_ass(self):
        if self._ass is not None and self.old_frame is not None:
            if self._ass.update(self.stopwatch.getTime(), self.old_frame.size):
                self._draw_frame(self.old_frame)

    def _play(self):
        self._after_id=None
        if self.state=="play":
            try:
                if self._subtitles is not None:
                    self._subtitles.update(self.stopwatch.getTime())
                while True:
                    if self._pending_frame is None:
                        self._pending_frame=self.ffmpeg._videoQ.get_nowait()
                    frame=self._pending_frame
                    gap=self.stopwatch.getTime()-frame[0]
                    if gap <= 0.5:
                        break
                    # Drain stale queued frames in this callback rather than
                    # scheduling a separate Tk callback for every discarded image.
                    frame[1].close()
                    self._pending_frame=None
            except Empty:
                self._refresh_ass()
                self._schedule(10)
            else:
                info=self.ffmpeg.info["streams"]["video"][self.ffmpeg.loader["video"]]
                sleep_time=1/info["fps"]
                if gap<float(0):
                    # Keep this frame until its presentation time. Taking
                    # another frame here would drain all prefetched video.
                    self._refresh_ass()
                    self._schedule(max(1, ceil(-gap*1000)))
                else:
                    if not self.old_frame is None:
                        self.old_frame.close()
                    if self._ass is not None:
                        self._ass.update(self.stopwatch.getTime(), frame[1].size)
                    self._draw_frame(frame[1])
                    self.old_frame=frame[1]
                    self._pending_frame=None
                    # Schedule against the media clock, so delayed callbacks
                    # catch up instead of adding another frame interval.
                    remaining = frame[0] + sleep_time - self.stopwatch.getTime()
                    self._schedule(max(1, int(remaining * 1000)))
    def pause(self):
        """Cancel scheduled drawing while retaining the current image."""
        self.state = "pause"
        self._cancel()
    def resume(self):
        """Schedule drawing again using the shared playback clock."""
        self.state = "play"
        self._schedule(0)
    def stop(self):
        """Cancel drawing and discard the pending frame and subtitles."""
        self.state="stop"
        self.reset()
    def close(self):
        """Stop drawing and release subtitle renderers and the Canvas item."""
        self.stop()
        if self._ass is not None:
            self._ass.close()
            self._ass = None
        if self._subtitles is not None:
            self._subtitles.close()
            self._subtitles = None
        if self._canvas_item is not None:
            try:
                self.frame.delete(self._canvas_item)
            except TclError:
                pass
            self._canvas_item = None
