# tkmedia3

[![PyPI version](https://badge.fury.io/py/tkmedia.svg)](https://badge.fury.io/py/tkmedia)

Video and audio playback, still-image display, and text subtitles for
Tkinter on Python 3.9 and later. Install the package as `tkmedia` and
import it as `media`.

## Install

```sh
pip install tkmedia
```

For the latest repository features, including still images and subtitles,
install from GitHub.

```sh
pip install git+https://github.com/Marusoftware/tkmedia3.git
```

Python needs Tkinter, and audio playback needs PortAudio. On Debian and
Ubuntu, install `python3-tk` and `libportaudio2`. Styled ASS/SSA subtitles
also use the optional system libass library.

## Get started

```python
import tkinter as tk
from media import Media

root = tk.Tk()
label = tk.Label(root)
label.pack()
player = Media("movie.mp4")

def close():
    player.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close)
player.play(video=0, videoFrame=label, video_size=(640, 360))
root.mainloop()
```

This example selects the first video track. Add `audio=0` to also play the
first audio track when the file contains one.

The [documentation](https://marusoftware.github.io/tkmedia3/) contains the
usage guide and API reference. It covers playback controls, track selection,
audio devices, resizable video, pictures, subtitle formats, and current
limitations. The guide's source and local build instructions are in
[docs/guide.md](docs/guide.md).

## License

[MIT](LICENSE).
