"""
apodo.connection
~~~~~~~~~~~~~~~~

This module contains the `Connection` class.
"""

from asyncio import AbstractEventLoop, Event, Task, Transport, sleep
from time import time
from typing import Callable

from apodo.server import Server
from apodo.net.headers import Headers
from apodo.util.parser import Parser
from apodo.util.stream import Stream

STATUS_PENDING: int = 1
STATUS_RECEIVING: int = 2
STATUS_PROCESSING: int = 3


class Connection:
    """ Implements the `Connection` class.

    This class is instantiated per connection received by the server.
    It controls all transport-level reading and writing operations
    from and to the client.

    Many of the methods in the `Connection` class are callback methods 
    for either the network flow or parser flow. They are marked as such 
    respectively with either the prefix (NFC) or (PFC) before 
    high-level line of the docstring.

    Many attributions that would be seen post-initialization would decrease
    performance, and are therefore set during initialization.

    :param server: The current `Server` instance.
    :param loop: An event loop.
    :param protocol: The `bytes` protocol of the connection.
    """

    def __init__(self, server: Server, loop: AbstractEventLoop, protocol: bytes):
        self.server: Server = server
        self.loop: AbstractEventLoop = loop

        self.transport: Transport = None
        self.stream: Stream = Stream(self)
        self.parser: Parser = Parser(self)

        self.protocol: bytes = protocol or b"1.1"

        self.status: int = STATUS_PENDING
        self.writable: bool = True
        self.readable: bool = True
        self.write_permission: Event = Event()
        self.current_task: Task = None
        self.timeout_task: Task = None
        self.closed: bool = False
        self.last_task_time: time = time()
        self.keep_alive = True
        self._stopped: bool = False

    def cancel_request(self):
        """ (NFC) Cancels a current task/request. """
        self.current_task.cancel()

    def connection_made(self, transport: Transport):
        """ (NFC) Localizes the transport and adds the connection to the server.

        :param transport: The connection stream's `Transport` object.
        """
        self.transport: Transport = transport
        self.server.connections.add(self)

    def data_received(self, data: bytes):
        """ (NFC) Sends received data to the parser.

        :param data: A `bytes` representation of the incoming data.
        """
        self.status = STATUS_RECEIVING

        try:
            self.parser.parse(data)
        except Exception:
            self.pause_reading()
            self.close()

    def pause_reading(self):
        """ (NFC) Pauses the transport reading the stream. """
        if self.readable:
            self.transport.pause_reading()
            self.readable = False

    def resume_reading(self):
        """ (NFC) Resumes the transport reading the stream. """
        if not self.readable:
            self.transport.resume_reading()
            self.readable = True

    def on_headers_complete(self, headers: Headers, url: bytes, method: bytes):
        """ (PFC) Carries out response flow once headers have been parsed.

        :param headers: A `Headers` object.
        :param url: A `bytes` representation of the URL.
        :param method: A `bytes` representation of the method.
        """
        self.last_task_time = time()
        self.current_task = Task(self.send_response(route, request), loop=self.loop)

    def on_body(self, body: bytes):
        """ (PFC) Reads the body of the request.

        This method pauses the reading of the socket while the response
        is being processed, helping prevent DoS, until the user explicitly
        consumes the stream.

        :param body: A `bytes` representation of the request body.
        """
        self.stream._put(body)
        self.pause_reading()

    def on_message_complete(self):
        """ (PFC) Closes the stream and sets up the process for monitoring. """
        self.stream.end()
        self.status = STATUS_PROCESSING

    def after_response(self):
        """ Handles after-response network flow. """
        self.status: int = STATUS_PENDING

        if not self.keep_alive:
            self.close()
        elif self._stopped:
            self.loop.create_task(self.scheduled_close(timeout=30))
        else:
            self.resume_reading()

        self.stream.clear()

        if self.timeout_task:
            self.timeout_task.cancel()
            self.timeout_task = None

    async def write(self, data: bytes):
        """ Writes data to the client.

        :param data: A `bytes` representation of data to return.
        """
        self.transport.write(data)

        if not self.writable:
            await self.write_permission.wait()

    def pause_writing(self):
        """ (NFC) Pauses the transport writing to the client. """
        self.writable = False

    def resume_writing(self):
        """ (NFC) Resumes the transport writing to the client. """
        if not self.writable:
            self.writable = True
            self.write_permission.set()

    async def send_response(self, route: Route, request: Request):
        """ Sends the response back to the client.

        :param route: The targeted `Route`.
        :param request: The received `Request`.
        """
        response: Response = await route.view(request)
        response.send(self)

    def close(self):
        """ (NFC) Closes the transport connection. """
        if not self.closed:
            self.transport.close()
            self.server.connections.discard(self)
            self.closed = True

    async def scheduled_close(self, timeout: int = 30):
        """ (NFC) Closes the connection after a scheduled timeout. """
        buffer_size = self.transport.get_write_buffer_size
        while buffer_size() > 0:
            await sleep(0.5)

        self.close()

    def stop(self):
        """ (NFC) Closes the connection and sets the connection to stopped. """
        self._stopped = True
        if self.status == STATUS_PENDING:
            self.close()
