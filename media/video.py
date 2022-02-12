from .exception import WrongOrderError
from PIL import ImageTk
from queue import Empty

class Video():
    def __init__(self, stream, mode="w"):
        self.ffmpeg = stream
        self.mode=mode
        self.played=False
        self.stopwatch=self.ffmpeg.stopwatch
        self.state="stop"
        self.old_frame=None
        self.old_frame2=None
        self.tkimage=None
    def play(self, frame, frame_type):
        if not self.ffmpeg.loader["loaded"]: raise WrongOrderError("Stream is not loaded.")
        info=self.ffmpeg.info["streams"]["video"][self.ffmpeg.loader["video"]]
        self.frame=frame
        self.frame_type=frame_type
        self.state="play"
        self.frame.after(info["start_time"], self._play)
        self.played=True
    def _play(self):
        if self.state=="play":
            try:
                frame=self.ffmpeg._videoQ.get_nowait()
            except Empty:
                pass
            else:
                info=self.ffmpeg.info["streams"]["video"][self.ffmpeg.loader["video"]]
                sleep_time=1/info["fps"]
                gap=self.stopwatch.getTime()-frame[0]
                border=0.5
                if gap<float(0):
                    self.frame.after(0, self._play)
                elif gap>float(border):
                    self.frame.after(int(gap), self._play)
                elif gap<=float(border):
                    if not self.old_frame is None:
                        self.old_frame.close()
                        self.old_frame2=self.tkimage
                    self.tkimage=ImageTk.PhotoImage(frame[1], master=self.frame)
                    if self.frame_type=="label":
                        self.frame.configure(image=self.tkimage)
                    self.old_frame=frame[1]
                    self.frame.after(int(sleep_time*1000), self._play)
        elif self.state == "pause":
            pass
        elif self.state == "stop":
            pass
    def pause(self):
        self.state = "pause"
    def resume(self):
        self.state = "play"
        self.frame.after(0, self._play)
    def stop(self):
        self.state="stop"
    def close(self):
        self.state="stop"