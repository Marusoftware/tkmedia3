Tkinter media playback and still-image display for Python 3.9 and later.
The package is installed as `tkmedia` and imported as `media`.

## Installation

```sh
pip install tkmedia
```

The examples on this page describe the current repository. For features
that are newer than the published package, install from GitHub.

```sh
pip install git+https://github.com/Marusoftware/tkmedia3.git
```

Python must include Tkinter, and audio playback requires PortAudio. On
Debian and Ubuntu, install the system dependencies with
`sudo apt install python3-tk libportaudio2`.

Styled ASS/SSA subtitles also use the optional system libass shared library
(`libass9` on Debian and Ubuntu). Without it, subtitles display as plain
text. The renderer uses installed system fonts, so install fonts covering
the subtitle's language. Fonts attached to an MKV are currently unused.

## Play a video

This complete example opens a file, selects its first video and audio
tracks when present, and releases playback resources when the window closes.

```python
import tkinter as tk
from tkinter import filedialog

from media import Media

root = tk.Tk()
root.title("tkmedia")
path = filedialog.askopenfilename(parent=root)
if not path:
    root.destroy()
else:
    player = Media(path)
    label = tk.Label(root)
    label.pack(fill="both", expand=True)

    def close():
        player.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    streams = player.info["streams"]
    player.play(
        video=0 if streams["video"] else None,
        audio=0 if streams["audio"] else None,
        videoFrame=label,
        video_size=(640, 360),
    )
    root.mainloop()
```

The snippets below reuse `player` and `label`. Apply playback options to
the example's existing `play()` call, and configure widgets before entering
`root.mainloop()`.

Call `media.Media.play` once to start playback. Both `video` and `audio`
default to `None`, so select the tracks you want to play explicitly. A
video needs a Tkinter Label or Canvas. Audio-only playback can use
`player.play(audio=0)` without a video widget.

Tkinter's main loop must run for video to update. Create the player and
call its playback controls on the Tkinter thread. Opening a file,
buffering playback, and seeking can block that thread briefly.

### Playback controls

After starting playback, bind buttons or other application controls to
these methods.

| Operation | Call | Required state |
| --- | --- | --- |
| Pause | `player.pause()` | Playing |
| Resume | `player.resume()` | Paused after starting playback |
| Seek to 12.5 seconds | `player.seek(12.5)` | Playing |
| Stop playback | `player.stop()` | An open player |
| Release resources | `player.close()` | Call when finished, before destroying the window |

Seeking resumes playback at the requested position. To seek from a paused
state, resume first, seek, then pause again if needed. A seek discards
buffered audio and video and restores subtitles active at the target.
Use `player.stopwatch.getTime()` to read the current position in seconds.

`player.status` reflects the last playback control (`"play"`, `"pause"`,
`"stop"`, or `"close"`). It does not signal end of file. To replay a stopped
or exhausted file, close the player and create a new `media.Media` instance.
The capitalized controls (`Play`, `Pause`, `Resume`, `Seek`, `Stop`, `Close`)
are compatibility aliases for the lowercase methods.

## Select tracks and audio output

Inspect `player.info["streams"]` before selecting tracks. Each of its
`"video"`, `"audio"`, and `"subtitles"` entries is a list of dictionaries.
Track selectors use a zero-based position within the corresponding list.
The `"index"` value inside a dictionary is the container-wide stream index.

```python
for number, track in enumerate(player.info["streams"]["audio"]):
    print(number, track["codec_name"], track["lang"], track["channel_name"])
```

Video entries include `width`, `height`, and `fps`. Audio entries include
`sample_rate`, `channel`, and `channel_name`. Subtitle entries include
`codec_name`, `lang`, and `meta`. Language and duration information can be
missing. The container's `player.info["duration"]` is in microseconds.
Stream-level durations use each stream's `time_base`.

The default audio output is stereo. The decoder downmixes multichannel
input using its channel layout. Select an output device and layout when
starting playback.

```python
from media.audio import getDevices

print(getDevices())
player.play(audio=0, audioDevice=None, audio_layout="stereo")
```

