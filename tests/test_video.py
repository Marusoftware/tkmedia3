import unittest
from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock, patch

from media import Media
from media.video import Video


class Widget:
    """A controllable Tk timer queue; tests advance the playback clock explicitly."""
    def __init__(self):
        self.callbacks = {}
        self.serial = 0
        self.configure = Mock()

    def after(self, delay, callback):
        self.serial += 1
        self.callbacks[self.serial] = (delay, callback)
        return self.serial

    def after_cancel(self, identifier):
        del self.callbacks[identifier]

    def tick(self):
        identifier = next(iter(self.callbacks))
        _, callback = self.callbacks.pop(identifier)
        callback()


class VideoTimingTests(unittest.TestCase):
    def setUp(self):
        self.clock = Mock()
        self.clock.getTime.return_value = 0
        self.stream = SimpleNamespace(
            stopwatch=self.clock, _videoQ=Queue(),
            loader={"loaded": True, "video": 0},
            info={"streams": {"video": [{"fps": 25, "start_time": 0}]}},
            pause=Mock(), resume=Mock(), seek=Mock(),
        )
        self.widget = Widget()
        self.video = Video(self.stream)
        self.photo = patch('media.video.ImageTk.PhotoImage', side_effect=lambda image, **kw: image)
        self.photo.start()
        self.addCleanup(self.photo.stop)
        self.video.play(self.widget, "label")

    def test_future_frame_waits_without_consuming_more_frames(self):
        first, second = Mock(), Mock()
        self.stream._videoQ.put((1, first))
        self.stream._videoQ.put((2, second))
        self.widget.tick()
        self.assertEqual(self.stream._videoQ.qsize(), 1)
        self.assertEqual(next(iter(self.widget.callbacks.values()))[0], 1000)
        self.widget.configure.assert_not_called()
        self.clock.getTime.return_value = 0.9
        self.widget.tick()
        self.assertEqual(self.stream._videoQ.qsize(), 1)
        self.clock.getTime.return_value = 1
        self.widget.tick()
        self.widget.configure.assert_called_once_with(image=first)
        first.close.assert_not_called()

    def test_late_frame_is_dropped_and_current_frame_is_displayed(self):
        late, current = Mock(), Mock()
        self.stream._videoQ.put((0, late))
        self.stream._videoQ.put((1, current))
        self.clock.getTime.return_value = 1
        self.widget.tick()
        late.close.assert_called_once()
        self.assertEqual(next(iter(self.widget.callbacks.values()))[0], 0)
        self.widget.tick()
        self.widget.configure.assert_called_once_with(image=current)

    def test_pause_retains_frame_and_resume_has_one_callback(self):
        image = Mock()
        self.stream._videoQ.put((1, image))
        self.widget.tick()
        self.video.pause()
        self.assertFalse(self.widget.callbacks)
        image.close.assert_not_called()
        self.video.resume()
        self.video.resume()
        self.assertEqual(len(self.widget.callbacks), 1)
        self.clock.getTime.return_value = 1
        self.widget.tick()
        self.widget.configure.assert_called_once_with(image=image)

    def test_media_seek_discards_old_pending_frame_and_timer(self):
        old, new = Mock(), Mock()
        self.stream._videoQ.put((8, old))
        self.widget.tick()
        media = Media.__new__(Media)
        media.ffmpeg = self.stream
        media.video = self.video
        media.status = "play"

        def seek(target):
            self.clock.getTime.return_value = target
            self.stream._videoQ.put((target, new))

        self.stream.seek.side_effect = seek
        media.seek(2)
        old.close.assert_called_once()
        self.assertEqual(len(self.widget.callbacks), 1)
        self.widget.tick()
        self.widget.configure.assert_called_once_with(image=new)
        self.assertEqual(media.status, "play")

    def test_stop_cancels_pending_frame_and_timer(self):
        image = Mock()
        self.stream._videoQ.put((8, image))
        self.widget.tick()
        self.video.stop()
        self.assertFalse(self.widget.callbacks)
        image.close.assert_called_once()
        self.assertIsNone(self.video._pending_frame)


if __name__ == '__main__':
    unittest.main()
