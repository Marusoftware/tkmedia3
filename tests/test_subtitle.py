import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from queue import SimpleQueue
from unittest.mock import Mock, patch

from media import Media
from media._ass import ass_library
from media.exception import MediaFileError
from media.subtitle import SubtitleOverlay


class SubtitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise unittest.SkipTest("ffmpeg is required to generate test media")
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.movie = Path(directory.name) / "movie.mkv"
        cls.subtitles = Path(directory.name) / "captions.srt"
        cls.styled = Path(directory.name) / "styled.ass"
        cls.styled.write_text(
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 32\nPlayResY: 32\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,sans-serif,12,&H000000FF,&H000000FF,&H00000000,&H00000000,"
            "0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,"
            r"{\an7\move(2,3,18,3,0,1000)\p1}m 0 0 l 7 0 7 7 0 7" "\n",
            encoding="utf-8",
        )
        cls.subtitles.write_text(
            "1\n00:00:01,200 --> 00:00:04,500\n<i>こんにちは</i>\nSecond line\n\n"
            "2\n00:00:05,000 --> 00:00:06,000\nNext\n",
            encoding="utf-8",
        )
        other = Path(directory.name) / "other.srt"
        other.write_text("1\n00:00:01,200 --> 00:00:04,500\nOther track\n", encoding="utf-8")
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=size=32x32:rate=10:duration=7",
            "-i", str(other), "-i", str(cls.subtitles), "-i", str(cls.styled),
            "-map", "0:v", "-map", "1:s", "-map", "2:s", "-map", "3:s",
            "-c:v", "mpeg4", "-g", "10", "-c:s", "copy",
            "-metadata:s:s:1", "language=jpn", str(cls.movie),
        ], check=True, timeout=20)

    def test_embedded_track_and_external_file_follow_playback_and_seek(self):
        for options in ({"subtitle": 1}, {"subtitle_file": self.subtitles}):
            with self.subTest(options=options):
                self.check_subtitle_playback(options)

    def check_subtitle_playback(self, options):
        canvas = Mock()
        canvas.winfo_width.return_value = 640
        canvas.create_image.return_value = 5
        clock = Mock()
        player = Media(str(self.movie))
        self.addCleanup(player.close)
        track = player.info["streams"]["subtitles"][1]
        self.assertEqual((track["lang"], track["codec_name"]), ("jpn", "srt"))

        with patch("media.subtitle.Label") as label, patch("media.video.ImageTk.PhotoImage"):
            overlay = label.return_value
            overlay.master = canvas
            player.play(video=0, videoFrame=canvas, frame_type="canvas", **options)
            player.video.stopwatch = clock

            def tick(time):
                clock.getTime.return_value = time
                canvas.after.call_args.args[1]()

            tick(0)
            canvas.create_image.assert_called_once()
            overlay.place.assert_not_called()
            tick(1.2)
            overlay.configure.assert_called_once_with(text="こんにちは\nSecond line", wraplength=628)
            player.pause()
            canvas.after_cancel.assert_called()
            overlay.place_forget.assert_not_called()
            player.resume()
            player.seek(3.5)
            overlay.place_forget.assert_called_once()
            tick(3.5)
            overlay.configure.assert_called_with(text="こんにちは\nSecond line", wraplength=628)
            self.assertGreater(canvas.itemconfigure.call_count, 0)
            canvas.create_image.assert_called_once()
            tick(4.5)
            self.assertEqual(overlay.place_forget.call_count, 2)
            tick(5)
            overlay.configure.assert_called_with(text="Next", wraplength=628)
            player.stop()
            self.assertEqual(overlay.place_forget.call_count, 3)
            player.close()
            overlay.destroy.assert_called_once()
            canvas.delete.assert_called_once_with(5)

    def test_invalid_subtitle_selection_is_reported_before_starting_playback(self):
        player = Media(str(self.movie))
        self.addCleanup(player.close)
        with self.assertRaisesRegex(MediaFileError, "Subtitle stream"):
            player.play(video=0, videoFrame=Mock(), subtitle=3)
        with self.assertRaises(ValueError):
            player.play(video=0, videoFrame=Mock(), subtitle=0, subtitle_file=self.subtitles)
        self.assertIsNone(player.ffmpeg.loader["thread"])

    def test_ass_position_color_and_motion_survive_seek(self):
        if ass_library() is None:
            self.skipTest("libass is not available")
        for options in ({"subtitle": 2}, {"subtitle_file": self.styled}):
            with self.subTest(options=options):
                self.check_ass_playback(options)

    def check_ass_playback(self, options):
        player = Media(str(self.movie))
        self.addCleanup(player.close)
        label = Mock()
        clock = Mock()
        with patch("media.video.ImageTk.PhotoImage", side_effect=lambda image, **kw: image.copy()):
            player.play(video=0, videoFrame=label, **options)
            player.video.stopwatch = clock

            def tick(time):
                clock.getTime.return_value = time
                label.after.call_args.args[1]()
                return label.configure.call_args.kwargs["image"]

            before = tick(0)
            self.assertEqual(before.getpixel((5, 6)), (0, 0, 0))
            player.seek(1)
            first = tick(1)
            self.assertEqual(first.getpixel((5, 6)), (255, 0, 0))
            moved = tick(1.5)
            self.assertEqual(moved.getpixel((5, 6)), (0, 0, 0))
            self.assertEqual(moved.getpixel((13, 6)), (255, 0, 0))
            player.seek(1.5)
            restored = tick(1.5)
            self.assertEqual(restored.getpixel((13, 6)), (255, 0, 0))
            player.pause()
            self.assertIs(label.configure.call_args.kwargs["image"], restored)
            player.resume()
            player.seek(4)
            ended = tick(4)
            self.assertEqual(ended.getpixel((21, 6)), (0, 0, 0))
            player.close()


class SubtitleOverlayTests(unittest.TestCase):
    def test_overlapping_cues_expire_independently(self):
        queue = SimpleQueue()
        queue.put((2, 5, "Second"))
        queue.put((1, 3, "First"))
        frame = Mock()
        frame.winfo_width.return_value = 320
        with patch("media.subtitle.Label") as label:
            label.return_value.master = frame
            overlay = SubtitleOverlay(frame, queue)
            overlay.update(2)
            label.return_value.configure.assert_called_with(text="First\nSecond", wraplength=308)
            overlay.update(3)
            label.return_value.configure.assert_called_with(text="Second", wraplength=308)
            overlay.update(5)
            label.return_value.place_forget.assert_called_once()
