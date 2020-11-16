#archived
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
        self.lib.avformat_configuration.restype=ctypes.c_char_p
        #class AVClassCategory(ctypes.Structure):
        #    _fields_=[("",)]
        #class AVOption(ctypes.Structure):
        #    _fields_=[("",)]
        class AVClass(ctypes.Structure):
            _fields_=[("class_name",ctypes.c_char_p),("item_name",ctypes.c_char_p),
            ("version",ctypes.c_int),("log_level_offset_offset",ctypes.c_int),
            ("parent_log_context_offset",ctypes.c_int),("child_next",ctypes.c_void_p),("query_ranges",ctypes.c_int)]#,
            #("child_class_next",AVClass),("category",AVClassCategory),("get_category",AVClassCategory),
            #("option",AVOption),("child_class_iterate",AVClass)]
        self.AVClass = AVClass
        def _get_class():
            rt = self.AVClass()
            print(self.lib.avformat_get_class(ctypes.byref(rt)))
            return rt
        #get info
        self.version = self.lib.avformat_version()
        self.licence = str(self.lib.avformat_license())[2:-1]
        self.config = str(self.lib.avformat_configuration())[2:-1]
        self.avformat_get_class = _get_class

class UTIL():
    def __init__(self):
        lib = ctypes.util.find_library("avutil")
        self.lib = ctypes.cdll.LoadLibrary(lib)

class CODEC():
    def __init__(self):
        lib = ctypes.util.find_library("avcodec")
        self.lib = ctypes.cdll.LoadLibrary(lib)

class FILTER():
    def __init__(self):
        lib = ctypes.util.find_library("avfilter")
        self.lib = ctypes.cdll.LoadLibrary(lib)

class DEVICE():
    def __init__(self):
        lib = ctypes.util.find_library("avdevice")
        self.lib = ctypes.cdll.LoadLibrary(lib)