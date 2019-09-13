"""
apodo.util.workers.necromancer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the `Necromancer` class.
"""

import time
from threading import Thread
from typing import Callable

from ...core.application import Application


class Necromancer(Thread):
    """ Implements the `Necromancer` class.

    :param `app`: The current `Application` object.
    :param `spawn_fuction`: A function to call to spawn workers.
    :param `interval`: An `int` indicating the interval at which workers should be
                       spawned/resurrected.
    """

    def __init__(self, app, spawn_function: Callable, interval: int = 5):
        super().__init__()

        self.app = app
        self.spawn_function = spawn_function
        self.interval = interval
        self.must_work = True

    def run(self):
        while self.must_work:
            time.sleep(self.interval)

            living_workers = []
            for worker in self.app.workers:
                if not worker.is_alive():
                    worker = self.spawn_function()
                    worker.start()

                    living_workers.append(worker)
                else:
                    living_workers.append(worker)

            self.app.workers = living_workers