`audioDevice=None` uses the sounddevice default output device. An integer
selects a device by its sounddevice index. Supported output layouts are
`"mono"`, `"stereo"`, `"5.1"`, and `"7.1"`; the selected device must support
the requested channel count.

## Fit video to a widget

`video_size=(640, 360)` fits decoded frames inside those bounds while
preserving their aspect ratio. It can enlarge or shrink the source.
Omit `video_size` to keep the source dimensions.

For a resizable area, cache the dimensions from Tkinter's `<Configure>`
event and pass a callable that reads the cached tuple.

```python
bounds = (640, 360)

def resized(event):
    global bounds
    bounds = (max(1, event.width), max(1, event.height))

label.bind("<Configure>", resized)
player.play(video=0, videoFrame=label, video_size=lambda: bounds)
```

The size callable runs on the decoder thread and must return positive
pixel dimensions. Access Tk widgets only from the Tkinter thread.
Already buffered frames retain their decoded size until displayed.

For Canvas output, pass `videoFrame=canvas, frame_type="canvas"`.
Images are drawn at `(0, 0)` with a northwest anchor. The Canvas image item
is reused between frames. The caller controls the widget dimensions.

## Display a still image

```python
from media import Picture

picture = Picture("photo.jpg")
picture.show(label, size=(640, 360))
# Or display in a Canvas
# picture.show(canvas, frame_type="canvas", size=(640, 360))
```

`media.Picture` accepts a path, a binary file object, or a Pillow image.
It loads its own image copy and applies EXIF orientation. Keep the
`Picture` instance while its image is visible. A supplied file object or
Pillow image remains owned by the caller.

The optional `size` fits the image inside positive pixel bounds while
preserving its aspect ratio. `media.Picture.show` can update the size or move
the image to another widget. A picture displays in one widget at a time.
Call `media.Picture.hide` to remove it while retaining the loaded image, or
`media.Picture.close` to also release the image. All display methods run on
the Tkinter thread. Animated images display their initially selected frame.

## Display subtitles

Select an embedded subtitle track when starting video playback.

```python
print(player.info["streams"]["subtitles"])
player.play(video=0, audio=0, videoFrame=label, subtitle=0)
```

For an external subtitle file, pass `subtitle_file` instead.

```python
player.play(video=0, videoFrame=label, subtitle_file="captions.srt")
```

Select at most one source. Subtitles require video output and follow the
playback clock during pause, resume, and seek. Both Label and Canvas
output support subtitles. External files use their first subtitle track
and are loaded into memory before playback.

| Subtitle format | Display |
| --- | --- |
| Text subtitles decoded by PyAV, including SRT and MP4 timed text | Plain text overlay at the bottom of the widget |
| ASS/SSA with system libass | Styles, positioning, and timed effects composited onto the video |
| ASS/SSA without libass | Plain text overlay |
| Blu-ray PGS and DVD/VobSub bitmap subtitles | Unsupported; selecting a track raises `media.exception.MediaFileError` |

Styled ASS/SSA uses the script's layout and system fonts. Font substitution
can change appearance. Text overlays wrap to the widget's width.

## API reference

Use `media.Media` for playback and `media.Picture` for still images.
The classes `media.Audio` and `media.Video` expose the lower-level playback
components used by `Media`. Audio device queries are in `media.audio`,
and playback exceptions are in `media.exception`.

`media.AudioFilter` and `media.VideoFilter` are experimental wrappers with
unfinished methods. Recording and writing media are also unfinished.
The supported examples use read mode and playback output.

## Build the documentation

From a checkout with the project dependencies installed, run the same
pdoc3 command used by GitHub Pages.

```sh
python -m pip install -r docs/requirements.txt
python -m pdoc --html --force --template-dir docs/templates --output-dir build/docs media
python -m http.server --directory build/docs/media 8000
```

Open [the local documentation](http://localhost:8000/).
Edit this guide in `docs/guide.md` and API descriptions in the corresponding
Python docstrings. pdoc3 includes this guide in the package's landing page.
