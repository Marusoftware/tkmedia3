from ._Sounddevice import Sounddevice, getDevices, getHostApi, getVersion
from .lib import StopWatch
from .exception import WrongOrderError

class Audio():
    def __init__(self, stream, mode="w", stopwatch=StopWatch(error=True)):
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.stopwatch=stopwatch
    def play(self, channels=2, device=None):
        if not self.ffmpeg.loader["loaded"]: raise WrongOrderError("Stream is not loaded.")
        if self.played:
            self.sdStream.Stop()
        info=self.ffmpeg.info["streams"]["audio"][self.ffmpeg.loader["audio"]]
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
        self.sdStream=Sounddevice(mode=self.mode, dataQueue=self.ffmpeg._audioQ, stopwatch=self.ffmpeg.stopwatch, streamOptions={"samplerate":info["sample_rate"], "blocksize":info["frame_size"], "channels":self.channels, "device":self.device})
        self.played=True
        self.sdStream.Play()
    def pause(self):
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Pause()
    def resume(self):
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Resume()
    def stop(self):
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Stop()
    def close(self):
        self.sdStream.Close()