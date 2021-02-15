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
        self.fifo=AudioFifo()
    def _Play(self):#TODO:speed, sounddevice_param, stop, reload(no sync??), bug fix
        #try: 
        while 1:
            if self.playback["syncV"] != None:
                vplayback = self.playback["syncV"].playback
                state=vplayback["state"]
            else:
                state=self.playback["state"]
            streamN = self.playback["a_streamN"]
            aud_info = self.file_info["streams"]["audio"][streamN]
            if state == "pause":
                if not self.soundStream.active:
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
                    pass
                else:
                    self.fifo.write(tmp_frame)
            time.sleep(1/1000)
    def _Play_callback(self, outdata, frames, time, status):
        if self.fifo.samples_written:
            outdata[:] = numpy.rot90(self.fifo.read(len(outdata)).to_ndarray(),-1).copy(order="C")
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
        self.soundStream = sounddevice.OutputStream(channels=aud_info["channel"], dtype="float32", samplerate=aud_info["sample_rate"], callback=self._Play_callback,prime_output_buffers_using_stream_callback=True)
        self.thread.start()
        self.soundStream.start()
        #if syncV == None:
        #self.soundStream.start()

""" class Video():
    def _Show(self):
        if state == "pause":
            #self.watch.stop()
            self.playback["v_Frame"].after(int(sleep_time*1000), self._Show)
            return
        elif state == "play":
            self.watch.start()
            if "temp_stream" in self.playback:
                l = self.playback["temp_stream"]
            else:
                #f = Filter.Graph()
                #f.add_buffer(template=self._ffmpeg.streams.video[streamN])
                #f.add("pad",":".join([str(self.playback["v_dispWidth"]),str(self.playback["v_dispHeight"])]))
                #f.add("buffersink")
                #f.configure()
                l = self._ffmpeg.av.decode(video=streamN)
                self.playback["temp_stream"]=l
            
            if "temp_image" in self.playback:
                try:
                    self.playback["temp_image"].close()
                    self.playback["temp_image2"].close()
                    #self.playback.pop("temp_image")
                except:
                    pass
            try:
                #tmp_frame=next(l).reformat(width=self.playback["v_dispWidth"],height=self.playback["v_dispHeight"])
                tmp_frame=next(l)
            except StopIteration:
                self.playback["state"]="stop"
                self.playback["v_Frame"].after(0, self._Show)
            else:
                if sleep_time*tmp_frame.index >= self.watch.getTime():
                    self.playback["temp_image"]=tmp_frame.to_image()
                    self.playback["temp_image"].thumbnail((self.playback["v_dispWidth"], self.playback["v_dispHeight"]))
                    self.playback["temp_image2"] = Image.new("RGBA",[self.playback["v_dispWidth"],self.playback["v_dispHeight"]],(0,0,0,255))
                    self.playback["temp_image2"].paste(self.playback["temp_image"],(int((self.playback["v_dispWidth"]-self.playback["temp_image"].size[0])/2),int((self.playback["v_dispHeight"]-self.playback["temp_image"].size[1])/2)))
                    self.playback["temp_imageTk"] = ImageTk.PhotoImage(self.playback["temp_image2"], master=self.playback["v_Frame"])
                    if self.playback["v_FrameType"] == "frame":
                        self.playback["v_Frame"].configure(image=self.playback["temp_imageTk"])
                    self.playback["v_Frame"].after(int(sleep_time*1000), self._Show)
                else:
                    self.playback["v_Frame"].after(0, self._Show)
            #self.playback["v_time"]+=(time.time()-t1)
            return
        elif state == "reload":
            self.watch.stop()
            l = self._ffmpeg.av.decode(video=streamN)
            self.playback.update(state="play")
        elif state == "stop":
            self.watch.stop()
            self.watch.clear()
            return
        else:
            self.playback.update(state="pause")
        self.playback["v_Frame"].after(0, self._Show)
    def Show(self, frame, streamN=0, start_point=0, speed=1, frameType="frame", thread_type="AUTO", height=600, width=600):
        self.playback["v_streamN"] = streamN
        self.playback["v_Frame"] = frame
        self.playback["v_FrameType"] = frameType
        self.playback["v_Point"] = start_point
        self.playback["v_dispHeight"] = height
        self.playback["v_dispWidth"] = width
        self.playback["v_time"] = 1
        self.playback["state"] = "play"
        self.playback["v_speed"] = speed
        self._ffmpeg.streams.video[streamN].thread_type=thread_type
        frame.after(0, self._Show)
    def Stop(self):
        self.playback["state"] = "stop"
    def Change(self, key, value=None):
        if key == "stream":
            self.v_streamN = int(value)
            self.Change("clr_cache")
        elif key == "state":
            self.state = value
        elif key == "clr_cache":
            self.playback.pop("temp_stream") """