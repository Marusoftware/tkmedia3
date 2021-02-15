from ._ffmpeg import _FFMPEG, Filter
from .exception import MediaFileError
from .lib import StopWatch
from PIL import Image, ImageTk
import time#, threading

class Video():
    def __init__(self, stream):
        self.playback = {}
        self._ffmpeg = stream.stream
        self.file_info = self._ffmpeg.info
        if len(self.file_info["streams"]["video"]) == 0:
            raise MediaFileError("This File doesn't contain video.")
        self.playback["state"]="stop"
        self.watch = StopWatch(error=False)
    def _Show(self):
        state=self.playback["state"]
        streamN = self.playback["v_streamN"]
        vid_info = self.file_info["streams"]["video"][streamN]
        sleep_time=float(1/vid_info["fps"]/self.playback["v_speed"])
        if state == "pause":
            self.watch.stop()
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
                    if self.playback["v_resize"]:
                        self.playback["temp_image"].thumbnail((self.playback["v_dispWidth"], self.playback["v_dispHeight"]))
                        self.playback["temp_image2"] = Image.new("RGBA",[self.playback["v_dispWidth"],self.playback["v_dispHeight"]],(0,0,0,255))
                        self.playback["temp_image2"].paste(self.playback["temp_image"],(int((self.playback["v_dispWidth"]-self.playback["temp_image"].size[0])/2),int((self.playback["v_dispHeight"]-self.playback["temp_image"].size[1])/2)))
                        self.playback["temp_imageTk"] = ImageTk.PhotoImage(self.playback["temp_image2"], master=self.playback["v_Frame"])
                    else:
                        self.playback["temp_imageTk"] = ImageTk.PhotoImage(self.playback["temp_image"], master=self.playback["v_Frame"])
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
    def Show(self, frame, streamN=0, start_point=0, speed=1, frameType="frame", thread_type="AUTO", height=600, width=600, resize=True):
        self.playback["v_streamN"] = streamN
        self.playback["v_Frame"] = frame
        self.playback["v_FrameType"] = frameType
        self.playback["v_dispHeight"] = height
        self.playback["v_dispWidth"] = width
        self.playback["v_resize"] = resize
        self.playback["v_speed"] = speed
        self._ffmpeg.streams.video[streamN].thread_type=thread_type
        frame.after(0, self._Show)
        self.watch.start()
        self.playback["state"] = "play"
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