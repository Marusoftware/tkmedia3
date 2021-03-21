import sounddevice

def getDevices(iterable):
    return sounddevice.DeviceList(iterable=iterable)
def getVersion():
    return sounddevice.get_portaudio_version()