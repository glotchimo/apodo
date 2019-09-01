"""
apodo.server
~~~~~~~~~~~~

This module contains the core `Apodo` class.
"""

import sys
from email.utils import formatdate
from functools import partial
from multiprocessing import cpu_count

from .core.application import Application
from .net.request import Request
from .util.utils import bind, pause
from .workers.handler import RequestHandler
from .workers.necromancer import Necromancer


class Apodo(Application):
    """ Implements the `Apodo` class.

    This class subclasses the Application and thus Blueprint objects
    and controls all server instance operations.
    """

    current_time: str = formatdate(timeval=None, localtime=False, usegmt=True)

    def __init__(self) -> None:
        self.components.add(self)
        self.add_blueprint(self)
        self.initialized = True

    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        workers: int = None,
        block: bool = True,
    ) -> None:
        """ Runs the server.

        :param `host`: A `str` host to connect to.
        :param port: An `int` port to connect to.
        :param workers: An `int` indicating how many workers to spawn.
        :param `block`: A `bool` to start the pause/block sequence.
        """
        spawner = partial(RequestHandler, self, host, port)
        for _ in range(0, (workers or cpu_count() + 2)):
            worker = spawner()
            worker.start()
            self.workers.append(worker)

        necromancer = Necromancer(
            self.workers, spawner=spawner, interval=self.server_limits.worker_timeout
        )
        necromancer.start()

        bind(host, port)
        print("# Apodo # http://" + str(host) + ":" + str(port))
        self.running = True

        if block:
            try:
                pause()
                self.running = False
            except KeyboardInterrupt:
                self.clean_up()
