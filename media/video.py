# from ._ffmpeg import _FFMPEG, Filter
# from .exception import MediaFileError
# from .lib import StopWatch
# from PIL import Image, ImageTk
# import time#, threading

# class Video():
#     def __init__(self, stream):
#         self.playback = {}
#         self._ffmpeg = stream.stream
#         self.file_info = self._ffmpeg.info
#         if len(self.file_info["streams"]["video"]) == 0:
#             raise MediaFileError("This File doesn't contain video.")
#         self.playback["state"]="stop"
#         self.watch = StopWatch(error=False)
#         self.playback["Now"]={"time":0,"index":0}
#         self.finished=False
#     def _Show(self):
#         state=self.playback["state"]
#         streamN = self.playback["v_streamN"]
#         vid_info = self.file_info["streams"]["video"][streamN]
#         sleep_time=float(1/vid_info["fps"]/self.playback["v_speed"])
#         if state == "pause":
#             self.watch.stop()
#             self.playback["v_Frame"].after(int(sleep_time*1000), self._Show)
#             return
#         elif state == "play":
#             self.watch.start()
#             if "temp_stream" in self.playback:
#                 l = self.playback["temp_stream"]
#             else:
#             #     f = Filter.Graph()
#             #     #f.add_buffer(template=self._ffmpeg.streams.video[streamN])
#             #     #f.add("pad",":".join([str(self.playback["v_dispWidth"]),str(self.playback["v_dispHeight"])]))
#             #     #f.add("buffersink")
#             #     #f.configure()
#                 l = self._ffmpeg.av.decode(self._ffmpeg.streams.get(video=0)[0])
#                 self.playback["temp_stream"]=l
            
#             if "temp_image" in self.playback:
#                 try:
#                     self.playback["temp_image"].close()
#                     self.playback["temp_image2"].close()
#                 except:
#                     pass
#             try:
#                 if self.playback["v_resize"] == "zoom":
#                     _tmp_frame=next(l).reformat(width=self.playback["v_dispWidth"],height=self.playback["v_dispHeight"])
#                     #tmp_frame=next(l).reformat(width=self.playback["v_dispWidth"],height=self.playback["v_dispHeight"])
#                 else:
#                     _tmp_frame=next(l)
#                     #tmp_frame=next(l)
#                 self.filter.push(_tmp_frame)
#                 tmp_frame=self.filter.pull()
#             except StopIteration:
#                 if self.playback["Now"]["index"]==vid_info["frame_count"] and vid_info["frame_count"] != 0:
#                     self.playback["state"]="pause"
#                     self.playback["v_Frame"].after(0, self._Show)
#                     self.finished=True
#             else:
#                 self.finished=False
#                 self.playback["Now"]["index"]=tmp_frame.index
#                 self.playback["Now"]["time"]=sleep_time*tmp_frame.index
#                 if sleep_time*_tmp_frame.index >= self.watch.getTime():
#                     self.playback["temp_image"]=tmp_frame.to_image()
#                     if self.playback["v_resize"] == "aspect":
#                         self.playback["temp_image"].thumbnail((self.playback["v_dispWidth"], self.playback["v_dispHeight"]), Image.ANTIALIAS)
#                         self.playback["temp_image2"] = Image.new("RGBA",[self.playback["v_dispWidth"],self.playback["v_dispHeight"]],(0,0,0,255))
#                         self.playback["temp_image2"].paste(self.playback["temp_image"],(int((self.playback["v_dispWidth"]-self.playback["temp_image"].size[0])/2),int((self.playback["v_dispHeight"]-self.playback["temp_image"].size[1])/2)))
#                         self.playback["temp_imageTk"] = ImageTk.PhotoImage(self.playback["temp_image2"], master=self.playback["v_Frame"])
#                     else:
#                         self.playback["temp_imageTk"] = ImageTk.PhotoImage(self.playback["temp_image"], master=self.playback["v_Frame"])
#                     if self.playback["v_FrameType"] == "frame":
#                         self.playback["v_Frame"].configure(image=self.playback["temp_imageTk"])
#                     self.playback["v_Frame"].after(int(sleep_time*1000), self._Show)
#                 else:
#                     self.playback["v_Frame"].after(0, self._Show)
#             return
#         elif state == "reload":
#             self.watch.stop()
#             l = self._ffmpeg.av.decode(video=streamN)
#             self.playback.update(state="play")
#         elif state == "stop":
#             self.watch.stop()
#             self.watch.clear()
#             return
#         elif state == "waita":
#             self.watch.stop()
#             self.playback["v_Frame"].after(0, self._Show)
#             return
#         else:
#             self.playback.update(state="pause")
#         self.playback["v_Frame"].after(0, self._Show)
#     def Show(self, frame, streamN=0, start_point=0, speed=1, frameType="frame", thread_type="AUTO", height=600, width=600, resize="aspect"):
#         self.playback["v_streamN"] = streamN
#         self.playback["v_Frame"] = frame
#         self.playback["v_FrameType"] = frameType
#         self.playback["v_dispHeight"] = height
#         self.playback["v_dispWidth"] = width
#         self.playback["v_resize"] = resize
#         self.playback["v_speed"] = speed
#         self._ffmpeg.streams.video[streamN].thread_type=thread_type
#         self.playback["state"] = "play"
#         self.filter = Filter.Graph()
#         self.filter_src = self.filter.add_buffer(template=self._ffmpeg.streams.video[streamN])
#         if resize == "aspect":
#             pad=self.filter.add("pad", "height="+str(height)+":width="+str(width)+":y="+str(height/2)+":x="+str(width/2)+":eval=frame")
#             self.filter_src.link_to(pad)
#             pad.link_to(self.filter.add("buffersink"))
#         self.filter.configure()
#         self.playback["v_Frame"].after(0, self._Show)
#         self.watch.start()
#     def Stop(self):
#         self.playback["state"] = "stop"
#     def Change(self, key, value=None):
#         if key == "stream":
#             self.v_streamN = int(value)
#             self.Change("clr_cache")
#         elif key == "state":
#             self.state = value
#         elif key == "clr_cache":
#             self.playback.pop("temp_stream")

