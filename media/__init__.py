from . import video, audio, picture, exception
from ._ffmpeg import FFMPEG, Filter, Util, time
from .lib import StopWatch

__version__="0.0.3"
__license__="GPL v2"
__author__="Marusoftware"
__author_email__="marusoftware@outlook.jp"
__url__="https://marusoftware.net"

Video = video.Video
Audio = audio.Audio
Picture = picture.Picture
MediaFileError=exception.MediaFileError

class Media():
    def __init__(self, url, mode="r", avformat=None):
        self.stream = FFMPEG()
        self.stream.OPEN(url, mode, avformat)
        self.info=self.stream.info
        self.streams=self.stream.streams
    def Play(self, audioDevice=None, videoFrame=None, video=None, audio=None):
        args={}
        if not video is None:
            self.video=Video(self.stream)
        if not audio is None:
            self.audio=Audio(self.stream, mode="w")
            args.update(AchBrkSCB=self.audio._play_AchBrkSCB)
        self.stream.LOAD(audio=audio, video=video, block=False, Acallback=Util.toSdArray, Vcallback=Util.toImage, **args)
        while not self.stream.loaded:
            time.sleep(1/1000)
        if not audio is None:
            self.audio.play()
        if not video is None:
            self.video.play(videoFrame, frame_type="label")
        