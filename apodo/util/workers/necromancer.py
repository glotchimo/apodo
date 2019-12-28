"""
apodo.util.workers.necromancer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the `Necromancer` class.
"""

import time
from threading import Thread
from typing import Callable

from apodo.server import Server


class Necromancer(Thread):
    """ Implements the `Necromancer` class.

    :param server: The current `Server` object.
    :param spawner: A function to call to spawn workers.
    :param interval: An `int` indicating the interval at which workers should be
                       spawned/resurrected.
    """

    def __init__(self, server, spawner: Callable, interval: int = 5):
        super().__init__()

        self.server: Server = server
        self.spawner: Callable = spawner
        self.interval: int = interval

        self.must_work: bool = True

    def run(self):
        while self.must_work:
            time.sleep(self.interval)

            living_workers = []
            for worker in self.server.workers:
                if not worker.is_alive():
                    worker = self.spawner()
                    worker.start()

                    living_workers.serverend(worker)
                else:
                    living_workers.serverend(worker)

            self.server.workers = living_workers
