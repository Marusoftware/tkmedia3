from ._Sounddevice import Sounddevice
from .exception import WrongOrderError
import time

class Audio():
    def __init__(self, stream, mode="w"):
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
    def _play_AchBrkSCB(self):
        if self.played:
            self.sdStream.Stop()
            info=self.ffmpeg.info["streams"]["audio"][self.ffmpeg.loadinfo["AstreamN"]]
            self.sdStream=Sounddevice(mode=self.mode, dataQueue=self.ffmpeg.loadinfo["Aqueue"], streamOptions={"samplerate":info["sample_rate"], "blocksize":info["frame_size"], "channels":2, "channels":self.channels, "device":self.device})
            self.sdStream.Play()
    def play(self, channels=2, device=None):
        if not self.ffmpeg.loaded: raise WrongOrderError("Stream is not loaded.")
        if self.played:
            self.sdStream.Stop()
        info=self.ffmpeg.info["streams"]["audio"][self.ffmpeg.loadinfo["AstreamN"]]
        self.channels=channels
        self.device=device
        #print("Aqueue=",self.ffmpeg.loadinfo["Aqueue"])
        self.sdStream=Sounddevice(mode=self.mode, dataQueue=self.ffmpeg.loadinfo["Aqueue"], streamOptions={"samplerate":info["sample_rate"], "blocksize":info["frame_size"], "channels":self.channels, "device":self.device})
        self.played=True
        time.sleep(info["start_time"])
        self.sdStream.Play()