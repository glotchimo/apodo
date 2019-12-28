"""
apodo.util.workers.handler
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the `Handler` class.
"""

import asyncio
import signal
from functools import partial
from multiprocessing import Process
from socket import (
    IPPROTO_TCP,
    SO_REUSEADDR,
    SO_REUSEPORT,
    SOL_SOCKET,
    TCP_NODELAY,
    socket,
)

from apodo.server import Server
from apodo.util.workers.reaper import Reaper


class Handler(Process):
    """ Implements the `Handler` class.

    This class controls the socket-level operations around request handling.

    :param server: The current `Server` object.
    :param host: A `str` host to bind to.
    :param port: A `int` port to bind to.
    :param sock: (optional) An existing `socket` to use.
    """

    def __init__(self, server: Server, host: str, port: int, sock=None):
        super().__init__()

        self.server = server
        self.host = host
        self.port = port
        self.daemon = True
        self.socket = sock

    def run(self):
        if not self.socket:
            self._bind_socket()

        self._create_loop()
        self._start_server()

        try:
            self.server.loop.add_signal_handler(signal.SIGTERM, self._handle_kill)
            self.server.loop.run_forever()
        except (SystemExit, KeyboardInterrupt):
            self.server.loop.stop()

    def _bind_socket(self):
        self.socket = socket()

        self.socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)

        self.socket.bind((self.host, self.port))

    def _create_loop(self):
        loop = asyncio.new_event_loop()

        loop.server = self.server
        self.server.loop = loop

        asyncio.set_event_loop(loop)

    def _start_server(self):
        self.server.reaper = Reaper(server=self.server)
        self.server.reaper.start()

        self.server.__init__()

        handler = partial(
            self.server.handler, server=self.server, loop=self.server.loop, worker=self
        )
        server = self.server.loop.create_server(
            handler, sock=self.socket, reuse_port=True, backlog=1000
        )

        self.server.loop.run_until_complete(server)

    async def _stop_server(self, timeout=30):
        """ Runs a soft-to-hard stop on active connections. """
        self.server.reaper.has_to_work = False

        for connection in self.server.connections.copy():
            connection.stop()

        while timeout:
            all_closed = True

            for connection in self.server.connections:
                if not connection.is_closed():
                    all_closed = False
                    break

            if all_closed:
                break

            timeout -= 1
            await asyncio.sleep(1)

        self.server.loop.stop()

    def _handle_kill(self):
        self.socket.close()
        self.server.loop.create_task(self._stop_server(10))
