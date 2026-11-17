[![PyPI version](https://badge.fury.io/py/tkmedia.svg)](https://badge.fury.io/py/tkmedia)

# tkmedia3
Tkinter/Python3 media support.

You can play video and audio, display still images in Tkinter, and overlay
text subtitles on video.

## Usage
see [docs](https://marusoftware.github.io/tkmedia3/master/index.html)(in progress) or test.py(mostly example)

(Hmm...? "No one decent material"..? Yeah...I see... It's sorry, I'll do it...)

### Video sizing

Pass `video_size=(640, 360)` to `Media.play()` to fit video within a
640 × 360 pixel area while preserving its aspect ratio. The decoded frame
is resized before it is queued for display.

For a resizable area, pass a callable that returns the latest
`(width, height)`. Update those dimensions from the widget's
`<Configure>` event and have the callable read the cached tuple. The
callable runs on the decoder thread. Leave `video_size` unset to keep
the source dimensions.

### Still images

```python
from media import Picture

picture = Picture("photo.jpg")
picture.show(label, size=(640, 360))
```

Keep the `Picture` instance while the image is visible. `Picture` accepts a
file path, a binary file object, or a Pillow image. Use
`picture.show(canvas, frame_type="canvas")` to draw at the canvas origin.
`picture.hide()` removes the image from the widget, and `picture.close()`
also releases the source image. Call these methods on the Tkinter thread.

### Subtitles

```python
from media import Media

player = Media("movie.mkv")
print(player.info["streams"]["subtitles"])
player.play(video=0, audio=0, videoFrame=label, subtitle=0)
```

`subtitle` selects a zero-based embedded subtitle track. For an external
file, pass `subtitle_file="captions.srt"` instead. Omit both to play without
subtitles. The overlay works with a Label or with a Canvas passed as
`videoFrame` alongside `frame_type="canvas"`.

Subtitles follow the playback clock during pause, resume, and seek. When
the system libass shared library is available, embedded ASS/SSA tracks and
external `.ass` and `.ssa` files render with their styles, positioning, and
timed effects. Rendering uses system fonts. Without libass, ASS/SSA uses
the plain-text overlay. Bitmap subtitle tracks such as PGS and VobSub
are unsupported.

## Install
Stable release:   
`pip install tkmedia`   
Dev:   
`pip install git+https://github.com/Marusoftware/tkmedia3.git`(not tested)   
