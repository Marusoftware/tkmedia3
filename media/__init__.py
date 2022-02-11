from .audio import Audio
from .video import Video
from .picture import Picture
from .exception import MediaFileError
from ._ffmpeg import Stream, Filter, Util, time
from .lib import StopWatch

__version__="0.1.0"
__license__="MIT License with Marusoftware License"
__author__="Marusoftware"
__author_email__="marusoftware@outlook.jp"
__url__="https://marusoftware.net"
__all__=["Video", "Audio", "Picture", "Media", "Filter"]

class Media():
    def __init__(self, url, mode="r", **options):
        """
        Initialize media library.
        url(str or file-like object): Media file url. This will pass to ffmpeg.
        mode(str): Opening mode. You can set to 'r' or 'w'.
        **options: Options for PyAV.
        """
        self.ffmpeg=Stream(url, mode, **options)
        self.info=self.ffmpeg.info
        self.ffmpegs=self.ffmpeg.streams
        self.watch=StopWatch()
        self.status="pause"
    def Play(self, audioDevice=None, videoFrame=None, video=None, audio=None, frame_type="label"):
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
            self.video=Video(self.ffmpeg, mode="w", stopwatch=self.watch)
        if not audio is None:
            self.audio=Audio(self.ffmpeg, mode="w", stopwatch=self.watch)
        if not audio is None:
            self.audio.play(device=audioDevice)
        if not video is None:
            self.video.play(frame=videoFrame, frame_type=frame_type)
        self.watch.start()
        self.status="play"
    def Pause(self):
        """
        Pause playing.
        """
        self.ffmpeg.pause()
        try:
            self.video.pause()
        except: pass
        try:
            self.audio.pause()
        except: pass
        self.watch.stop()
        self.status="pause"
    def Seek(self, point):
        """
        Seek media.(Now NO-OP)
        """
        req_reload=not self.ffmpeg.seek(point)
        self.status="pause"
    def Close(self):
        """
        Close media.
        """
        self.Stop()
        try:
            self.audio.close()
        except: pass
        try:
            self.video.close()
        except: pass
        self.ffmpeg.CLOSE()
        self.status="close"