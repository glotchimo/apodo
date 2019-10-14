"""
apodo.server
~~~~~~~~~~~~

This module contains the core `Apodo` class.
"""

from email.utils import formatdate
from functools import partial
from multiprocessing import cpu_count

from .core.application import Application
from .util.utils import bind, pause
from .util.workers.handler import Handler
from .util.workers.necromancer import Necromancer


class Apodo(Application):
    """ Implements the `Apodo` class.

    This class subclasses the Application and thus Blueprint objects
    and controls all server instance operations.
    """

    current_time: str = formatdate(timeval=None, localtime=False, usegmt=True)

    def __init__(self):
        super().__init__()

        self.add_blueprint(self)
        self.initialized = True

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
        print("# Apodo # http://" + str(host) + ":" + str(port))
        self.running = True

        if block:
            try:
                pause()
                self.running = False
            except KeyboardInterrupt:
                self.clean_up()
