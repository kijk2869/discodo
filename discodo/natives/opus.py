import array
import ctypes
import os
import sys

SAMPLING_RATE = int(os.getenv("SAMPLING_RATE", "48000"))
CHANNELS = int(os.getenv("CHANNELS", "2"))
FRAME_LENGTH = int(os.getenv("FRAME_LENGTH", "20"))
SAMPLE_SIZE = int(os.getenv("SAMPLE_SIZE", "4"))
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)
FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLES_PER_FRAME
EXPECTED_PACKETLOSS = int(os.getenv("EXPECTED_PACKETLOSS", "0"))
BITRATE = int(os.getenv("BITRATE", "128"))

_library = None

c_int_pointer = ctypes.POINTER(ctypes.c_int)
c_int16_pointer = ctypes.POINTER(ctypes.c_int16)
c_float_pointer = ctypes.POINTER(ctypes.c_float)


class EncoderStructure(ctypes.Structure):
    pass


EncoderStructurePointer = ctypes.POINTER(EncoderStructure)


def _errorLt(result, func, args):
    if result < 0:
        raise Exception
    return result


def _errorNe(result, func, args):
    ret = args[-1]._obj
    if ret.value != 0:
        raise Exception
    return result


exported_functions = {
    "opus_strerror": ([ctypes.c_int], ctypes.c_char_p, None),
    "opus_encoder_get_size": ([ctypes.c_int], ctypes.c_int, None),
    "opus_encoder_create": (
        [ctypes.c_int, ctypes.c_int, ctypes.c_int, c_int_pointer],
        EncoderStructurePointer,
        _errorNe,
    ),
    "opus_encode": (
        [
            EncoderStructurePointer,
            c_int16_pointer,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int32,
        ],
        ctypes.c_int32,
        _errorLt,
    ),
    "opus_encoder_ctl": (None, ctypes.c_int32, _errorLt),
    "opus_encoder_destroy": ([EncoderStructurePointer], None, None),
}


def loadOpus(name):
    global _library
    _library = loadLibopus(name)

    return _library is not None


def loadDefaultOpus():
    global _library
    try:
        if sys.platform == "win32":
            architecture = "x64" if sys.maxsize > 32 ** 2 else "x86"
            directory = os.path.dirname(os.path.abspath(__file__))
            _library = loadLibopus(
                os.path.join(directory, "bin", f"libopus-0.{architecture}.dll")
            )
        else:
            _library = loadLibopus(ctypes.util.find_library("opus"))
    except:
        _library = None

    return _library is not None


def loadLibopus(name):
    library = ctypes.cdll.LoadLibrary(name)

    for FuncName, Options in exported_functions.items():
        Func = getattr(library, FuncName)

        try:
            if Options[1]:
                Func.argtypes = Options[0]
            Func.restype = Options[1]
        except KeyError:
            pass

        try:
            if Options[2]:
                Func.errcheck = Options[2]
        except KeyError:
            pass

    return library


def isLoaded():
    global _library
    return _library is not None


ENCODER_CTL = {
    "OK": 0,
    "APPLICATION_AUDIO": 2049,
    "APPLICATION_VOIP": 2048,
    "APPLICATION_LOWDELAY": 2051,
    "CTL_SET_BITRATE": 4002,
    "CTL_SET_BANDWIDTH": 4008,
    "CTL_SET_FEC": 4012,
    "CTL_SET_PLP": 4014,
    "CTL_SET_SIGNAL": 4024,
}

BAND_CTL = {
    "narrow": 1101,
    "medium": 1102,
    "wide": 1103,
    "superwide": 1104,
    "full": 1105,
}

SIGNAL_CTL = {
    "auto": -1000,
    "voice": 3001,
    "music": 3002,
}


class Encoder:
    def __init__(self, application=ENCODER_CTL["APPLICATION_AUDIO"]):
        self.application = application

        if not isLoaded() and not loadDefaultOpus():
            raise ValueError

        self.state = self.createState()
        self.setBitrate(BITRATE)
        self.setFec(True)
        self.setExpectedPacketLoss(EXPECTED_PACKETLOSS)
        self.setBandwidth("full")
        self.setSignalType("auto")

    def createState(self):
        ret = ctypes.c_int()
        return _library.opus_encoder_create(
            SAMPLING_RATE, CHANNELS, self.application, ctypes.byref(ret)
        )

    def __del__(self):
        if hasattr(self, "state"):
            _library.opus_encoder_destroy(self.state)
            self.state = None

    def setBitrate(self, kbps):
        kbps = min(512, max(16, int(kbps)))

        _library.opus_encoder_ctl(
            self.state, ENCODER_CTL["CTL_SET_BITRATE"], kbps * 1024
        )

    def setBandwidth(self, req):
        if not req in BAND_CTL:
            raise KeyError

        _library.opus_encoder_ctl(
            self.state, ENCODER_CTL["CTL_SET_BANDWIDTH"], BAND_CTL[req]
        )

    def setSignalType(self, req):
        if not req in SIGNAL_CTL:
            raise KeyError

        _library.opus_encoder_ctl(
            self.state, ENCODER_CTL["CTL_SET_SIGNAL"], SIGNAL_CTL[req]
        )

    def setFec(self, enabled=True):
        _library.opus_encoder_ctl(
            self.state, ENCODER_CTL["CTL_SET_FEC"], 1 if enabled else 0
        )

    def setExpectedPacketLoss(self, percentage):
        _library.opus_encoder_ctl(self.state, ENCODER_CTL["CTL_SET_PLP"], percentage)

    def encode(self, Pcm, FrameSize=SAMPLES_PER_FRAME):
        max_length = len(Pcm)
        Pcm = ctypes.cast(Pcm, c_int16_pointer)
        Data = (ctypes.c_char * max_length)()

        Encoded = _library.opus_encode(self.state, Pcm, FrameSize, Data, max_length)

        return array.array("b", Data[:Encoded]).tobytes()
