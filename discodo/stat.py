import os
import psutil

Process = psutil.Process(os.getpid())

def getProcessMemory():
    return round(Process.memory_info().rss / 1e+6)

def getProcessCpu():
    return Process.cpu_percent()

def getTotalCpu():
    return psutil.cpu_percent()

def getMemory():
    return round(psutil.virtual_memory().total / 1e+6)

def getCpuCount():
    return psutil.cpu_count()

def getStat():
    return {
        'UsedMemory': getProcessMemory(),
        'TotalMemory': getMemory(),
        'ProcessLoad': getProcessCpu(),
        'TotalLoad': getTotalCpu(),
        'Cores': getCpuCount()
    }