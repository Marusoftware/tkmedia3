# import media, tkinter, time, pprint#, tkinter.filedialog
# from media.lib import askopenfilename
# #url="https://marusoftware.ddns.net/service/video/dA6rdGC9slWBThQ.mp4"

# def chg_state():
#     if (en["Video"] and v.playback["state"] == "pause") or (en["Audio"] and a.playback["state"] == "pause"):
#         if en["Video"]:
#             v.playback["state"] = "play"
#             if v.finished: m.Seek(0)
#         if en["Audio"]:
#             a.playback["state"] = "play"
#             if a.finished: m2.Seek(0)
#         root.bt1.configure(text="Pause")
#     else:
#         if en["Video"]:
#             v.playback["state"] = "pause"
#         if en["Audio"]:
#             a.playback["state"] = "pause"
#         root.bt1.configure(text="Play")
# def finish():
#     if en["Video"]:
#         v.Stop()
#     if en["Audio"]:
#         a.Stop()
#     root.destroy()

# def seek():
#     point=int(root.e.get())
#     if en["Video"]: m.Seek(point)
#     if en["Audio"]: m2.Seek(point)

# root = tkinter.Tk()
# url=askopenfilename()
# root.f = tkinter.Label(root)
# root.f.pack(fill="both", expand=True)
# root.bt1 = tkinter.Button(root, text="Pause", command=chg_state)
# root.bt1.pack()
# root.bt2 = tkinter.Button(root, text="Exit", command=finish)
# root.bt2.pack()
# root.e = tkinter.Entry(root)
# root.e.pack()
# root.bt3 = tkinter.Button(root, text="Seek", command=seek)
# root.bt3.pack()
# m = media.Media(url)
# en = {"Video":None,"Audio":None}
# try:
#     v = media.Video(m)
# except media.MediaFileError:
#     en["Video"]=False
# else:
#     en["Video"]=True
# print("Video:",en["Video"])
# m2 = media.Media(url)
# try:
#     a = media.Audio(m2)
# except:
#     en["Audio"]=False
# else:
#     en["Audio"]=True
# print("Audio:",en["Audio"])
# pprint.pprint(m.info)
# if en["Video"]:v.Show(root.f, height=900, width=1920, resize="aspect")
# if en["Audio"]:
#     if en["Video"]:
#         a.Play(syncV=v)
#     else:
#         a.Play()
# try:
#     root.mainloop()
# except KeyboardInterrupt:
#     v.Stop()
#     a.Stop()
#     root.destroy()
import media, tkinter, tkinter.filedialog as fd, os
root=tkinter.Tk()
root.menu=tkinter.Menu(root)
root.config(menu=root.menu)
a = media.Media(fd.askopenfilename(initialdir=os.path.expanduser("~")),"r")
l = tkinter.Label(root)
l.pack(fill="both", expand="true")
a.Play(audio=0, video=0, audioDevice="default", videoFrame=l)
root.mainloop()