from typing import Literal, Optional
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
__all__=["Video", "Audio", "Picture", "Media", "AudioFilter", "VideoFilter", "exception"]

class Media():
    def __init__(self, url:str, mode:Literal["r", "w"]="r", **options):
        """
        Initialize media library.
        url(str or file-like object): Media file url. This will pass to ffmpeg.
        mode(str): Opening mode. You can set to 'r' or 'w'.
        **options: Options for PyAV.
        """
        self.ffmpeg=Stream(url, mode, **options)
        self.info=self.ffmpeg.info
        self.ffmpegs=self.ffmpeg.streams
        self.stopwatch=self.ffmpeg.stopwatch
        self.status="pause"
    def play(self, audioDevice:Optional[int]=None, videoFrame:Optional[int]=None, video:Optional[int]=None,
             audio:Optional[int]=None, frame_type:Literal["label", "canvas"]="label",
             audio_layout:Literal["mono", "stereo", "5.1", "7.1"]="stereo", *,
             video_size=None, subtitle:Optional[int]=None, subtitle_file=None):
        """
        Play media.
        audioDevice(int): An number of Device(You can get with media.audio.getDevices func)
        videoFrame(tkinter.Label or tkinter.Canvas): An frame to playing video
        frame_type(str): videoFrame type(Label->label, Canvas->canvas)
        video(int): video stream number
        audio(int): audio stream number
        audio_layout(str): Output channel layout, e.g. 'mono', 'stereo', or '5.1'.
        video_size: Optional (width, height) in pixels or a callable returning
            the current bounds. The callable runs on the decoder thread and
            must not access Tk widgets. The image fits inside the bounds.
        subtitle(int): Zero-based index of an embedded text subtitle track.
        subtitle_file: Path to an external text subtitle file, such as SRT.
            Select at most one subtitle source. Subtitles require video output.
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
        Pause playing.
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
        Resume playing.
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
    def seek(self, point:int):
        """
        Seek media.
        point(int): time/s to seek
        """
        self.Pause()
        if hasattr(self, "video"):
            self.video.reset()
        self.ffmpeg.seek(point)
        self.Resume()
        self.status="play"
    def stop(self):
        """
        Stop media.
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
        Close media.
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
