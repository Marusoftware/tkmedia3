from . import video, audio, picture, _ffmpeg
Video = video.Video
Audio = audio.Audio
Picture = picture.Picture

class Media:
    def __init__(self, url, mode="r", avformat=None):#TODO:書き直し
        self.stream = _ffmpeg._FFMPEG()
        self.stream.OPEN(url, mode, avformat)