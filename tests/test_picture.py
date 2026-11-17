import io
import unittest
from unittest.mock import Mock, patch

from PIL import Image

from media import Picture


class PictureTests(unittest.TestCase):
    def test_file_lifetime_resize_and_move_to_canvas(self):
        source = io.BytesIO()
        with Image.new("RGBA", (100, 50), (255, 0, 0, 128)) as image:
            image.save(source, format="PNG")
        picture = Picture(source)
        source.close()
        self.addCleanup(picture.close)
        label = Mock()
        canvas = Mock()
        canvas.create_image.return_value = 12
        images = []

        def make_photo(image, *, master):
            images.append((image.size, image.getpixel((0, 0))))
            return f"photo{len(images)}"

        with patch("media.picture.ImageTk.PhotoImage", side_effect=make_photo):
            picture.show(label, size=(40, 40))
            label.configure.assert_called_once_with(image="photo1")
            label.cget.return_value = "photo1"
            picture.show(canvas, frame_type="canvas")
            picture.show(canvas, frame_type="canvas", size=(20, 20))
        self.assertEqual(images, [
            ((40, 20), (255, 0, 0, 128)),
            ((100, 50), (255, 0, 0, 128)),
            ((20, 10), (255, 0, 0, 128)),
        ])
        label.configure.assert_called_with(image="")
        canvas.create_image.assert_called_once_with(0, 0, anchor="nw", image="photo2")
        canvas.itemconfigure.assert_called_once_with(12, image="photo3")
        picture.hide()
        picture.close()
        canvas.delete.assert_called_once_with(12)

    def test_close_leaves_caller_owned_pillow_image_open(self):
        with Image.new("RGB", (10, 10), "blue") as image:
            picture = Picture(image)
            picture.close()
            self.assertEqual(image.getpixel((0, 0)), (0, 0, 255))
            with self.assertRaisesRegex(ValueError, "closed"):
                picture.show(Mock())
