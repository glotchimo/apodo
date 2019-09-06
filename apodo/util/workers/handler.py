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

from ...core.application import Application
from .reaper import Reaper


class Handler(Process):
    """ Implements the `Handler` class.

    This class controls the socket-level operations around request handling.

    :param `app`: The current `Application` object.
    :param `bind`: A `str` host to bind to.
    :param `port`: A `int` port to bind to.
    :param `socket`: (optional) An existing `socket` to use.
    """

    def __init__(self, app: Application, host: str, port: int, socket=None):
        super().__init__()

        self.app = app
        self.host = host
        self.port = port
        self.daemon = True
        self.socket = socket

    def run(self):
        self._bind_socket()
        self._create_loop()
        self._create_server()

        try:
            self.app.loop.add_signal_handler(signal.SIGTERM, self._handle_kill)
            self.app.loop.run_forever()
        except (SystemExit, KeyboardInterrupt):
            self.app.loop.stop()

    def _create_socket(self):
        if not self.socket:
            self.socket = socket()

            self.socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)

            self.socket.bind((self.host, self.port))

    def _create_loop(self):
        loop = asyncio.new_event_loop()

        loop.app = self.app
        self.app.loop = loop

        asyncio.set_event_loop(loop)

    def _create_server(self):
        self.app.reaper = Reaper(app=self.app)
        self.app.reaper.start()

        self.app.initialize()

        handler = partial(
            self.app.handler, app=self.app, loop=self.app.loop, worker=self
        )
        server = self.app.loop.create_server(
            handler, sock=self.socket, reuse_port=True, backlog=1000
        )

        self.app.loop.run_until_complete(server)

    async def _stop_server(self, timeout=30):
        """ Runs a soft-to-hard stop on active connections. """
        self.app.reaper.has_to_work = False

        for connection in self.app.connections.copy():
            connection.stop()

        while timeout:
            all_closed = True

            for connection in self.app.connections:
                if not connection.is_closed():
                    all_closed = False
                    break

            if all_closed:
                break

            timeout -= 1
            await asyncio.sleep(1)

        self.app.loop.stop()

    def _handle_kill(self):
        self.socket.close()
        self.app.loop.create_task(self._stop_server(10))
