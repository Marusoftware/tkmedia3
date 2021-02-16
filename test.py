import media, tkinter, time
url="https://marusoftware.ddns.net/service/video/dA6rdGC9slWBThQ.mp4"
#url="/home/maruo/ビデオ/test.mp4"

def chg_state():
    if a.playback["state"] == "pause":
        a.playback["state"] == "play"
        b.playback["state"] == "play"
    else:
        a.playback["state"] == "pause"

root = tkinter.Tk()
root.f = tkinter.Label(root)
root.f.pack(fill="both", expand=True)
root.bt1 = tkinter.Button(root, text="Stop", command=chg_state)
a = media.Media(url)
b = media.Video(a)
a2 = media.Media(url)
c = media.Audio(a2)
b.Show(root.f, height=600, width=600, resize="aspect")
c.Play(syncV=b)
root.mainloop()