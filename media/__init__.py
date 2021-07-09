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
        self.watch = StopWatch()
    def Play(self, audioDevice=None, videoFrame=None, video=None, audio=None):
        args={}
        if not video is None:
            #self.streams.video[video].thread_type="AUTO"
            self.video=Video(self.stream)
        if not audio is None:
            #self.streams.audio[audio].thread_type="AUTO"
            self.audio=Audio(self.stream, mode="w")
            args.update(AchBrkSCB=self.audio._play_AchBrkSCB)
        self.stream.LOAD(audio=audio, video=video, block=False, Acallback=Util.toSdArray, Vcallback=Util.toImage, **args)
        while not self.stream.loaded:
            time.sleep(1/1000)
        if not audio is None:
            self.audio.play()
        if not video is None:
            self.video.play(videoFrame, frame_type="label")
        self.watch.start()
    def Stop(self):
        try:
            self.video.pause()
        except: pass
        try:
            self.audio.pause()
        except: pass
        self.watch.stop()
        try:
            self.video.timer.setTime(self.watch.getTime())
        except: pass
        self.stream.SEEK(self.watch.getTime())
    def Restart(self, videoFrame=None):
        while not self.stream.loaded:
            time.sleep(1/1000)
        try:
            self.audio.play()
        except: pass
        try:
            self.video.restart()
        except: pass
        self.watch.start()
    def Close(self):
        self.Stop()
        try:
            self.audio.close()
        except: pass
        try:
            self.video.close()
        except: pass
        self.stream.CLOSE()