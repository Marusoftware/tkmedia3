import media, tkinter
root = tkinter.Tk()
root.f = tkinter.Label(root)
root.f.pack(fill="both", expand=True)
a = media.Media("/home/maruo/ビデオ/test.mp4")
b = media.Video(a)
b.Show(root.f, height=600, width=600)
root.mainloop()