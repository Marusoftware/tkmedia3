import time
try:
    from .exception import WrongOrderError
except:
    from exception import WrongOrderError

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
            if self.error: raise WrongOrderError("Already Started.")
    def stop(self):
        if self.isStop:
            if self.error: raise WrongOrderError("Already Stoped.")
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
        stoped=self.isStop
        try:
            self.stop()
        except:
            pass
        self.time=t
        if not stoped:
            self.start()