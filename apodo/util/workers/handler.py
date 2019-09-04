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
    """

    def __init__(self, app: Application, bind: str, port: int, socket=None):
        super().__init__()

        self.app = app
        self.bind = bind
        self.port = port
        self.daemon = True
        self.socket = socket

    def run(self):
        """ Runs the server. """
        if not self.socket:
            self.socket = socket()

            self.socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)

            self.socket.bind((self.bind, self.port))

        loop = asyncio.new_event_loop()
        loop.app = self.app
        self.app.loop = loop
        self.app.components.add(loop)
        asyncio.set_event_loop(loop)

        self.app.reaper = Reaper(app=self.app)
        self.app.reaper.start()

        self.app.initialize()

        handler = partial(self.app.handler, app=self.app, loop=loop, worker=self)
        ss = loop.create_server(
            handler, sock=self.socket, reuse_port=True, backlog=1000
        )

        loop.run_until_complete(ss)

        async def stop_server(timeout=30):
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

            loop.stop()

        def handle_kill_signal():
            """ Closes the socket and stops the server. """
            self.socket.close()
            loop.create_task(stop_server(10))

        try:
            loop.add_signal_handler(signal.SIGTERM, handle_kill_signal)
            loop.run_forever()
        except (SystemExit, KeyboardInterrupt):
            loop.stop()
