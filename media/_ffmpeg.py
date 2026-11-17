from typing import Literal
import av
import av, threading, time, numpy, warnings
from av.filter import Graph, filters_available
from av.audio.fifo import AudioFifo 
from queue import Full, Queue, Empty, SimpleQueue
from ._ass import styled_header
from .exception import MediaFileError
from .lib import StopWatch
from .picture import _fit_size
from .subtitle import decode_cues, read_subtitle_file, validate_text_stream

def toImage(frame, bounds=None):
    timestamp = frame.time
    if bounds is not None:
        size = _fit_size((frame.width, frame.height), bounds)
        if size != (frame.width, frame.height):
            frame = frame.reformat(width=size[0], height=size[1], format="rgb24")
    try:
        return (timestamp, frame.to_image())
    except:
        return (timestamp, frame.to_rgb().to_image())
def toSdArray(frame, layout:Literal["mono", "stereo", "5.1", "7.1"]="stereo"):
    # Normalize packed/planar and integer/float input, and downmix using the
    # channel layout so that center and surround audio reach stereo output.
    resampler = av.AudioResampler(format="flt", layout=layout, rate=frame.sample_rate)
    converted = resampler.resample(frame)[0]
    channels = len(converted.layout.channels)
    return (frame.time, converted.to_ndarray().reshape(-1, channels).copy(order='C'))

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
                    if st.type == "subtitle":
                        codec = st.codec_context.codec
                        return {"duration": st.duration, "id": st.id, "index": st.index,
                                "lang": st.language, "meta": st.metadata,
                                "codec_name": codec.name, "codec_long": codec.long_name,
                                "time_base": st.time_base, "start_time": st.start_time}
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
            self.loader={"state":"stop", "thread":None, "queue_min":100, "queue_max":300, "audio":None, "video":None, "loaded":False, "audio_processor":[toSdArray], "video_processor":[self._convert_video], "frame_size": 0}
            self.loader["audio_layout"] = "stereo"
            self.loader["video_size"] = None
            self.loader["audio_processor"] = [self._convert_audio]
            self._loader_stop = threading.Event()
            self._buffer_ready = threading.Event()
            self._loader_error = None
            self._seek_point = None
            self._subtitle_stream = None
            self._subtitleQ = None
            self._ass_header = None
            self._external_cues = ()
        elif mode == "w":
            pass
    def _convert_audio(self, frame):
        return toSdArray(frame, layout=self.loader["audio_layout"])
    def _convert_video(self, frame):
        bounds = self.loader["video_size"]
        if callable(bounds):
            bounds = bounds()
        return toImage(frame, bounds)

    def load(self, audio=None, video=None, queue_min=None, queue_max=None, block=True,
             audio_layout:Literal["mono", "stereo", "5.1", "7.1"]="stereo", *,
             video_size=None, subtitle=None, subtitle_file=None):
        if audio is None and video is None:
            return
        if subtitle is not None and subtitle_file is not None:
            raise ValueError("Select either a subtitle stream or a subtitle file.")
        selected = {}
        for kind, index, streams in (("audio", audio, self.streams.audio),
                                     ("video", video, self.streams.video),
                                     ("subtitle", subtitle, self.streams.subtitles)):
            if index is not None:
                first_index = 0 if kind == "subtitle" else -len(streams)
                if not first_index <= index < len(streams):
                    raise MediaFileError(f"{kind.capitalize()} stream '{index}' does not exist.")
                selected[kind] = streams[index]
        subtitle_stream = selected.get("subtitle")
        if subtitle_stream is not None:
            validate_text_stream(subtitle_stream)
        header, external_cues = None, ()
        if subtitle_file is not None:
            header, external_cues = read_subtitle_file(subtitle_file)
        elif subtitle_stream is not None:
            header = styled_header(subtitle_stream)
        layout = av.AudioLayout(audio_layout).name
        if "generator" in self.loader:
            self.stop()
            self.clear()
        self.loader["audio_layout"] = layout
        self.loader["video_size"] = video_size
        if not queue_min is None:
            self.loader["queue_min"]=queue_min
        if not queue_max is None:
            self.loader["queue_max"]=queue_max
        self.loader["audio"]=audio
        self.loader["video"]=video
        self._seek_point = None
        self._selected_streams = tuple(selected.values())
        self._subtitle_stream = subtitle_stream
        self._ass_header = header
        self._external_cues = external_cues
        self._subtitleQ = SimpleQueue() if subtitle is not None or subtitle_file is not None else None
        self._queue_external_cues(0)
        if not audio is None:
            self._audioPreQ=AudioFifo()
            self._audioQ=Queue(maxsize=self.loader["queue_max"])
            self.loader["frame_size"]=self.info["streams"]["audio"][audio]["frame_size"]
        if not video is None:
            self._videoQ=Queue(maxsize=self.loader["queue_max"])
        self.loader["generator"] = self.ffmpeg.demux(*self._selected_streams)
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
            if self._seek_point is not None and self._subtitle_stream is not None:
                self._load_active_cues(self._seek_point)
                if self._loader_stop.is_set():
                    return
                self._seek_demux(self._seek_point)
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
                if item.stream.type == "subtitle":
                    for cue in decode_cues(item, bool(self._ass_header)):
                        if self._seek_point is None or cue[0] > self._seek_point:
                            self._subtitleQ.put(cue)
                    continue
                for frame in item.decode():
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
                        # Avoid spending image-conversion time on video the
                        # renderer would discard. Leave 400 ms of the renderer's
                        # lateness allowance for conversion and Tk drawing.
                        if (self.loader["loaded"] and not self.stopwatch.isStop
                                and frame.time is not None
                                and self.stopwatch.getTime() - frame.time > 0.1):
                            continue
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
        if self._subtitle_stream is None:
            self._seek_demux(point)
        self._queue_external_cues(point)
        self._seek_point = point
        self.stopwatch.setTime(point)
        self._start_loader()
        if block:
            self._wait_loaded()
        self.stopwatch.start()

    def _seek_demux(self, point):
        self.ffmpeg.seek(int(point * av.time_base))
        self.loader["generator"] = self.ffmpeg.demux(*self._selected_streams)

    def _queue_external_cues(self, point):
        for cue in self._external_cues:
            if cue[1] > point:
                self._subtitleQ.put(cue)

    def _load_active_cues(self, point):
        # A subtitle can start before the keyframe used for the video seek.
        # Read only subtitle packets up to the target to restore overlapping cues.
        self.ffmpeg.seek(min(0, self.ffmpeg.start_time or 0))
        packets = self.ffmpeg.demux(self._subtitle_stream)
        try:
            for packet in packets:
                if self._loader_stop.is_set():
                    break
                if packet.pts is not None and float(packet.pts * packet.time_base) > point:
                    break
                for cue in decode_cues(packet, bool(self._ass_header)):
                    if cue[1] > point:
                        self._subtitleQ.put(cue)
        finally:
            packets.close()

    def clear(self):
        generator = self.loader.pop("generator", None)
        if generator is not None:
            generator.close()
        if hasattr(self, "_audioPreQ"):
            self._audioPreQ = AudioFifo()
        for queue in (*self._queues(), self._subtitleQ):
            if queue is None:
                continue
            while True:
                try:
                    queue.get_nowait()
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
