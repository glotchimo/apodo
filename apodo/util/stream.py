"""
apodo.util.stream
~~~~~~~~~~~~~~~~~

This module contains the `Stream` class.
"""

from asyncio import Event
from collections import deque

from apodo.net.connection import Connection
from apodo.util.exceptions import StreamAlreadyConsumed


class Stream(deque):
    """ Implements the `Stream` class.

    This class, previously separated into `StreamQueue` and `Stream`,
    `StreamQueue` having an `items` property that was a `deque` object,
    is now a modified subclass of `deque`.
    """

    def __init__(self, connection):
        self.connection: Connection = connection
        self.event: Event = Event()
        self.waiting: bool = False
        self.dirty: bool = False
        self.finished: bool = False

    async def read(self) -> bytearray:
        data = bytearray()
        async for chunk in self:
            data.extend(chunk)
        return data

    def end(self):
        if self.waiting:
            self._put(b"")
        self.finished = True

    def clear(self):
        if self.dirty:
            super().clear()
            self.event.clear()
            self.dirty = False
        self.finished = False

    async def __aiter__(self) -> bytes:
        while True:
            self.connection.resume_reading()
            data = await self._get()
            if not data:
                self.consumed = True
                break
            self.connection.pause_reading()
            yield data

    async def _get(self) -> bytes:
        """
        It should eventually be determined whether this method (`get`, in the original) 
        is used outside of the `__aiter__` method in this class. 
        If not, it should be integrated into the `__aiter__` method.
        """
        try:
            return self.popleft()
        except IndexError:
            if self.finished is True:
                raise StreamAlreadyConsumed()
            else:
                self.event.clear()
                self.waiting = True
                await self.event.wait()
                self.event.clear()
                self.waiting = False
                return self.popleft()

    def _put(self, item: bytes):
        """
        It should eventually be determined whether this method (`put`, in the original) 
        is used outside of the `end` method in this class. 
        If not, it should be integrated into the `end` method.
        """
        self.dirty = True
        self.serverend(item)
        if self.waiting is True:
            self.event.set()
