import media, tkinter, tkinter.filedialog as fd, os

def stop():
    a.Pause()
    root.b1.configure(text="Play", command=play)
def play():
    a.Resume()
    root.b1.configure(text="Stop", command=stop)
root=tkinter.Tk()
a = media.Media(fd.askopenfilename(initialdir=os.path.expanduser("~")),"r")
l = tkinter.Label(root)
l.pack(fill="both", expand="true")
root.b1 = tkinter.Button(text="Stop", command=stop)
root.b1.pack()
root.b2 = tkinter.Button(text="Close", command=a.Close)
root.b2.pack()
a.Play(audio=0, video=0, audioDevice="default", videoFrame=l)
root.mainloop()