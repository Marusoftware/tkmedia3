import time
import platform
import tkinter.filedialog as _fd1
if platform.system() == "Linux":
    import tkfilebrowser as _fd2
else:
    try:
        import tkfilebrowser as _fd2
    except:
        pass

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

#default setting
if platform.system() == "Linux":
    mode = 1
else:
    mode = 0

#dialogs
def askdirectory(fd=None, **argv):
    if fd == None: fd = mode
    if fd:
        return _fd2.askopendirname(**argv)
    else:
        return _fd1.askdirectory(**argv)

def askopenfilename(fd=None, **argv):
    if fd == None: fd = mode
    if platform.system() == "Darwin":
        #load_fd2()
        return _fd2.askopenfilename(**argv)
    if fd:
        return _fd2.askopenfilename(**argv)
    else:
        return _fd1.askopenfilename(**argv)
def askopenfilenames(fd=None, **argv):
    if fd == None: fd = mode
    if platform.system() == "Darwin":
        #load_fd2()
        return _fd2.askopenfilenames(**argv)
    if fd:
        return _fd2.askopenfilenames(**argv)
    else:
        return _fd1.askopenfilenames(**argv)
def asksaveasfilename(fd=None, **argv):
    if fd == None: fd = mode
    if fd:
        return _fd2.asksaveasfilename(**argv)
    else:
        return _fd1.asksaveasfilename(**argv)
        