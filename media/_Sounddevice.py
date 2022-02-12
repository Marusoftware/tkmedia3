import sounddevice, queue
from .exception import ModeError, WrongOrderError

def getDevices(device=None, kind=None):
    return list(sounddevice.query_devices(device=device, kind=kind))
def getVersion():
    return sounddevice.get_portaudio_version()
def getHostApi(index=None):
    return sounddevice.query_hostapis(index=index)

class Sounddevice():
    def __init__(self, mode, streamOptions={}, dataQueue=None, rw_autoStop=True):
        self.mode = mode
        if self.mode=="rw":
            if not "callback" in streamOptions: streamOptions.update(callback=self._Queue2)
            self.sdStream= sounddevice.Stream(dtype="float32", **streamOptions)
            self.rw_autoStop=rw_autoStop
        elif self.mode == "r":
            if not "callback" in streamOptions: streamOptions.update(callback=self._Queue)
            self.sdStream= sounddevice.InputStream(dtype="float32", **streamOptions)
        elif self.mode == "w":
            if not "callback" in streamOptions: streamOptions.update(callback=self._Queue)
            self.sdStream= sounddevice.OutputStream(dtype="float32", **streamOptions)
        else:
            raise ModeError("Unknown mode.")
        if dataQueue is None:
            if self.mode == "rw":
                self.dataQueue = (queue.SimpleQueue(), queue.SimpleQueue())
            else:
                self.dataQueue = queue.SimpleQueue()
        else:
            self.dataQueue=dataQueue
        self.state="stop"
    def Record(self):
        if self.mode == "w": raise ModeError("Can't record in write Mode.")
        if self.mode == "rw" and self.state == "play": self.state = "both"
        else: self.state="rec"
        self.sdStream.start()
    def Play(self):
        if self.mode == "r": raise ModeError("Can't play in read Mode.")
        if self.state in ["both", "play", "rec"]:
            raise WrongOrderError("Alredy Played.")
        if self.mode == "rw" and self.state == "rec": self.state = "both"
        else: self.state="play"
        self.sdStream.start()
    def Stop(self):
        self.state="stop"
        self.sdStream.stop()
    def Pause(self):
        self.state="pause"
    def _Queue(self, data, frames, time, status):
        if self.state == "play":
            try:
                frame_time, datafQ=self.dataQueue.get_nowait()
                data[:] = datafQ
                print("\r", int(frame_time), int(time.inputBufferDacTime), len(data), frames, status, end="")
            except:
                data.fill(0)
        elif self.state == "rec":
            self.dataQueue.put(data)
        elif self.state == "stop":
            raise sounddevice.CallbackAbort
        elif self.state == "pause":
            raise sounddevice.CallbackAbort
    def _Queue2(self, indata, outdata, frames, time, status):
        if self.state == "both":
            self.dataQueue[0].put(indata)
            outdata[:] = self.dataQueue[1].get()
        elif self.state == "stop":
            raise sounddevice.CallbackAbort
        elif self.state == "pause":
            raise sounddevice.CallbackAbort
        
