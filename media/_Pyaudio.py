import pyaudio

import queue
from .exception import ModeError, WrongOrderError

portaudio=pyaudio.PyAudio()

def getDevices(device=None, kind=None):
    if not device is None and type(device) == int:
        return portaudio.get_device_info_by_index(device)
    else:
        l = []
        for i in range(portaudio.get_device_count()):
            dv = portaudio.get_device_info_by_index(i)
            if not device is None and type(device) == str and dv["name"] == device:
                return dv
            elif not kind is None:
                if kind == "input" and dv["maxInputChannels"] != 0:
                    l.append(dv)
                elif kind == "output" and dv["maxOutputChannels"] != 0:
                    l.append(dv)
            else:
                l.append(dv)
        return l

def getVersion():
    return (pyaudio.get_portaudio_version(), pyaudio.get_portaudio_version_text())

def getHostApi(index=None):
    if not index is None and type(index) == int:
        return portaudio.get_host_api_info_by_index(index)
    else:
        l =[]
        for i in range(portaudio.get_host_api_count()):
            ha = portaudio.get_host_api_info_by_index(i)
            l.append(ha)
        return l

class PyAudio():
    def __init__(self, mode, rate, streamOptions={"start": False}, dataQueue=None, rw_autoStop=True, channels:int=2):
        self.mode = mode
        if not "stream_callback" in streamOptions: streamOptions.update(stream_callback=self._Queue)
        if self.mode=="rw":
            self.sdStream= portaudio.open(rate=rate, channels=channels, format=pyaudio.paFloat32, output=True, input=True, **streamOptions)
            self.rw_autoStop=rw_autoStop
        elif self.mode == "r":
            self.sdStream= portaudio.open(rate=rate, channels=channels, format=pyaudio.paFloat32, input=True, **streamOptions)
        elif self.mode == "w":
            self.sdStream= portaudio.open(rate=rate, channels=channels, format=pyaudio.paFloat32, output=True, **streamOptions)
        else:
            raise ModeError("Unknown mode.")
        if dataQueue is None:
            if self.mode == "rw":
                self.dataQueue = (queue.Queue(), queue.Queue())
            else:
                self.dataQueue = queue.Queue()
        else:
            self.dataQueue=dataQueue
        self.state="stop"
    def Record(self):
        if self.mode == "w": raise ModeError("Can't record in write Mode.")
        if self.state in ["both", "play", "rec"]:
            raise WrongOrderError("Alredy Played.")
        elif self.state == "close":
            raise WrongOrderError("Already closed.")
        if self.mode == "rw" and self.state == "play": self.state = "both"
        else: self.state="rec"
        self.sdStream.start_stream()
    def Play(self):
        if self.mode == "r": raise ModeError("Can't play in read Mode.")
        if self.state in ["both", "play", "rec"]:
            raise WrongOrderError("Alredy Played.")
        elif self.state == "close":
            raise WrongOrderError("Already closed.")
        if self.mode == "rw" and self.state == "rec": self.state = "both"
        else: self.state="play"
        self.sdStream.start_stream()
    def Stop(self):
        self.state="stop"
        self.sdStream.close()
    def Pause(self):
        self.state="pause"
        self.sdStream.stop_stream()
    def Close(self):
        self.state="close"
        self.sdStream.close()
    def _Queue(self, data, frames, time, status):
        state = self.state
        if state == "play":
            return(self.dataQueue.get(), pyaudio.paContinue)
        elif state == "rec":
            self.dataQueue.put(data)
            return([],pyaudio.paContinue)
        elif state == "stop":
            return([],pyaudio.paComplete)
        elif state == "both":
            self.dataQueue[0].put(data)
            return (self.dataQueue[1].get(), pyaudio.paContinue)