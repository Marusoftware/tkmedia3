from . import video, audio, picture, exception
from ._ffmpeg import FFMPEG, Filter, Util, time

#Video = video.Video
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
        #if not video is None:
        #    self.video=Video(self.stream)
        if not audio is None:
            self.audio=Audio(self.stream, mode="w")
            args.update(AchBrkSCB=self.audio._play_AchBrkSCB)
        self.stream.LOAD(audio=audio, video=video, block=False, Acallback=Util.toSdArray, **args)#, Vcallback=Util.toImage, **args)
        while not self.stream.loaded:
            time.sleep(1/1000)
        if not audio is None:
            self.audio.play()
        