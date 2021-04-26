import os
import threading

import psutil

Process = psutil.Process(os.getpid())


def getProcessMemory():
    """Get process memory usage. the unit is mega bytes.

    :rtype: int"""

    return round(Process.memory_info().rss / 1e6)


def getProcessCpu():
    """Get process cpu usage. the unit is percent.

    :rtype: int"""

    return Process.cpu_percent()


def getProcessThreads():
    """Get process thread count.

    :rtype: int"""

    return threading.active_count()


def getTotalCpu():
    """Get system cpu usage. the unit is percent.

    :rtype: int"""

    return psutil.cpu_percent()


def getMemory():
    """Get system memory usage. the unit is mega bytes.

    :rtype: int"""

    return round(psutil.virtual_memory().total / 1e6)


def getCpuCount():
    """Get cpu core count.

    :rtype: int"""

    return psutil.cpu_count()


def getNetworkInbound():
    """Get network inbound counters. the unit is mega bytes.

    :rtype: int"""

    return round(psutil.net_io_counters().bytes_recv / 1e6)  # type: ignore


def getNetworkOutbound():
    """Get network outbound counters. the unit is mega bytes.

    :rtype: int"""

    return round(psutil.net_io_counters().bytes_sent / 1e6)  # type: ignore


def getStatus():
    """Represents all information to dictionary

    :rtype: dict"""

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
