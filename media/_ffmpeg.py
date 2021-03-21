import av, queue, threading, time
from av import codec, filter
from  av.audio.fifo import AudioFifo 
import av.datasets
try:
    from .exception import MediaFileError
except:
    from exception import MediaFileError

class Filter():
    def __init__(self):
        self.filter=filter.Graph()

class FFMPEG():
    def __init__(self):
        self.av = None
        self.loaded=False
    def OPEN(self, path, mode="r", avformat=None):
        self.av = av.open(av.datasets.curated(path), mode=mode, format=avformat)
        self.info = {
            "codec_name" : self.av.format.name.split(","),
            "codec_long" : self.av.format.long_name,
            "mode" : mode
        }
        if mode == "rw" or mode == "r":
            self.streams = self.av.streams
            self.info.update(bit_rate=self.av.bit_rate)
            self.info.update(duration=self.av.duration)
            self.info.update(size=self.av.size)
            self.info.update(start_time=self.av.start_time)
            def _stream_info(streams):
                def toDict(st):
                    if st.type == "video" or st.type == "audio":
                        codec=st.codec_context
                        o = {"duration":st.duration, "id":st.id, "index":st.index, "lang":st.language, "meta":st.metadata,
                        "frame_count":st.frames, "bit_rate":codec.bit_rate, "codec_name":codec.name, "codec_long":codec.codec.long_name,
                        "delay":codec.codec.delay, "time_base":st.time_base}
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
        elif mode == "rw" or mode == "w":
            #self.ADD=self.av.add_stream
            pass
        #self.CLOSE = self.av.close
        #self.SEEK = self.av.seek
    def LOAD(self, audio=None, video=None, block=False, Aspeed=1, Vspeed=1, Aqueue=queue.SimpleQueue(), Vqueue=queue.SimpleQueue(), border=100):
        self.loadinfo={"AstreamN":audio, "VstreamN":video, "border":border}
        if not audio is None:
            if len(self.info["streams"]["audio"]) == 0:
                raise MediaFileError("This File doesn't contain audio.")
            self.loadinfo.update([("Astream",self.streams.get(audio=audio)),("Aspeed",Aspeed),("Aqueue",Aqueue)])
        if not video is None:
            if len(self.info["streams"]["video"]) == 0:
                raise MediaFileError("This File doesn't contain video.")
            self.loadinfo.update([("Vstream",self.streams.get(video=video)),("Vspeed",Vspeed),("Vqueue",Vqueue)])
        self.loadPacket=self.av.demux(audio=audio, video=video)
        self.loadStatus="load"
        self.loaded=True
        self.loadThread=threading.Thread(target=self._LOAD)
        self.loadThread.start()

    def _LOAD(self):
        info=self.loadinfo
        while 1:
            if self.loadStatus == "stop":
                break
            elif self.loadStatus == "pause":
                while self.loadStatus == "pause":
                    time.sleep(1/1000)
            elif self.loadStatus == "reload":
                info=self.loadinfo
            elif self.loadStatus == "load":
                req=[]
                if "Vqueue" in info:
                    if info["Vqueue"].qsize() <= info["border"]:
                        req.append("v")
                if "Aqueue" in info:
                    if info["Aqueue"].qsize() <= info["border"]:
                        req.append("a")
                if "a" in req or "v" in req:
                    try:
                        frame=next(self.loadPacket).decode()[0]
                    except StopIteration:
                        self.loadStatus="pause"
                    else:
                        if type(frame) == av.audio.AudioFrame and "Aqueue" in info:
                            info["Aqueue"].put(frame)
                        elif type(frame) == av.video.VideoFrame and "Vqueue" in info:
                            info["Vqueue"].put(frame)
                        else:
                            print("Unknown frame!")
                            print(type(frame))
                            self.loadStatus="stop"
                else:
                    time.sleep(1/1000)
    def CLOSE(self):
        if self.loaded:
            self.loadStatus="stop"
                