from . import video, audio, picture, _ffmpeg, exception
Video = video.Video
Audio = audio.Audio
Picture = picture.Picture
MediaFileError=exception.MediaFileError

class Media:
    def __init__(self, url, mode="r", avformat=None):#TODO:書き直し
        self.stream = _ffmpeg._FFMPEG()
        self.stream.OPEN(url, mode, avformat)
        self.info=self.stream.info
        self.streams=self.stream.streams
    def Seek(self, p):
        self.stream.SEEK(p)