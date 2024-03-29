import media, tkinter, tkinter.filedialog as fd, os
import faulthandler; faulthandler.enable()
import logging
logging.basicConfig()

def stop():
    a.Pause()
    root.b1.configure(text="Play", command=play)
def play():
    a.Resume()
    root.b1.configure(text="Stop", command=stop)
def seek():
    a.Seek(int(root.sp.get()))
def close():
    a.Close()
    root.destroy()
root=tkinter.Tk()
a = media.Media(fd.askopenfilename(initialdir=os.path.expanduser("~")),"r")
l = tkinter.Label(root)
l.pack(fill="both", expand="true")
root.b1 = tkinter.Button(text="Stop", command=stop)
root.b1.pack()
root.b2 = tkinter.Button(text="Close", command=close)
root.b2.pack()
root.sp=tkinter.Spinbox(root, from_ = 1, to = 10, increment = 1, width = 10)
root.sp.pack()
root.b2 = tkinter.Button(text="Seek", command=seek)
root.b2.pack()
a.Play(audio=0, video=0, audioDevice=None, videoFrame=l)
root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()
a.Close()