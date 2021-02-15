import media, tkinter
url="https://marusoftware.ddns.net/service/video/dA6rdGC9slWBThQ.mp4"
#url="/home/maruo/ビデオ/test.mp4"
root = tkinter.Tk()
root.f = tkinter.Label(root)
root.f.pack(fill="both", expand=True)
a = media.Media(url)
b = media.Video(a)
b.Show(root.f, height=600, width=600, resize=False)
a2 = media.Media(url)
c = media.Audio(a2)
c.Play(syncV=b)
root.mainloop()