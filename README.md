[![PyPI version](https://badge.fury.io/py/tkmedia.svg)](https://badge.fury.io/py/tkmedia)

# tkmedia3
Tkinter/Python3 media support.

You can play video and audio on tkinter Frame/Canvas.

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

## Install
Stable release:   
`pip install tkmedia`   
Dev:   
`pip install git+https://github.com/Marusoftware/tkmedia3.git`(not tested)   
