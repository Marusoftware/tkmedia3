import av
from av import codec

class _FFMPEG():
    def __init__(self):
        self.av = None
    def OPEN(self, path, mode="r", format="autodect"):
        self.av = av.open(path, mode=mode)
    def READ(self, ):
        pass
    def SEEK(self, place):
        self.av
    def CLOSE(self):
        self.av.close()