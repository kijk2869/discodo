import os
import threading

import psutil

Process = psutil.Process(os.getpid())


def getProcessMemory():
    return round(Process.memory_info().rss / 1e6)


def getProcessCpu():
    return Process.cpu_percent()


def getProcessThreads():
    return threading.active_count()


def getTotalCpu():
    return psutil.cpu_percent()


def getMemory():
    return round(psutil.virtual_memory().total / 1e6)


def getCpuCount():
    return psutil.cpu_count()


def getNetworkInbound():
    return round(psutil.net_io_counters().bytes_recv / 1e6)


def getNetworkOutbound():
    return round(psutil.net_io_counters().bytes_sent / 1e6)


def getStat():
    return {
        "UsedMemory": getProcessMemory(),
        "TotalMemory": getMemory(),
        "ProcessLoad": getProcessCpu(),
        "TotalLoad": getTotalCpu(),
        "Cores": getCpuCount(),
        "Threads": getProcessThreads(),
        "NetworkInbound": getNetworkInbound(),
        "NetworkOutbound": getNetworkOutbound(),
    }
