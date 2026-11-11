"""Seek regression tests using real PyAV decoding, without a GUI or audio device."""
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from queue import Queue

from media._ffmpeg import Stream


def bounded_call(callback, timeout=5):
    result = Queue()

    def run():
        try:
            result.put((True, callback()))
        except Exception as error:
            result.put((False, error))

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise AssertionError("Media operation did not finish within five seconds")
    success, value = result.get_nowait()
    if not success:
        raise value
    return value


class SeekTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise unittest.SkipTest("ffmpeg is required to generate test media")
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.path = Path(cls.directory.name) / "seek.mp4"
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=32x32:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
            "-t", "6", "-c:v", "mpeg4", "-g", "20", "-bf", "2",
            "-c:a", "aac", "-ac", "2", str(cls.path),
        ], check=True, timeout=20)

    def open_stream(self, audio=0, video=0, queue_min=2, queue_max=20):
        stream = Stream(str(self.path))
        self.addCleanup(lambda: bounded_call(stream.close))
        bounded_call(lambda: stream.load(audio=audio, video=video,
                                        queue_min=queue_min, queue_max=queue_max))
        return stream

    def assert_position(self, stream, target):
        for kind, tolerance in (("audio", 0.03), ("video", 0.11)):
            if stream.loader[kind] is None:
                continue
            queue = getattr(stream, "_" + kind + "Q")
            timestamp, _ = queue.get_nowait()
            self.assertGreaterEqual(timestamp, target)
            self.assertLess(timestamp, target + tolerance)
        self.assertAlmostEqual(stream.stopwatch.getTime(), target, delta=0.5)

    def test_forward_and_backward_seek_replace_worker_and_buffer(self):
        stream = self.open_stream()
        for target in (3, 1, 4.25, 0, 2):
            with self.subTest(target=target):
                old_worker = stream.loader["thread"]
                bounded_call(lambda: stream.seek(target))
                self.assertFalse(old_worker.is_alive())
                self.assertIsNot(stream.loader["thread"], old_worker)
                self.assert_position(stream, target)

    def test_seek_from_paused_full_queue(self):
        stream = self.open_stream(audio=None, queue_min=1, queue_max=1)
        stream.pause()
        bounded_call(lambda: stream.seek(3))
        self.assert_position(stream, 3)

    def test_audio_only_seek(self):
        stream = self.open_stream(video=None)
        bounded_call(lambda: stream.seek(2.5))
        self.assert_position(stream, 2.5)

    def test_video_only_seek(self):
        stream = self.open_stream(audio=None)
        bounded_call(lambda: stream.seek(2.5))
        self.assert_position(stream, 2.5)

    def test_short_tail_and_seek_after_eof(self):
        stream = self.open_stream()
        bounded_call(lambda: stream.seek(5.95))
        stream.loader["thread"].join(5)
        self.assertFalse(stream.loader["thread"].is_alive())
        self.assertTrue(stream.loader["loaded"])
        self.assertGreaterEqual(stream._audioQ.get_nowait()[0], 5.95)
        bounded_call(lambda: stream.seek(7))
        self.assertFalse(stream.loader["loaded"])
        self.assertTrue(stream._audioQ.empty())
        self.assertTrue(stream._videoQ.empty())
        bounded_call(lambda: stream.seek(1))
        self.assert_position(stream, 1)

    def test_nonblocking_seek(self):
        stream = self.open_stream()
        bounded_call(lambda: stream.seek(3, block=False))
        self.assertTrue(stream._buffer_ready.wait(5))
        self.assert_position(stream, 3)

    def test_decoder_error_reaches_seek_caller(self):
        stream = self.open_stream()

        def fail(frame):
            raise ValueError("processor failed")

        stream.loader["video_processor"] = [fail]
        with self.assertRaisesRegex(ValueError, "processor failed"):
            bounded_call(lambda: stream.seek(3))

    def test_decoded_frames_remain_in_timestamp_order(self):
        stream = self.open_stream(queue_min=1000, queue_max=1000)
        bounded_call(lambda: stream.seek(1))
        stream.loader["thread"].join(5)
        self.assertFalse(stream.loader["thread"].is_alive())
        for queue in (stream._audioQ, stream._videoQ):
            timestamps = []
            while not queue.empty():
                timestamps.append(queue.get_nowait()[0])
            self.assertTrue(timestamps)
            self.assertEqual(timestamps, sorted(timestamps))


if __name__ == "__main__":
    unittest.main()
