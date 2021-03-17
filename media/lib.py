import time
import platform
import tkinter.filedialog as _fd1
fdmode=0
if platform.system() in ["Linux", "Darwin"]:
    try:
        import tkfilebrowser as _fd2
    except:
        fdmode=0
    else:
        fdmode=1
else:
    try:
        import tkfilebrowser as _fd2
    except:
        fdmode=0
    else:
        fdmode=1

class StopWatch():
    def __init__(self, error=True):
        self.start_time = 0
        self.stop_time = 0
        self.time = 0
        self.isStop = True
        self.error = error
    def start(self):
        if self.isStop:
            self.start_time = time.time() 
            self.isStop=False
        else:
            if self.error: raise AttributeError("Already Started.")
    def stop(self):
        if self.isStop:
            if self.error: raise AttributeError("Already Stoped.")
        else:
            self.time+=time.time()-self.start_time
            self.isStop=True
    def clear(self):
        self.time = 0
        self.stop_time=0
        self.isStop=True
    def getTime(self):
        if self.isStop:
            return self.time
        else:
            return self.time+(time.time()-self.start_time)
    def setTime(self, t):
        if self.isStop:
            self.time = t

#dialogs
def askdirectory(fd=None, **argv):
    if fd == None: fd = fdmode
    if fd:
        return _fd2.askopendirname(**argv)
    else:
        return _fd1.askdirectory(**argv)

def askopenfilename(fd=None, **argv):
    if fd == None: fd = fdmode
    if platform.system() == "Darwin" and "filetypes" in argv:
        if len(argv["filetypes"])==1 and argv["filetypes"][0][1]=="*.*" and fdmode:
            return _fd2.askopenfilename(**argv)
        else:
            return _fd1.askopenfilename(**argv)
    elif fd:
        try:
            return _fd2.askopenfilename(**argv)
        except:
            return _fd1.askopenfilename(**argv)
    else:
        return _fd1.askopenfilename(**argv)
def askopenfilenames(fd=None, **argv):
    if fd == None: fd = fdmode
    if platform.system() == "Darwin":
        #load_fd2()
        return _fd2.askopenfilenames(**argv)
    if fd:
        return _fd2.askopenfilenames(**argv)
    else:
        return _fd1.askopenfilenames(**argv)
def asksaveasfilename(fd=None, **argv):
    if fd == None: fd = fdmode
    if fd:
        return _fd2.asksaveasfilename(**argv)
    else:
        return _fd1.asksaveasfilename(**argv)
        