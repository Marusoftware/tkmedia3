import av, queue, threading, time, numpy
from av import codec, filter
from  av.audio.fifo import AudioFifo 
import av.datasets
try:
    from .exception import MediaFileError
except:
    from exception import MediaFileError

class Util():
    def toImage(frame):
        return (frame.index, frame.to_image())
    def toSdArray(frame):
        return numpy.rot90(frame.to_ndarray(), -1)

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
        elif mode == "rw" or mode == "w":
            #self.ADD=self.av.add_stream
            pass
        #self.CLOSE = self.av.close
        #self.SEEK = self.av.seek
    def LOAD(self, audio=None, video=None, block=False, Aqueue=queue.Queue(), Vqueue=queue.Queue(), border=100, Acallback=None, Vcallback=None, AchBrkSCB=None, queueMax=300):
        self.loadinfo={"AstreamN":audio, "VstreamN":video, "border":border, "queueMax":queueMax}
        mux_source=[]
        if not audio is None:
            if len(self.info["streams"]["audio"]) == 0:
                raise MediaFileError("This File doesn't contain audio.")
            self.loadinfo.update([("Astream",self.streams.get(audio=audio)),("Aqueue",Aqueue)])
            if not Acallback is None:
                self.loadinfo.update(Acallback=Acallback)
            if not AchBrkSCB is None:
                self.loadinfo.update(AchBrkSCB=AchBrkSCB)
            mux_source.append(self.loadinfo["Astream"])
        if not video is None:
            if len(self.info["streams"]["video"]) == 0:
                raise MediaFileError("This File doesn't contain video.")
            self.loadinfo.update([("Vstream",self.streams.get(video=video)),("Vqueue",Vqueue)])
            if not Vcallback is None:
                self.loadinfo.update(Vcallback=Vcallback)
            mux_source.append(self.loadinfo["Vstream"])
        if not audio is None and not video is None:
            self.loadPacket=self.av.demux(audio=audio, video=video)
        elif not audio is None:
            self.loadPacket=self.av.decode(self.loadinfo["Astream"])
        elif not video is None:
            self.loadPacket=self.av.decode(self.loadinfo["Vstream"])
        self.loadStatus="load"
        if block:
            self._LOAD()
        else:
            self.loadThread=threading.Thread(target=self._LOAD)
            self.loadThread.start()

    def _LOAD(self):
        info=self.loadinfo
        while 1:
            if self.loadStatus == "stop":
                self.loaded=False
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
                    frame=self._getFrame(info)
                    if frame:
                        self._putFrame(frame, info)
                else:
                    self.loaded=True
                    time.sleep(1/1000)
            elif "seek" in self.loadStatus:
                self.loaded=False
                point = float(self.loadStatus.split(" ")[1])
                info=self.loadinfo
                frame=self._getFrame(info)
                if frame:
                    if point-frame.time>=0:
                        while 1:
                            if point-frame.time>0:
                                pass
                            elif point-frame.time<=0:
                                self._putFrame(frame, info)
                                break
                            frame=self._getFrame(info)
                        self.loadStatus="load"
                    elif point-frame.time<0:
                        self.av.seek(0)

    def SEEK(self, point):
        if self.loaded:
            self.loadStatus = "pause"
            if "Vqueue" in self.loadinfo:
                while 1:
                    try: self.loadinfo["Vqueue"].get(block=False)
                    except queue.Empty: break
                #self.av.seek(int(point), stream=self.loadinfo["Vstream"][0])
            if "Aqueue" in self.loadinfo:
                while 1:
                    try: self.loadinfo["Aqueue"].get(block=False)
                    except queue.Empty: break
                #self.av.seek(int(point), stream=self.loadinfo["Astream"][0])
            self.loadStatus="seek "+str(point)            
            #self.loadStatus="load"
            #print(int(point))
    def CLOSE(self):
        if self.loaded:
            self.loadStatus="stop"
    def _getFrame(self, info):
        try:
            if "Vstream" in info and "Astream" in info:
                try:
                    frame=next(self.loadPacket).decode()
                    frame=frame[0]
                except IndexError:
                    print("Frame error!",frame)
                    self.loadStatus="pause"
                    return False
            else:
                frame=next(self.loadPacket)
        except StopIteration:
            self.loadStatus="pause"
            print("stopIt")
            return False
        else:
            return frame
    def _putFrame(self, frame, info):
        if type(frame) == av.audio.AudioFrame and "Aqueue" in info:
            if self.info["streams"]["audio"][info["AstreamN"]]["frame_size"] != frame.samples:
                if self.info["streams"]["audio"][info["AstreamN"]]["frame_size"] != 0 and "AchBrkSCB" in info:
                    info["AchBrkSCB"]()
                self.info["streams"]["audio"][info["AstreamN"]]["frame_size"]=frame.samples
            if "Acallback" in info:
                frame=info["Acallback"](frame)
            info["Aqueue"].put(frame, timeout=3)
            if info["Aqueue"].qsize() > info["queueMax"]:
                info["Aqueue"].get()
        elif type(frame) == av.video.VideoFrame and "Vqueue" in info:
            if "Vcallback" in info:
                frame=info["Vcallback"](frame)
            info["Vqueue"].put(frame)
            if info["Vqueue"].qsize() > info["queueMax"]:
                info["Vqueue"].get()
        else:
            print("Unknown frame!")
            print(type(frame))
            self.loadStatus="stop"
                