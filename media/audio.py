from ._Sounddevice import Sounddevice, getDevices, getHostApi, getVersion
from .exception import WrongOrderError
import av

class Audio():
    def __init__(self, stream, mode="w"):
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.stopwatch=self.ffmpeg.stopwatch
    def play(self, channels=None, device=None):
        if not self.ffmpeg.loader["loaded"]: raise WrongOrderError("Stream is not loaded.")
        output_channels = len(av.AudioLayout(self.ffmpeg.loader.get("audio_layout", "stereo")).channels)
        if channels is not None and channels != output_channels:
            raise ValueError("channels must match the audio_layout selected when loading the stream")
        if self.played:
            self.sdStream.Stop()
        info=self.ffmpeg.info["streams"]["audio"][self.ffmpeg.loader["audio"]]
        self.channels=output_channels
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
        self.sdStream=Sounddevice(mode=self.mode, dataQueue=self.ffmpeg._audioQ, stopwatch=self.stopwatch, streamOptions={"samplerate":info["sample_rate"], "blocksize":info["frame_size"], "channels":self.channels, "device":self.device})
        self.played=True
        self.sdStream.Play()
    def pause(self):
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Pause()
    def resume(self):
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.fixDataQueue(self.ffmpeg._audioQ)
        self.sdStream.Resume()
    def stop(self):
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Stop()
    def close(self):
        self.sdStream.Close()
