from .exception import WrongOrderError
from PIL import ImageTk
from queue import Empty
from math import ceil
from tkinter import TclError

class Video():
    def __init__(self, stream, mode="w"):
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
    def play(self, frame, frame_type):
        if not self.ffmpeg.loader["loaded"]: raise WrongOrderError("Stream is not loaded.")
        self.frame=frame
        self.frame_type=frame_type
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
        self._after_id=self.frame.after(milliseconds, self._play)
    def reset(self):
        """Discard the pending frame and callback when the timeline changes."""
        self._cancel()
        if self._pending_frame is not None:
            self._pending_frame[1].close()
            self._pending_frame=None
    def _play(self):
        self._after_id=None
        if self.state=="play":
            try:
                if self._pending_frame is None:
                    self._pending_frame=self.ffmpeg._videoQ.get_nowait()
                frame=self._pending_frame
            except Empty:
                self._schedule(10)
            else:
                info=self.ffmpeg.info["streams"]["video"][self.ffmpeg.loader["video"]]
                sleep_time=1/info["fps"]
                gap=self.stopwatch.getTime()-frame[0]
                border=0.5
                if gap<float(0):
                    # Keep this frame until its presentation time. Taking
                    # another frame here would drain all prefetched video.
                    self._schedule(max(1, ceil(-gap*1000)))
                elif gap>float(border):
                    frame[1].close()
                    self._pending_frame=None
                    self._schedule(0)
                elif gap<=float(border):
                    if not self.old_frame is None:
                        self.old_frame.close()
                        self.old_frame2=self.tkimage
                    self.tkimage=ImageTk.PhotoImage(frame[1], master=self.frame)
                    if self.frame_type=="label":
                        self.frame.configure(image=self.tkimage)
                    self.old_frame=frame[1]
                    self._pending_frame=None
                    self._schedule(max(1, int(sleep_time*1000)))
        elif self.state == "pause":
            pass
        elif self.state == "stop":
            pass
    def pause(self):
        self.state = "pause"
        self._cancel()
    def resume(self):
        self.state = "play"
        self._schedule(0)
    def stop(self):
        self.state="stop"
        self.reset()
    def close(self):
        self.stop()