from .exception import WrongOrderError
from .lib import StopWatch
from PIL import ImageTk

class Video():
    def __init__(self, stream, mode="w"):
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.timer=StopWatch(error=False)
        self.state="stop"
        self.old_frame=None
        self.old_frame2=None
        self.tkimage=None
    def play(self, frame, frame_type):
        if not self.ffmpeg.loaded: raise WrongOrderError("Stream is not loaded.")
        info=self.ffmpeg.info["streams"]["video"][self.ffmpeg.loadinfo["VstreamN"]]
        self.frame=frame
        self.frame_type=frame_type
        self.timer.setTime(info["start_time"])
        self.timer.start()
        self.state="play"
        self.frame.after(info["start_time"], self._play)
        self.played=True
    def _play(self):
        if self.state=="play":
            info=self.ffmpeg.info["streams"]["video"][self.ffmpeg.loadinfo["VstreamN"]]
            frame=self.ffmpeg.loadinfo["Vqueue"].get()
            sleep_time=1/info["fps"]
            gap=self.timer.getTime()-frame[0]*sleep_time
            border=1
            if gap<float(0):
                self.frame.after(0, self._play)
            if gap>float(border):
                self.frame.after(int(gap), self._play)
            if gap<=float(border):
                if not self.old_frame is None:
                    self.old_frame.close()
                    self.old_frame2=self.tkimage
                self.tkimage=ImageTk.PhotoImage(frame[1], master=self.frame)
                if self.frame_type=="label":
                    self.frame.configure(image=self.tkimage)
                self.old_frame=frame[1]
                self.frame.after(int(sleep_time*1000), self._play)
                #self.frame.after(int(frame[0]*sleep_time-self.timer.getTime()), self._play)   
        elif self.state == "pause":
            pass
        elif self.state == "stop":
            pass
    
    def pause(self):
        self.state = "pause"
        self.timer.stop()
        
    def restart(self):
        print(self.timer.getTime())
        self.state = "play"
        self.frame.after(0, self._play)
        self.timer.start()
    
    def close(self):
        self.state="stop"
        self.timer.stop()