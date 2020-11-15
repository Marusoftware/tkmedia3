import ctypes
import ctypes.util

class FORMAT():
    def __init__(self):
        lib = ctypes.util.find_library("avformat")
        self.lib = ctypes.cdll.LoadLibrary(lib)
        #init
        self.lib.avformat_network_init()
        self.lib.avformat_version.restype=ctypes.c_uint
        self.lib.avformat_license.restype=ctypes.c_char_p
        #get info
        self.version = self.lib.avformat_version()
        self.licence = self.lib.avformat_license()

class UTIL():
    def __init__(self):
        lib = ctypes.util.find_library("avutil")
        self.lib = ctypes.cdll.LoadLibrary(lib)
        #self.lib.avformat_network_init()
        #self.avio_enum_protocols = self.lib.avio_enum_protocols

class CODEC():
    def __init__(self):
        lib = ctypes.util.find_library("avcodec")
        self.lib = ctypes.cdll.LoadLibrary(lib)
        #self.lib.avformat_network_init()
        #self.avio_enum_protocols = self.lib.avio_enum_protocols

class FILTER():
    def __init__(self):
        lib = ctypes.util.find_library("avfilter")
        self.lib = ctypes.cdll.LoadLibrary(lib)

class DEVICE():
    def __init__(self):
        lib = ctypes.util.find_library("avdevice")
        self.lib = ctypes.cdll.LoadLibrary(lib)