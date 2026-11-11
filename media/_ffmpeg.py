from typing import Literal
import av
import av, threading, time, numpy, warnings
from av.filter import Graph, filters_available
from av.audio.fifo import AudioFifo 
from queue import Full, Queue, Empty
from .exception import MediaFileError
from .lib import StopWatch

def toImage(frame):
    try:
        return (frame.time, frame.to_image())
    except:
        return (frame.time, frame.to_rgb().to_image())
def toSdArray(frame):
    return (frame.time, numpy.transpose(frame.to_ndarray()[:2]).copy(order='C'))

class AudioFilter():
    def __init__(self, stream=None, width=None, height=None, format=None, name=None):
        self.filter=Graph()
        self.src=self.filter.add_abuffer(template=stream, width=width, height=height, format=format, name=name)
    def addFilter(self, filter, arg):
        f = self.filter.add(filter=filter, args=arg)
        self.src.link_to(f)
        f.link_to(self.filter.add("buffersink"))#thinking...
        self.filter.configure()
    def Process(self, frame):
        self.filter.push(frame=frame)
        return self.filter.pull()
    def getFilter(self):
        pass
    def availableFilters(self):
        return filters_available

class VideoFilter():
    def __init__(self, stream=None, width=None, height=None, format=None, name=None):
        self.filter=Graph()
        self.src=self.filter.add_buffer(template=stream, width=width, height=height, format=format, name=name)
    def addFilter(self, filter, arg):
        f = self.filter.add(filter=filter, args=arg)
        self.src.link_to(f)
        f.link_to(self.filter.add("buffersink"))#thinking...
        self.filter.configure()
    def Process(self, frame):
        self.filter.push(frame=frame)
        return self.filter.pull()
    def getFilter(self):
        pass
    def availableFilters(self):
        return filters_available

class Stream():
    def __init__(self, path, mode:Literal["r", "w"]="r", **options):#TODO: write support
        self.stopwatch=StopWatch(error=False)
        self.ffmpeg = av.open(path, mode=mode, **options)
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
            self._loader_stop = threading.Event()
            self._buffer_ready = threading.Event()
            self._loader_error = None
            self._seek_point = None
        elif mode == "w":
            pass
    def load(self, audio=None, video=None, queue_min=None, queue_max=None, block=True):
        if audio is None and video is None:
            return
        if not queue_min is None:
            self.loader["queue_min"]=queue_min
        if not queue_max is None:
            self.loader["queue_max"]=queue_max
        self.loader["audio"]=audio
        self.loader["video"]=video
        mux_source=[]
        if not audio is None:
            if len(self.info["streams"]["audio"]) == 0:
                raise MediaFileError("This File doesn't contain audio.")
            if len(self.info["streams"]["audio"]) < audio:
                raise MediaFileError(f"Audio stream '{audio}' is not exists.")
            self._audioPreQ=AudioFifo()
            self._audioQ=Queue(maxsize=self.loader["queue_max"])
            self.loader["frame_size"]=self.info["streams"]["audio"][audio]["frame_size"]
            mux_source.append(self.streams.get(audio=audio))
        if not video is None:
            if len(self.info["streams"]["video"]) == 0:
                raise MediaFileError("This File doesn't contain video.")
            if len(self.info["streams"]["video"]) < video:
                raise MediaFileError(f"Video stream '{video}' is not exists.")
            self._videoQ=Queue(maxsize=self.loader["queue_max"])
            mux_source.append(self.streams.get(video=video))
        if not audio is None and not video is None:
            self.loader["generator"]=self.ffmpeg.demux(audio=audio, video=video)
        elif not audio is None:
            self.loader["generator"]=self.ffmpeg.decode(mux_source[0])
        elif not video is None:
            self.loader["generator"]=self.ffmpeg.decode(mux_source[0])
        del mux_source
        self._start_loader()
        if block:
            self._wait_loaded()
        self.stopwatch.start()
    def _start_loader(self):
        self.loader["loaded"] = False
        self._loader_error = None
        self._loader_stop.clear()
        self._buffer_ready.clear()
        self.loader["state"] = "load"
        self.loader["thread"] = threading.Thread(target=self._loader)
        self.loader["thread"].start()
    def _wait_loaded(self):
        self._buffer_ready.wait()
        if self._loader_error is not None:
            raise self._loader_error
    def _queues(self):
        return [getattr(self, "_" + kind + "Q") for kind in ("audio", "video")
                if self.loader[kind] is not None]
    def _update_loaded(self):
        queues = self._queues()
        # A full queue must be consumed before demuxing can continue, even
        # when another stream has not reached queue_min yet.
        if queues and (all(q.qsize() >= self.loader["queue_min"] for q in queues)
                       or any(q.full() for q in queues)):
            self.loader["loaded"] = True
            self._buffer_ready.set()
    def _loader(self):
        try:
            generator = self.loader["generator"]
            while not self._loader_stop.is_set():
                if (self.loader["state"] == "pause"
                        or any(q.full() for q in self._queues())):
                    self._loader_stop.wait(0.001)
                    continue
                try:
                    item = next(generator)
                except StopIteration:
                    break
                frames = item.decode() if isinstance(item, av.Packet) else [item]
                for frame in frames:
                    if self._loader_stop.is_set():
                        return
                    # Seeking lands on a preceding keyframe. Decode from it,
                    # but only enqueue frames at or after the requested time.
                    if (self._seek_point is not None and frame.time is not None
                            and frame.time < self._seek_point):
                        continue
                    if isinstance(frame, av.AudioFrame):
                        kind = "audio"
                    elif isinstance(frame, av.VideoFrame):
                        kind = "video"
                    else:
                        warnings.warn("Unknown frame type.", Warning)
                        continue
                    for processor in self.loader[kind + "_processor"]:
                        frame = processor(frame)
                    queue = getattr(self, "_" + kind + "Q")
                    while not self._loader_stop.is_set():
                        try:
                            queue.put_nowait(frame)
                            self._update_loaded()
                            break
                        except Full:
                            self._loader_stop.wait(0.001)
        except Exception as error:
            self._loader_error = error
        finally:
            self.loader["state"] = "stop"
            if not self._loader_stop.is_set():
                self.loader["loaded"] = any(not q.empty() for q in self._queues())
            # EOF (including an empty tail) and decoding errors also end a
            # blocking load/seek; neither may leave the caller waiting forever.
            self._buffer_ready.set()
    def seek(self, point, block=True):
        # The container and its iterator must not be used by the old worker
        # while we seek or clear its queues.
        self.stop()
        self.clear()
        self.ffmpeg.seek(int(point * av.time_base))
        if self.loader["audio"] is not None and self.loader["video"] is not None:
            self.loader["generator"]=self.ffmpeg.demux(audio=self.loader["audio"], video=self.loader["video"])
        elif self.loader["audio"] is not None:
            self.loader["generator"]=self.ffmpeg.decode(audio=self.loader["audio"])
        elif self.loader["video"] is not None:
            self.loader["generator"]=self.ffmpeg.decode(video=self.loader["video"])
        self._seek_point = point
        self.stopwatch.setTime(point)
        self._start_loader()
        if block:
            self._wait_loaded()
        self.stopwatch.start()
    def clear(self):
        generator = self.loader.pop("generator", None)
        if generator is not None:
            generator.close()
        if hasattr(self, "_audioPreQ"):
            self._audioPreQ = AudioFifo()
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
        self._loader_stop.set()
        if block and self.loader["thread"] is not None:
            self.loader["thread"].join()
        self.stopwatch.stop()
    def close(self):
        self.stop()
        self.ffmpeg.close()
