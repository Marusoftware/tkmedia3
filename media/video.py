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