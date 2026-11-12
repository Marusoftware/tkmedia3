import shutil
import subprocess
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock, patch

import av
import numpy

from media._ffmpeg import Stream, toSdArray
from media._Sounddevice import Sounddevice
from media import Media


class AudioConversionTests(unittest.TestCase):
    def test_supported_formats_and_layouts_produce_float_stereo(self):
        for layout in ("mono", "stereo", "3.0", "5.1", "7.1"):
            for format in ("flt", "fltp", "s16", "s16p"):
                with self.subTest(layout=layout, format=format):
                    frame = av.AudioFrame(format=format, layout=layout, samples=1024)
                    frame.sample_rate = 48000
                    frame.time_base = Fraction(1, 48000)
                    frame.pts = 96000
                    dtype = numpy.float32 if format.startswith('flt') else numpy.int16
                    value = 0.25 if dtype == numpy.float32 else 8192
                    for plane in frame.planes[:len(frame.layout.channels)]:
                        plane.update(numpy.full(plane.buffer_size // numpy.dtype(dtype).itemsize,
                                                value, dtype=dtype).tobytes())
                    timestamp, samples = toSdArray(frame)
                    self.assertEqual(timestamp, 2)
                    self.assertEqual(samples.shape, (1024, 2))
                    self.assertEqual(samples.dtype, numpy.float32)
                    self.assertTrue(samples.flags.c_contiguous)
                    self.assertTrue(numpy.isfinite(samples).all())
                    self.assertGreater(numpy.max(numpy.abs(samples)), 0)
                    self.assertLessEqual(numpy.max(numpy.abs(samples)), 1)

    def test_center_and_surround_channels_are_audible(self):
        for channel in (2, 4, 5):
            with self.subTest(channel=channel):
                samples = numpy.zeros((6, 1024), dtype=numpy.float32)
                samples[channel] = 0.25
                frame = av.AudioFrame.from_ndarray(samples, format="fltp", layout="5.1")
                frame.sample_rate = 48000
                _, stereo = toSdArray(frame)
                self.assertGreater(numpy.max(numpy.abs(stereo)), 0)

    def test_requested_output_layout(self):
        frame = av.AudioFrame.from_ndarray(numpy.full((6, 1024), 0.1, dtype=numpy.float32),
                                          format="fltp", layout="5.1")
        frame.sample_rate = 48000
        for layout, channels in (("mono", 1), ("stereo", 2), ("5.1", 6), ("7.1", 8)):
            with self.subTest(layout=layout):
                _, samples = toSdArray(frame, layout=layout)
                self.assertEqual(samples.shape, (1024, channels))
                if layout == "5.1":
                    numpy.testing.assert_array_equal(samples, 0.1)


class AudioCallbackTests(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        clock = Mock()
        clock.getTime.return_value = 0
        with patch('media._Sounddevice.sounddevice.OutputStream',
                   return_value=SimpleNamespace(samplerate=48000)):
            self.output = Sounddevice('w', streamOptions={}, dataQueue=self.queue,
                                      stopwatch=clock)
        self.output.state = 'play'

    def render(self, frames):
        data = numpy.full((frames, 2), numpy.nan, dtype=numpy.float32)
        status = SimpleNamespace(output_underflow=False)
        self.output._Queue(data, frames, None, status)
        return data, status

    def test_variable_callback_sizes_preserve_all_samples(self):
        expected = numpy.arange(2048, dtype=numpy.float32).reshape(1024, 2) / 2048
        self.queue.put((0, expected[:300]))
        self.queue.put((300 / 48000, expected[300:]))
        rendered = []
        for frames in (128, 512, 384):
            data, status = self.render(frames)
            self.assertFalse(status.output_underflow)
            rendered.append(data)
        numpy.testing.assert_array_equal(numpy.concatenate(rendered), expected)
        self.assertAlmostEqual(self.output.last_frametime, 1024 / 48000)

    def test_short_tail_is_played_then_padded_with_silence(self):
        self.queue.put((0, numpy.full((100, 2), 0.25, dtype=numpy.float32)))
        data, status = self.render(256)
        numpy.testing.assert_array_equal(data[:100], 0.25)
        numpy.testing.assert_array_equal(data[100:], 0)
        self.assertTrue(status.output_underflow)

    def test_seek_replaces_partially_played_audio(self):
        self.queue.put((0, numpy.full((1024, 2), 0.25, dtype=numpy.float32)))
        self.render(128)
        replacement = Queue()
        replacement.put((0, numpy.full((128, 2), 0.5, dtype=numpy.float32)))
        self.output.fixDataQueue(replacement)
        data, status = self.render(128)
        numpy.testing.assert_array_equal(data, 0.5)
        self.assertFalse(status.output_underflow)


class MultichannelFileTests(unittest.TestCase):
    def test_pcm_and_aac_files_decode_to_non_silent_stereo(self):
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg is None:
            self.skipTest('ffmpeg is required to generate multichannel test media')
        with tempfile.TemporaryDirectory() as directory:
            for codec, extension in (('pcm_s16le', 'wav'), ('aac', 'm4a')):
                with self.subTest(codec=codec):
                    path = Path(directory) / ('surround.' + extension)
                    subprocess.run([
                        ffmpeg, '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
                        '-i', 'aevalsrc=0|0|0.2*sin(2*PI*440*t)|0|0|0:s=48000:c=5.1',
                        '-t', '0.1', '-c:a', codec, str(path),
                    ], check=True, timeout=15)
                    stream = Stream(str(path))
                    try:
                        stream.load(audio=0, queue_min=100, queue_max=100, block=False)
                        stream.loader['thread'].join(5)
                        self.assertFalse(stream.loader['thread'].is_alive())
                        self.assertIsNone(stream._loader_error)
                        self.assertFalse(stream._audioQ.empty())
                        peak = 0
                        while not stream._audioQ.empty():
                            _, samples = stream._audioQ.get_nowait()
                            self.assertEqual(samples.shape[1], 2)
                            self.assertEqual(samples.dtype, numpy.float32)
                            peak = max(peak, float(numpy.max(numpy.abs(samples))))
                        self.assertGreater(peak, 0)
                    finally:
                        stream.close()
                    for layout, channels in (("mono", 1), ("stereo", 2), ("5.1", 6), ("7.1", 8)):
                        with self.subTest(codec=codec, output_layout=layout):
                            media = Media(str(path))
                            try:
                                device = Mock(samplerate=48000)
                                with patch('media._Sounddevice.sounddevice.OutputStream',
                                           return_value=device) as output_stream:
                                    media.play(audio=0, audio_layout=layout)
                                self.assertEqual(output_stream.call_args.kwargs['channels'], channels)
                                self.assertEqual(media.play_options['audio_layout'], layout)
                                media.seek(0.02)
                                data = numpy.empty((128, channels), dtype=numpy.float32)
                                status = SimpleNamespace(output_underflow=False)
                                media.audio.sdStream._Queue(data, 128, None, status)
                                self.assertFalse(status.output_underflow)
                                self.assertTrue(numpy.isfinite(data).all())
                                self.assertGreater(numpy.max(numpy.abs(data)), 0)
                            finally:
                                media.close()


if __name__ == '__main__':
    unittest.main()
