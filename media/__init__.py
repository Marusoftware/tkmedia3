from typing import Literal
from .audio import Audio
from .video import Video
from .picture import Picture
from .exception import MediaFileError, ModeError, WrongOrderError
from ._ffmpeg import Stream, AudioFilter, VideoFilter
from .lib import StopWatch

__version__="0.1.2"
__license__="MIT License"
__author__="Marusoftware"
__author_email__="marusoftware@outlook.jp"
__url__="https://marusoftware.net"
__all__=["Video", "Audio", "Picture", "Media", "Filter"]

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
    def Play(self, audioDevice:int=None, videoFrame:int=None, video:int=None, audio:int=None, frame_type:Literal["label", "canvas"]="label"):
        """
        Play media.
        audioDevice(int): An number of Device(You can get with media.audio.getDevices func)
        videoFrame(tkinter.Label or tkinter.Canvas): An frame to playing video
        frame_type(str): videoFrame type(Label->label, Canvas->canvas)
        video(int): video stream number
        audio(int): audio stream number
        """
        self.ffmpeg.load(audio=audio, video=video, wait=True)
        if not video is None:
            self.video=Video(self.ffmpeg, mode="w")
        if not audio is None:
            self.audio=Audio(self.ffmpeg, mode="w")
        if not audio is None:
            self.audio.play(device=audioDevice)
        if not video is None:
            self.video.play(frame=videoFrame, frame_type=frame_type)
        self.play_options={"audioDevice":audioDevice, "videoFrame":videoFrame, "video":video, "audio":audio, "frame_type":frame_type}
        self.status="play"
    def Pause(self):
        """
        Pause playing.
        """
        if self.status != "play": raise WrongOrderError("Media is not playing.")
        self.ffmpeg.pause()
        try:
            self.video.pause()
        except: pass
        try:
            self.audio.pause()
        except: pass
        self.status="pause"
    def Resume(self):
        """
        Resume playing.
        """
        if self.status != "pause": raise WrongOrderError("Media is not paused.")
        self.ffmpeg.resume()
        try:
            self.video.resume()
        except: pass
        try:
            self.audio.resume()
        except: pass
        self.status="play"
    def Seek(self, point:int):
        """
        Seek media.
        point(int): time/s to seek
        """
        self.Pause()
        self.ffmpeg.seek(point)
        self.Resume()
        self.status="play"
    def Stop(self):
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
    def Close(self):
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