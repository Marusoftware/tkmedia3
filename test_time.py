import tkinter
from media import StopWatch

def update():
    l.configure(text=str(int(t.getTime())))
    root.after(1, update)

def Set():
    try:
        tm = int(e.get())
    except:
        pass
    else:
        t.setTime(tm)
        

root = tkinter.Tk()
t=StopWatch(error=0)
l=tkinter.Label(root)
l.pack()
update()
b1=tkinter.Button(root, text="start", command=t.start)
b1.pack()
b2=tkinter.Button(root, text="stop", command=t.stop)
b2.pack()
b3=tkinter.Button(root, text="set", command=Set)
b3.pack()
e = tkinter.Entry(root)
e.pack()
root.mainloop()