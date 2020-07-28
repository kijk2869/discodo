import audioop
import math
import sys

import numpy as np


def volumeDetect(Data):
    volume = audioop.rms(Data, 2)
    return volume


def volumeNorm(Data):
    if not Data:
        return

    try:
        detected = volumeDetect(Data)
        sys.stdout.write("" + str(detected) + "|" + "#" * round(detected / 150) + "\n")
        a = 7000 / detected
        print(a)
        _Data = audioop.mul(Data, 2, a)
        b = volumeDetect(Data)
        sys.stdout.write("->" + str(b) + "|" + "#" * round(b / 150) + "\n")
        return _Data
    except:
        return Data
