#from ._Sounddevice import Sounddevice, getDevices, getHostApi, getVersion
from .lib import StopWatch
from ._Pyaudio import PyAudio, getDevices, getHostApi, getVersion
from .exception import WrongOrderError
import time

class Audio():
    def __init__(self, stream, mode="w", stopwatch=StopWatch(error=True)):
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.stopwatch=stopwatch
    def _play_AchBrkSCB(self):
        if self.played:
            self.sdStream.Close()
            info=self.ffmpeg.info["streams"]["audio"][self.ffmpeg.loadinfo["AstreamN"]]
            #self.sdStream=Sounddevice(mode=self.mode, dataQueue=self.ffmpeg.loadinfo["Aqueue"], streamOptions={"samplerate":info["sample_rate"], "blocksize":info["frame_size"], "channels":2, "channels":self.channels, "device":self.device})
            self.sdStream=PyAudio(mode=self.mode, rate=info["sample_rate"], channels=self.channels, dataQueue=self.ffmpeg.loadinfo["Aqueue"], streamOptions=self.streamOptions)
            self.sdStream.Play()
    def play(self, channels=2, device=None):
        if not self.ffmpeg.loaded: raise WrongOrderError("Stream is not loaded.")
        if self.played:
            self.sdStream.Stop()
        info=self.ffmpeg.info["streams"]["audio"][self.ffmpeg.loadinfo["AstreamN"]]
        self.channels=channels
        self.device=device
        streamOptions={"frames_per_buffer":info["frame_size"]}
        if self.mode == "rw":
            if type(self.device) in [list, tuple]:
                streamOptions.update(input_device_index=self.device[0], output_device_index=self.device[1])
            else:
                streamOptions.update(input_device_index=self.device, output_device_index=self.device)
        elif self.mode == "r":
            streamOptions.update(input_device_index=self.device)
        else:
            streamOptions.update(output_device_index=self.device)
        self.streamOptions=streamOptions
        #self.sdStream=Sounddevice(mode=self.mode, dataQueue=self.ffmpeg.loadinfo["Aqueue"], streamOptions={"samplerate":info["sample_rate"], "blocksize":info["frame_size"], "channels":self.channels, "device":self.device})
        self.sdStream=PyAudio(mode=self.mode, rate=info["sample_rate"], channels=self.channels, dataQueue=self.ffmpeg.loadinfo["Aqueue"], streamOptions=self.streamOptions)
        self.played=True
        #time.sleep(info["start_time"])
        self.sdStream.Play()
    def pause(self):
        if not self.ffmpeg.loaded: raise WrongOrderError("Stream is not loaded.")
        if not self.played: raise WrongOrderError("Already paused.")
        self.sdStream.Stop()