"""<span id="media"></span>

.. include:: ../docs/guide.md
"""

import tkinter as tk
from typing import Literal, Optional, Union
from .audio import Audio
from .video import Video
from .picture import Picture
from . import exception
from ._ffmpeg import Stream, AudioFilter, VideoFilter

__version__="0.1.2"
__license__="MIT License"
__author__="Marusoftware"
__author_email__="marusoftware@outlook.jp"
__url__="https://marusoftware.net"
__all__=["Media", "Picture", "Audio", "Video", "AudioFilter", "VideoFilter", "exception"]
__pdoc__ = {
    "subtitle": False,
    "lib": False,
    **{f"Media.{name}": False for name in ("Play", "Pause", "Resume", "Seek", "Stop", "Close")},
}

class Media():
    """Open a media source and coordinate video, audio, and subtitle playback.

    Keep the instance alive during playback and call `close()` when finished.
    Start playback with `play()` before pausing, resuming, or seeking.
    """

    def __init__(self, url:str, mode:Literal["r", "w"]="r", **options):
        """
        Open the source through PyAV.

        - `url` — A filesystem path, media URL, or binary file-like object
          accepted by `av.open`.
        - `mode` — Use `"r"` for playback. Writing support is unfinished.
        - `options` — Additional keyword arguments forwarded to `av.open`,
          such as `format` or an `options` dictionary of FFmpeg options.

        PyAV reports source opening and probing errors to the caller.
        """
        self.ffmpeg=Stream(url, mode, **options)
        #: Container metadata and per-type stream lists. Container duration is
        #: in microseconds; stream durations use each stream's time_base.
        self.info=self.ffmpeg.info
        self.ffmpegs=self.ffmpeg.streams
        #: Playback clock. Call getTime() to read the position in seconds.
        self.stopwatch=self.ffmpeg.stopwatch
        #: Last control state. End of file does not update this value.
        self.status="pause"
    def play(self, audioDevice:Optional[int]=None, videoFrame:Optional[Union[tk.Label, tk.Canvas]]=None, video:Optional[int]=None,
             audio:Optional[int]=None, frame_type:Literal["label", "canvas"]="label",
             audio_layout:Literal["mono", "stereo", "5.1", "7.1"]="stereo", *,
             video_size=None, subtitle:Optional[int]=None, subtitle_file=None):
        """
        Buffer the selected tracks and start playback.

        - **video**, **audio** — Zero-based positions within the corresponding
          `info["streams"]` lists. `None` disables that output.
        - `videoFrame` — Tkinter Label or Canvas for video output.
        - `frame_type` — `"label"` or `"canvas"`, matching the widget.
          Canvas images use the northwest anchor at (0, 0).
        - `audioDevice` — sounddevice output device index. `None` uses
          the default device. See `media.audio.getDevices`.
        - `audio_layout` — Output channel layout. The default is `"stereo"`.
          Also accepts `"mono"`, `"5.1"`, or `"7.1"`. The output device
          must support the corresponding channel count.
        - `video_size` — Positive (width, height) pixel bounds, or a callable
          returning them. Frames fit inside the bounds with their aspect
          ratio preserved. The callable runs on the decoder thread and
          must not access Tk widgets. `None` keeps the source dimensions.
        - `subtitle` — Zero-based embedded text subtitle track position.
        - `subtitle_file` — External subtitle path, such as SRT or ASS.
          Select at most one subtitle source. Subtitles require video output.

        Call on the Tkinter thread. Initial buffering blocks until frames
        are ready. Use a new instance to replay after stopping or reaching EOF.
        Invalid track positions raise `media.exception.MediaFileError`;
        conflicting subtitle sources or missing video widgets raise
        `ValueError`. Audio device failures are reported by sounddevice.
        """
        options = {}
        if subtitle is not None or subtitle_file is not None:
            if video is None or videoFrame is None:
                raise ValueError("Subtitles require a video stream and videoFrame.")
            options.update(subtitle=subtitle, subtitle_file=subtitle_file)
        if video is not None and (videoFrame is None or frame_type not in ("label", "canvas")):
            raise ValueError("Video requires a videoFrame with frame_type 'label' or 'canvas'.")
        if video_size is not None:
            options["video_size"] = video_size
            if audio is None and video is not None:
                # Keep resized frames responsive to viewport changes.
                options.update(queue_min=4, queue_max=8)
        self.ffmpeg.load(audio=audio, video=video, block=True, audio_layout=audio_layout, **options)
        if not video is None:
            self.video=Video(self.ffmpeg, mode="w")
        if not audio is None:
            self.audio=Audio(self.ffmpeg, mode="w")
        if not audio is None:
            self.audio.play(device=audioDevice)
        if not video is None:
            self.video.play(frame=videoFrame, frame_type=frame_type)
        self.play_options={"audioDevice":audioDevice, "videoFrame":videoFrame, "video":video, "audio":audio, "frame_type":frame_type, "audio_layout":audio_layout, "video_size":video_size, "subtitle":subtitle, "subtitle_file":subtitle_file}
        self.status="play"
    def pause(self):
        """
        Pause playback and keep the current image and subtitles visible.

        Requires `status == "play"`; otherwise raises
        `media.exception.WrongOrderError`.
        """
        if self.status != "play": raise exception.WrongOrderError("Media is not playing.")
        self.ffmpeg.pause()
        try:
            self.video.pause()
        except: pass
        try:
            self.audio.pause()
        except: pass
        self.status="pause"
    def resume(self):
        """
        Resume playback previously paused after `play()`.

        Requires `status == "pause"`; otherwise raises
        `media.exception.WrongOrderError`.
        """
        if self.status != "pause": raise exception.WrongOrderError("Media is not paused.")
        self.ffmpeg.resume()
        try:
            self.video.resume()
        except: pass
        try:
            self.audio.resume()
        except: pass
        self.status="play"
    def seek(self, point:float):
        """
        Seek to `point` seconds from the source's timeline origin.

        Accepts fractional seconds at runtime. Call while playing. To seek
        while paused, call `resume()` first. Seeking blocks while buffers
        are replaced and resumes playback at the target.
        """
        self.Pause()
        if hasattr(self, "video"):
            self.video.reset()
        self.ffmpeg.seek(point)
        self.Resume()
        self.status="play"
    def stop(self):
        """
        Stop decoding and playback, and clear subtitle overlays.

        Call `close()` to release the file and audio device. For replay,
        create a new instance.
        """
        self.ffmpeg.stop()
        try:
            self.video.stop()
            pass
        except: pass
        try:
            self.audio.stop()
        except: pass
        self.status="stop"
    def close(self):
        """
        Stop playback and release the container, audio output, and renderers.

        Call before destroying the Tkinter window.
        """
        if self.status !="stop": self.Stop()
        try:
            self.audio.close()
        except: pass
        try:
            self.video.close()
        except: pass
        self.ffmpeg.close()
        self.status="close"
    Play = play
    Pause = pause
    Resume = resume
    Seek = seek
    Stop = stop
    Close = close
