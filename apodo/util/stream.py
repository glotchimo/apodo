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

    def __init__(self, connection: Connection):
        super().__init__()

        self.connection: Connection = connection
        self.event: Event = Event()

        self.waiting: bool = False
        self.dirty: bool = False
        self.consumed: bool = False

    async def __aiter__(self):
        if self.consumed:
            raise StreamAlreadyConsumed()

        while True:
            self.connection.resume_reading()

            data = await self.get()
            if not data:
                self.consumed = True
                break

            self.connection.pause_reading()
            yield data

    async def get(self) -> bytes:
        try:
            return self.popleft()
        except IndexError:
            if self.consumed:
                return b""
            else:
                self.event.clear()
                self.waiting = True

                await self.event.wait()

                self.event.clear()
                self.waiting = False

                return self.popleft()

    def put(self, item: bytes):
        self.dirty = True
        self.append(item)

        if self.waiting is True:
            self.event.set()

    def clear_queue(self):
        if self.dirty:
            self.clear()
            self.event.clear()

            self.dirty = False

        self.consumed = False

    def end(self):
        if self.waiting:
            self.put(b"")

        self.consumed = True

    async def read(self) -> bytearray:
        if self.consumed:
            raise StreamAlreadyConsumed()

        data = bytearray()
        async for chunk in self:
            data.extend(chunk)

        return data
