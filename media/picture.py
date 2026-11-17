from tkinter import TclError
from typing import Literal

from PIL import Image, ImageOps, ImageTk


def _fit_size(source_size, bounds):
    width, height = source_size
    ratio = min(bounds[0] / width, bounds[1] / height)
    return max(1, int(width * ratio)), max(1, int(height * ratio))


def _set_widget_image(frame, frame_type, image, canvas_item=None):
    if frame_type == "label":
        frame.configure(image=image)
    elif canvas_item is None:
        canvas_item = frame.create_image(0, 0, anchor="nw", image=image)
    else:
        frame.itemconfigure(canvas_item, image=image)
    return canvas_item


class Picture:
    """Display a still image from a path, a binary file, or a Pillow image."""

    def __init__(self, source):
        if isinstance(source, Image.Image):
            self._image = ImageOps.exif_transpose(source)
        else:
            with Image.open(source) as image:
                self._image = ImageOps.exif_transpose(image)
        self._widget = None
        self._frame_type = None
        self._canvas_item = None
        self._photo = None

    def show(self, frame, frame_type: Literal["label", "canvas"] = "label", *, size=None):
        """Display the image, optionally fitting it within (width, height)."""
        if frame_type not in ("label", "canvas"):
            raise ValueError("frame_type must be 'label' or 'canvas'")
        if self._image is None:
            raise ValueError("Picture is closed")
        if size is not None:
            width, height = size
            if width < 1 or height < 1:
                raise ValueError("size must contain positive dimensions")
            with self._image.resize(_fit_size(self._image.size, size), Image.Resampling.LANCZOS) as image:
                photo = ImageTk.PhotoImage(image, master=frame)
        else:
            photo = ImageTk.PhotoImage(self._image, master=frame)
        if frame is not self._widget or frame_type != self._frame_type:
            self.hide()
        self._canvas_item = _set_widget_image(frame, frame_type, photo, self._canvas_item)
        self._widget = frame
        self._frame_type = frame_type
        self._photo = photo

    def hide(self):
        """Remove the displayed image and keep it available to show again."""
        if self._widget is not None:
            try:
                if self._canvas_item is not None:
                    self._widget.delete(self._canvas_item)
                elif str(self._widget.cget("image")) == str(self._photo):
                    self._widget.configure(image="")
            except TclError:
                pass  # The widget may already have been destroyed.
        self._widget = None
        self._canvas_item = None
        self._photo = None

    def close(self):
        """Remove the display and release the source image."""
        self.hide()
        if self._image is not None:
            self._image.close()
            self._image = None

