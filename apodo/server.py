"""
apodo.server
~~~~~~~~~~~~

This module contains the core `Apodo` class.
"""

from email.utils import formatdate
from functools import partial
from multiprocessing import cpu_count

from .net.connection import Connection
from .util.utils import bind, pause
from .util.workers.handler import Handler
from .util.workers.necromancer import Necromancer


class Server:
    """ Implements the `Server` class.

    This class controls the high-level operations of the server,
    and contains other attribute/instance data.
    """

    current_time: str = formatdate(timeval=None, localtime=False, usegmt=True)

    def __init__(self):
        super().__init__()
        self.initialized = True

        self.handler = Connection

        self.connections = set()
        self.workers = []

        self.loop = None

        self.initialized = False
        self.running = False

    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        workers: int = None,
        block: bool = True,
    ):
        spawner = partial(Handler, self, host, port)
        for _ in range(0, (workers or cpu_count())):
            worker = spawner()
            worker.start()
            self.workers.append(worker)

        Necromancer(self.workers, spawner=spawner).start()

        bind(host, port)
        print("Apodo - Running on http://" + str(host) + ":" + str(port))
        self.running = True

        if block:
            try:
                pause()
                self.running = False
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """ Kills all active worker processes. """
        for process in self.workers:
            process.terminate()

        self.running = False
