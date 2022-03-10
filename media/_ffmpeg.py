import av, threading, time, numpy, warnings
from av import filter
from  av.audio.fifo import AudioFifo 
from queue import Full, Queue, Empty
import av.datasets
from .exception import MediaFileError
from .lib import StopWatch

def toImage(frame):
    try:
        return (frame.time, frame.to_image())
    except:
        return (frame.time, frame.to_rgb().to_image())
def toSdArray(frame):
    return (frame.time, numpy.transpose(frame.to_ndarray()).copy(order='C'))

class Filter():
    def __init__(self, stream=None, width=None, height=None, format=None, name=None):
        self.filter=filter.Graph()
        self.src=self.filter.add_buffer(template=stream, width=width, height=height, format=format, name=name)
    def addFilter(self, filter, arg):
        f = self.filter.add(filter=filter, args=arg)
        self.src.link_to(f)
        f.link_to(self.filter.add("buffersink"))
        self.filter.configure()
    def Process(self, frame):
        self.filter.push(frame=frame)
        return (frame.index, self.filter.pull())

class Stream():
    def __init__(self, path, mode="r", **options):#TODO: write support
        self.stopwatch=StopWatch(error=False)
        self.ffmpeg = av.open(av.datasets.curated(path), mode=mode, **options)
        self.info = {
            "codec_name" : self.ffmpeg.format.name.split(","),
            "codec_long" : self.ffmpeg.format.long_name,
            "mode" : mode
        }
        self.streams = self.ffmpeg.streams
        if mode == "r":
            self.info.update(bit_rate=self.ffmpeg.bit_rate)
            self.info.update(duration=self.ffmpeg.duration)
            self.info.update(size=self.ffmpeg.size)
            self.info.update(start_time=self.ffmpeg.start_time)
            def _stream_info(streams):
                def toDict(st):
                    if st.type == "video" or st.type == "audio":
                        codec=st.codec_context
                        o = {"duration":st.duration, "id":st.id, "index":st.index, "lang":st.language, "meta":st.metadata,
                        "frame_count":st.frames, "bit_rate":codec.bit_rate, "codec_name":codec.name, "codec_long":codec.codec.long_name,
                        "delay":codec.codec.delay, "time_base":st.time_base, "start_time":st.start_time}
                        if st.type == "audio":
                            o.update(channel=codec.channels, channel_name=codec.layout.name, sample_rate=st.sample_rate, frame_size=codec.frame_size)
                        elif st.type == "video":
                            o.update(height=codec.height,width=codec.width, fps=st.base_rate, aspect_ratio=codec.sample_aspect_ratio)
                        return o
                return [toDict(st) for st in streams]
            self.info.update(streams={
                "video" : _stream_info(self.streams.video),
                "audio" : _stream_info(self.streams.audio),
                "data" : _stream_info(self.streams.data),
                "subtitles" : _stream_info(self.streams.subtitles),
                "other" : _stream_info(self.streams.other)
            })
            self.loader={"state":"stop", "thread":None, "queue_min":100, "queue_max":300, "audio":None, "video":None, "loaded":False, "audio_processor":[toSdArray], "video_processor":[toImage], "frame_size": 0}
        elif mode == "w":
            pass
    def load(self, audio=None, video=None, queue_min=None, queue_max=None, wait=True):
        if not queue_min is None:
            self.loader["queue_min"]=queue_min
        if not queue_max is None:
            self.loader["queue_max"]=queue_max
        mux_source=[]
        self._oldFrames=[]
        if not audio is None:
            if len(self.info["streams"]["audio"]) == 0:
                raise MediaFileError("This File doesn't contain audio.")
            if len(self.info["streams"]["audio"]) < audio:
                raise MediaFileError(f"Audio stream '{audio}' is not exists.")
            self.loader["audio"]=audio
            self._audioPreQ=AudioFifo()
            self._audioQ=Queue(maxsize=self.loader["queue_max"])
            self.loader["frame_size"]=self.info["streams"]["audio"][audio]["frame_size"]
            mux_source.append(self.streams.get(audio=audio))
        if not video is None:
            if len(self.info["streams"]["video"]) == 0:
                raise MediaFileError("This File doesn't contain video.")
            if len(self.info["streams"]["video"]) < video:
                raise MediaFileError(f"Video stream '{video}' is not exists.")
            self.loader["video"]=video
            self._videoQ=Queue(maxsize=self.loader["queue_max"])
            mux_source.append(self.streams.get(video=video))
        if audio is None and video is None:
            return
        if not audio is None and not video is None:
            self.loader["generator"]=[self.ffmpeg.demux(audio=audio, video=video)]
        elif not audio is None:
            self.loader["generator"]=[self.ffmpeg.decode(mux_source[0])]
        elif not video is None:
            self.loader["generator"]=[self.ffmpeg.decode(mux_source[0])]
        self.loader["state"]="load"
        self.loader["thread"]=threading.Thread(target=self._loader)
        self.loader["thread"].start()
        if wait:
            while True:
                if self.loader["loaded"]:
                    break
                time.sleep(0.1)
        self.stopwatch.start()
    def _loader(self):
        for generator in self.loader["generator"]:
            for frame in generator:
                if self.loader["state"] == "stop":
                    break
                audio=self._audioQ.qsize()>= self.loader["queue_min"] if hasattr(self, "_audioQ")  else True
                video=self._videoQ.qsize()>= self.loader["queue_min"] if hasattr(self, "_videoQ")  else True
                if audio and video:
                    self.loader["loaded"]=True
                else:
                    self.loader["loaded"]=False
                req=[]
                while len(req)==0:
                    if self.loader["state"] == "pause":
                        time.sleep(0.001)
                        continue
                    elif self.loader["state"] == "stop":
                        break
                    if not self.loader["audio"] is None and self._audioQ.qsize() < self.loader["queue_min"]:
                        req.append("a")
                    if not self.loader["video"] is None and self._videoQ.qsize() < self.loader["queue_min"]:
                        req.append("v")
                    time.sleep(0.001)
                if isinstance(frame, av.packet.Packet):
                    frames=frame.decode()
                else:
                    frames=[frame]
                for frame in frames:
                    if isinstance(frame, av.audio.AudioFrame):
                        try:
                            self._audioPreQ.write(frame)
                        except:
                            pass
                        else:
                            frame=self._audioPreQ.read(self.loader["frame_size"])
                        if not frame is None:
                            if not frame in self._oldFrames:
                                self._oldFrames.append(frame)
                            for processor in self.loader["audio_processor"]:
                                frame=processor(frame)
                            try:
                                self._audioQ.put_nowait(frame)
                            except Full:
                                warnings.warn("Can't put frame to audio queue.(Queue is full)", Warning)
                    elif isinstance(frame, av.video.VideoFrame):
                        if not frame in self._oldFrames:
                            self._oldFrames.append(frame)
                        for processor in self.loader["video_processor"]:
                            frame=processor(frame)
                        try:
                            self._videoQ.put_nowait(frame)
                        except Full:
                            warnings.warn("Can't put frame to video queue.(Queue is full)", Warning)
                    else:
                        warnings.warn("Unknown frame type.", Warning)
            else:
                self.loader["state"]="stop"
                return
    def seek(self, point):
        self.stop(block=True)
        self.clear()
        for i, f in enumerate(self._oldFrames):
            if f.time > point:
                break
        self.loader["generator"]=[self._oldFrames[i:], self.loader["generator"][-1]]
        self.stopwatch.setTime(point)
        self.loader["state"]="load"
        self.loader["loaded"]=False
        self.loader["thread"]=threading.Thread(target=self._loader)
        self.loader["thread"].start()
        while True:
            if self.loader["loaded"]:
                break
            time.sleep(0.1)
        self.stopwatch.start()
    def clear(self):
        if hasattr(self, "_audioPreQ"):
            self._audioPreQ.read(0)
        if hasattr(self, "_audioQ"):
            while 1:
                try:
                    self._audioQ.get_nowait()
                except Empty:
                    break
        if hasattr(self, "_videoQ"):
            while 1:
                try:
                    self._videoQ.get_nowait()
                except Empty:
                    break
    def pause(self):
        self.loader["state"]="pause"
        self.stopwatch.stop()
    def resume(self):
        self.loader["state"]="load"
        self.stopwatch.start()
    def stop(self, block=True):
        self.loader["state"]="stop"
        if block: self.loader["thread"].join()
        self.stopwatch.stop()
    def close(self):
        self.stopwatch.stop()
        self.ffmpeg.close()