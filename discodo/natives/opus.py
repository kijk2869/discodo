import os
import sys
import ctypes

SAMPLING_RATE = os.getenv('SAMPLING_RATE', 48000)
CHANNELS = os.getenv('CHANNELS', 2)
FRAME_LENGTH = os.getenv('FRAME_LENGTH', 20)
SAMPLE_SIZE = os.getenv('SAMPLE_SIZE', 4)
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)
FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLES_PER_FRAME
EXPECTED_PACKETLOSS = os.getenv('EXPECTED_PACKETLOSS', 0.0)
BITRATE = os.getenv('BITRATE', 128)

_library = None

c_int_pointer = ctypes.POINTER(ctypes.c_int)
c_int16_pointer = ctypes.POINTER(ctypes.c_int16)
c_float_pointer = ctypes.POINTER(ctypes.c_float)


class EncoderStructure(ctypes.Structure):
    pass


EncoderStructurePointer = ctypes.POINTER(EncoderStructure)

def _errorNe(result, func, args):
    if result < 0:
        raise
    return result

def _errorLt(result, func, args):
    ret = args[-1]._obj
    if ret.value != 0:
        raise
    return result

exported_functions = {
    'opus_strerror': ([ctypes.c_int], ctypes.c_char_p, None),
    'opus_encoder_get_size': ([ctypes.c_int], ctypes.c_int, None),
    'opus_encoder_create': ([ctypes.c_int, ctypes.c_int, ctypes.c_int, c_int_pointer], EncoderStructurePointer, _errorNe),
    'opus_encode': ([EncoderStructurePointer, c_int16_pointer, ctypes.c_int, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int32, _errorLt),
    'opus_encoder_ctl': (None, ctypes.c_int32, _errorLt),
    'opus_encoder_destroy': ([EncoderStructurePointer], None, None)
}


def loadOpus(name):
    global _library
    _library = loadLibopus(name)

    return _library is not None


def loadDefaultOpus():
    global _library
    try:
        if sys.platform == 'win32':
            architecture = 'x64' if sys.maxsize > 32**2 else 'x86'
            directory = os.path.dirname(os.path.abspath(__file__))
            _library = loadLibopus(os.path.join(
                directory, 'bin', f'libopus-0.{architecture}.dll'))
        else:
            _library = loadLibopus(ctypes.util.find_library('opus'))
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
