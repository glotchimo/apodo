"""
apodo.util.workers.reaper
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the `Reaper` class.
"""

import os
import signal
import time
from datetime import datetime, timezone
from email.utils import formatdate
from threading import Thread

from apodo.server import Server
from apodo.net.connection import STATUS_PENDING, STATUS_PROCESSING


class Reaper(Thread):
    """ Implements the `Reaper` class.

    This class automatically kills/cleans idle/dead connections.

    :param server: The current `Server` instance.
    """

    def __init__(self, server: Server):
        super().__init__()

        self.server: Server = server
        self.connections: set = self.server.connections

        self.keep_alive_timeout: int = self.server.server_limits.keep_alive_timeout
        self.worker_timeout: int = self.server.server_limits.worker_timeout

        self.has_to_work: bool = True

    def run(self):
        count = 0
        while self.has_to_work:
            count += 1

            self.server.current_time = datetime.time().isoformat()

            if self.keep_alive_timeout > 0:
                if count % self.keep_alive_timeout == 0:
                    self._kill_idles()

            if count % self.worker_timeout == 0:
                self._check_worker()

            time.sleep(1)

    def _check_connections(self):
        """ Checks potentially stuck connections, hard-stops them. """
        now = time.time()
        for connection in self.server.connections.copy():
            if (
                connection.get_status() == STATUS_PROCESSING
                and now - connection.get_last_task_time() >= self.worker_timeout
            ):
                os.kill(os.getpid(), signal.SIGKILL)

    def _kill_idles(self):
        """ Checks potentially idle connections, soft-stops them. """
        now = time.time()
        for connection in self.connections.copy():
            if connection.get_status() == STATUS_PENDING and (
                now - connection.get_last_task_time() > self.keep_alive_timeout
            ):
                connection.stop()

    @staticmethod
    async def kill_connections(connections: list):
        for connection in connections:
            connection.transport.clean_up()
