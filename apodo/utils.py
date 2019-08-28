"""
apodo.utils
~~~~~~~~~~~

This module contains assorted utility classes and methods.
"""

import os
import time
import socket
import signal


def bind(host: str, port: int, timeout: int = 10) -> None:
    """ Binds to socket when available.

    :param `host`: A `str` host to connect to.
    :param `port`: An `int` TCP port to connect to.
    :param `timeout`: An `int` count of seconds to wait before timing out.
    """
    sock = socket.socket()
    sock.settimeout(timeout)

    while timeout > 0:
        start = time.time()

        try:
            sock.connect((host, port))
            sock.close()
            break
        except OSError:
            time.sleep(0.001)
            timeout -= time.time() - start
    else:
        sock.close()
        raise TimeoutError("Server is taking too long to get online.")


def pause() -> None:
    """ Pauses the process until a signal is received. """
    if os.name == "nt":
        while True:
            time.sleep(60)
    else:
        signal.pause()
