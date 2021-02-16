from .exception import MediaFileError
from ._ffmpeg import _FFMPEG, AudioFifo
import time, sounddevice, threading, numpy, queue

class Audio():#TODO: Stop, Change
    def __init__(self, stream):
        self._ffmpeg = stream.stream
        self.playback={}
        self.file_info = self._ffmpeg.info
        if len(self.file_info["streams"]["audio"]) == 0:
            raise MediaFileError("This File doesn't contain audio.")
        self.playback["state"]="stop"
        self.playback["Now"]={"time":0,"index":0}
        self.fifo=AudioFifo()
        self.finished=False
    def _Play(self):#TODO:speed, sounddevice_param, stop, reload(no sync??), bug fix
        while 1:
            if self.playback["syncV"] != None:
                vplayback = self.playback["syncV"].playback
                vstate=vplayback["state"]
            else:
                vstate="disable"
            state=self.playback["state"]
            streamN = self.playback["a_streamN"]
            aud_info = self.file_info["streams"]["audio"][streamN]
            if state == "pause" or vstate=="pause":
                if self.soundStream.active:
                    self.soundStream.abort()
            elif state == "play":
                if "temp_stream" in self.playback:
                    l = self.playback["temp_stream"]
                else:
                    l = self._ffmpeg.av.decode(self._ffmpeg.streams.audio[streamN])
                    self.playback["temp_stream"]=l
                try:
                    tmp_frame=next(l)
                except StopIteration:
                    if not self.soundStream.active:
                        self.soundStream.start()
                else:
                    self.playback["Now"]["index"]=tmp_frame.index
                    self.finished=False
                    if aud_info["frame_count"]-tmp_frame.index <= 5:
                        border = (aud_info["frame_count"]-tmp_frame.index)*tmp_frame.samples
                    else:
                        border = tmp_frame.samples*5
                    if self.fifo.samples < border:#TODO: sync!
                        if self.soundStream.active:
                            self.soundStream.abort()
                        if self.playback["syncV"] != None and vstate == "play":
                            self.playback["syncV"].playback["state"] = "waita"
                    else:
                        if not self.soundStream.active:
                            self.soundStream.start()
                        if self.playback["syncV"] != None and vstate == "waita":
                            self.playback["syncV"].playback["state"] = "play"
                    self.fifo.write(tmp_frame)
            elif state == "stop" or vstate=="stop":
                if self.soundStream.active:
                    self.soundStream.abort()
                break
            time.sleep(1/1000)
    def _Play_callback(self, outdata, frames, time, status):
        aud_info = self.file_info["streams"]["audio"][self.playback["a_streamN"]]
        if self.fifo.samples_written:
            data = self.fifo.read(len(outdata))
            if data == None:
                if aud_info["frame_count"] == self.playback["Now"]["index"]:
                    self.soundStream.abort()
                    self.finished=True
                else:
                    print("oh no...")
                    raise sounddevice.CallbackAbort
            else:
                self.playback["Now"]["time"]+=self.fifo.pts_per_sample
                outdata[:] = numpy.rot90(data.to_ndarray(),-1).copy(order="C")
        else:
            print("oh no...")
            raise sounddevice.CallbackAbort
    def Play(self, streamN=0, syncV=None, speed=1, thread_type="AUTO"):
        self.playback["a_streamN"] = streamN
        self.playback["syncV"] = syncV
        self.playback["state"] = "play"
        self.playback["a_speed"] = speed
        aud_info = self.file_info["streams"]["audio"][streamN]
        self._ffmpeg.streams.audio[streamN].thread_type=thread_type
        self.thread = threading.Thread(target=self._Play)
        self.soundStream = sounddevice.OutputStream(channels=aud_info["channel"], dtype="float32", samplerate=aud_info["sample_rate"],
        callback=self._Play_callback, prime_output_buffers_using_stream_callback=True, blocksize=aud_info["frame_size"])
        self.thread.start()
    def Stop(self):
        self.playback["state"] = "stop"
    def Change(self, key, value=None):
        if key == "stream":
            self.v_streamN = int(value)
            self.Change("clr_cache")
        elif key == "state":
            self.state = value
        elif key == "clr_cache":
            self.playback.pop("temp_stream")