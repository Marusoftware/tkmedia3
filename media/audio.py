from .exception import MediaFileError
from ._ffmpeg import _FFMPEG#, AudioFifo
import time, sounddevice, threading, numpy, queue

class Audio():#TODO: Stop, Change
    def __init__(self, stream):
        self._ffmpeg = stream.stream
        self.playback={}
        self.file_info = self._ffmpeg.info
        if len(self.file_info["streams"]["audio"]) == 0:
            raise MediaFileError("This File doesn't contain audio.")
        self.playback["state"]="stop"
        self.playback["Now"]={"load_index":0,"index":0}
        self.fifo=queue.SimpleQueue()
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
            if vstate == "pause":
                if not self.playback["syncV"] and not self.soundStream.closed:
                    self.soundStream.abort()
            if state == "pause":
                if not self.soundStream.closed:
                    self.soundStream.abort()
            elif state == "play":
                if abs(self.playback["Now"]["load_index"] - self.playback["Now"]["index"]) <= 1000:
                    if "temp_stream" in self.playback:
                        l = self.playback["temp_stream"]
                    else:
                        l = self._ffmpeg.av.decode(self._ffmpeg.streams.audio[streamN])
                        self.playback["temp_stream"]=l
                    try:
                        tmp_frame=next(l)
                    except StopIteration:
                        pass
                    else:
                        array=tmp_frame.to_ndarray()
                        self.playback["Now"]["load_index"]=tmp_frame.index
                        self.finished=False
                        if aud_info["frame_size"] != array.shape[1]:
                            print("Oh, no. wrong stream frame_size!!restarting frame...")
                            #self.soundStream.abort()
                            if self.playback["Now"]["load_index"] - self.playback["Now"]["index"] != 0:
                                while self.playback["state"] == "play" and self.playback["Now"]["load_index"] - self.playback["Now"]["index"] > 0:sounddevice.sleep(2)
                            self.soundStream.stop()
                            self.file_info["streams"]["audio"][streamN]["frame_size"]=tmp_frame.samples
                            aud_info = self.file_info["streams"]["audio"][streamN]
                            self.soundStream = sounddevice.OutputStream(channels=aud_info["channel"], dtype="float32", samplerate=aud_info["sample_rate"],
                                callback=self._Play_callback, prime_output_buffers_using_stream_callback=True, blocksize=aud_info["frame_size"])
                            if not self.finished:
                                self.soundStream.start()
                            else:
                                self.playback["state"]="pause"
                        if aud_info["frame_count"]-tmp_frame.index <= 5:
                            #border = (aud_info["frame_count"]-tmp_frame.index)*tmp_frame.samples
                            border=aud_info["frame_count"]-tmp_frame.index
                        else:
                            #border = tmp_frame.samples*5
                            border=5
                        #if self.fifo.samples < border:#TODO: sync!
                        if self.fifo.qsize() < border:
                            if not self.soundStream.stopped:
                                self.soundStream.abort()
                                print("a")
                            if self.playback["syncV"] != None and vstate == "play":
                                self.playback["syncV"].playback["state"] = "waita"
                        else:
                            if self.soundStream.stopped:
                                self.soundStream.start()
                                print("s")
                            if self.playback["syncV"] != None and vstate == "waita":
                                self.playback["syncV"].playback["state"] = "play"
                        #print(tmp_frame)
                        #self.fifo.write(tmp_frame)
                        self.fifo.put(numpy.rot90(array,-1).copy(order="C"))
                        #print("p")
            elif state == "stop" or vstate=="stop":
                if self.soundStream.active:
                    self.soundStream.abort()
                break
            sounddevice.sleep(2)
            #time.sleep(1/1000)
    def _Play_callback(self, outdata, frames, time, status):
        astate = self.playback["state"]
        if self.playback["syncV"] == None:
            vstate = "disable"
        else:
            vstate = self.playback["syncV"].playback["state"]
        aud_info = self.file_info["streams"]["audio"][self.playback["a_streamN"]]
        if astate == "play":
            try:
                data = self.fifo.get_nowait()
            except queue.Empty:
                if aud_info["frame_count"] == self.playback["Now"]["index"]:
                    if aud_info["frame_count"] == 0:
                        #print("em")
                        pass
                    else:
                        self.finished=True
                        #print("f")
                        raise sounddevice.CallbackStop
                else:
                    #print("em")
                    pass
                    #raise sounddevice.CallbackAbort
            else:
                if len(data) != len(outdata): raise sounddevice.CallbackAbort
                outdata[:] = data
                self.playback["Now"]["index"]+=1
                #print("w")
                #self.playback["Now"]["time"]+=1
        else:
            print("oh no...")
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