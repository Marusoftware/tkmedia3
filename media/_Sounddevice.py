import sounddevice, queue
from .exception import ModeError, WrongOrderError
from .lib import StopWatch

def getDevices(device=None, kind=None):
    return list(sounddevice.query_devices(device=device, kind=kind))
def getVersion():
    return sounddevice.get_portaudio_version()
def getHostApi(index=None):
    return sounddevice.query_hostapis(index=index)

class Sounddevice():
    def __init__(self, mode, streamOptions={}, dataQueue=None, rw_autoStop=True, stopwatch=StopWatch(error=False)):
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
                self.dataQueue = (queue.Queue(), queue.Queue())
            else:
                self.dataQueue = queue.Queue()
        else:
            self.dataQueue=dataQueue
        self.state="stop"
        self.stopwatch=stopwatch
        self.last_frametime=0
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
    def Pause(self):
        self.state="pause"
    def Resume(self):
        if self.state != "pause": WrongOrderError("Not Paused")
        self.state="play"
    def Close(self):
        self.sdStream.close()
    def _Queue(self, data, frames, time, status):
        if self.state == "play":
            try:
                gap=self.stopwatch.getTime()-self.last_frametime
                border=1
                if gap<float(0):
                    data.fill(0)
                else:
                    frame_time, datafQ=self.dataQueue.get_nowait()
                    if gap>float(border):
                        frame_time, datafQ=self.dataQueue.get_nowait()
                        data[:] = datafQ
                    else:
                        data[:] = datafQ
                    status.output_underflow=False
                    self.last_frametime=frame_time
                print("\r", gap, end="")
            except queue.Empty:
                status.output_underflow=True
                data.fill(0)
        elif self.state == "rec":
            try:
                self.dataQueue.put_nowait(data)
                status.input_overflow=False
            except queue.Full:
                status.input_overflow=True
        elif self.state == "stop":
            raise sounddevice.CallbackAbort
        elif self.state == "pause":
            data.fill(0)
    def _Queue2(self, indata, outdata, frames, time, status):
        if self.state == "both":
            try:
                self.dataQueue[0].put_nowait(indata)
                status.input_overflow=False
            except queue.Full:
                status.input_overflow=True
            try:
                outdata[:] = self.dataQueue[1].get_nowait()
                status.output_underflow=False
            except:
                status.output_underflow=True
        elif self.state == "stop":
            raise sounddevice.CallbackAbort
        elif self.state == "pause":
            outdata.fill(0)