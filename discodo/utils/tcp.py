import socket
from contextlib import closing


def getFreePort() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        _, port = sock.getsockname()

    return port
