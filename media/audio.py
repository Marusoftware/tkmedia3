"""Audio output and sounddevice device queries.

Use `media.Media.play` for coordinated playback. `getDevices()`,
`getHostApi()`, and `getVersion()` expose the sounddevice queries.
"""

from ._Sounddevice import Sounddevice, getDevices, getHostApi, getVersion
from .exception import WrongOrderError
import av

# Keep the existing wildcard exports while making imported device queries visible to pdoc.
__all__ = ["Audio", "getDevices", "getHostApi", "getVersion", "Sounddevice", "WrongOrderError", "av"]
__pdoc__ = {"Sounddevice": False, "WrongOrderError": False}

class Audio():
    """Play decoded audio from an already loaded stream.

    Applications normally use `media.Media` to load and coordinate tracks.
    """
    def __init__(self, stream, mode="w"):
        """Attach to the internal stream owned by a Media instance.

        Use output mode `"w"`. Recording and duplex operation are unfinished.
        """
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.stopwatch=self.ffmpeg.stopwatch
    def play(self, channels=None, device=None):
        """Open the audio device and start consuming buffered samples.

        - `device` — sounddevice output device index, or `None` for the default.
        - `channels` — Optional channel count matching the loaded audio layout.

        The stream must already be loaded. A channel count that differs from
        the selected layout raises `ValueError`.
        """
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
        """Pause sample consumption. Playback must have started."""
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Pause()
    def resume(self):
        """Resume sample consumption and discard any partially played buffer.

        The shared playback clock is controlled by Media.
        """
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.fixDataQueue(self.ffmpeg._audioQ)
        self.sdStream.Resume()
    def stop(self):
        """Stop sample consumption. Call `close()` to release the device."""
        if not self.played: raise WrongOrderError("Not played")
        self.sdStream.Stop()
    def close(self):
        """Close the sounddevice stream opened by `play()`."""
        self.sdStream.Close()
