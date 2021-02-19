import av
from av import codec, filter
from  av.audio.fifo import AudioFifo 
import av.datasets

Filter = filter

class _FFMPEG():
    def __init__(self):
        self.av = None
    def OPEN(self, path, mode="r", avformat="autodetect"):
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
            self.ADD=self.av.add_stream
        self.CLOSE = self.av.close
        self.SEEK = self.av.seek