from . import video, audio, picture, exception
from ._ffmpeg import FFMPEG, Filter, Util, time
from .lib import StopWatch

__version__="0.1.0"
__license__="MIT License with Marusoftware License"
__author__="Marusoftware"
__author_email__="marusoftware@outlook.jp"
__url__="https://marusoftware.net"
__all__=["Video","Audio","Picture","Media", "Filter"]

Video = video.Video
Audio = audio.Audio
Picture = picture.Picture
MediaFileError=exception.MediaFileError

class Media():
    def __init__(self, url, mode="r", **options):
        """
        Initialize media library.
        url(str or file-like object): Media file url. This will pass to ffmpeg.
        mode(str): Opening mode. You can set to 'r' or 'w'.
        **options: Options for PyAV.
        """
        self.stream = FFMPEG()
        self.stream.OPEN(url, mode, **options)
        self.info=self.stream.info
        self.streams=self.stream.streams
        self.watch = StopWatch()
        self.status={"status":"pause"}
    def Play(self, audioDevice=None, videoFrame=None, video=None, audio=None):
        """
        Play media.
        audioDevice(int): An number of Device(You can get with media.audio.getDevices func)
        videoFrame(tkinter.Frame): An frame to playing video
        video(int): video stream number
        audio(int): audio stream number
        """
        if not video is None:
            self.video=Video(self.stream, mode="w", stopwatch=self.watch)
        if not audio is None:
            self.audio=Audio(self.stream, mode="w", stopwatch=self.watch)
        self.stream.LOAD(audio=audio, video=video, block=False, Acallback=Util.toSdArray, Vcallback=Util.toImage)
        while not self.stream.loaded:
            time.sleep(1/1000)
        if not audio is None:
            self.audio.play(device=audioDevice)
        if not video is None:
            self.video.play(frame=videoFrame, frame_type="label")
        self.watch.start()
        self.status={"status":"playing"}
    def Pause(self):
        """
        Pause playing.
        """
        try:
            self.video.pause()
        except: pass
        try:
            self.audio.pause()
        except: pass
        self.watch.stop()
        self.status={"status":"pause"}
    def Seek(self):
        """
        Seek media.(Now NO-OP)
        """
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
        self.stream.CLOSE()
        self.status={"status":"close"}