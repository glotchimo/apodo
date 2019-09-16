"""
apodo.connection
~~~~~~~~~~~~~~~~

This module contains the `Connection` class.
"""

from asyncio import AbstractEventLoop, Event, Task, Transport, sleep
from time import time

from apodo.core.application import Application
from apodo.net.headers import Headers
from apodo.net.request import Request, Stream
from apodo.net.response import Response
from apodo.net.router import Route
from apodo.util.parser import HttpParser, HttpParserError

PENDING_STATUS: int = 1
RECEIVING_STATUS: int = 2
PROCESSING_STATUS: int = 3
EVENTS_BEFORE_ENDPOINT: int = 3
EVENTS_AFTER_ENDPOINT: int = 4
EVENTS_AFTER_RESPONSE_SENT: int = 5


class Connection:
    """ Implements the `Connection` class.

    This class is instantiated per connection received by the server.
    It controls all reading and writing operations from and to the client.

    :param app: The current `Application` object.
    :param loop: An event loop.
    :param protocol: The `bytes` protocol of the connection.
    :param parser: An `HttpParser` object.
    """

    def __init__(
        self,
        app: Application,
        loop: AbstractEventLoop,
        protocol: bytes,
        parser: HttpParser,
    ):
        self.app: Application = app
        self.loop: AbstractEventLoop = loop

        self.transport: Transport = None
        self.stream: Stream = Stream(self)
        self.parser: HttpParser = parser or HttpParser()

        self.protocol: bytes = protocol or b"1.1"

        self.status: int = PENDING_STATUS
        self.writable: bool = True
        self.readable: bool = True
        self.write_permission: Event = Event()
        self.current_task = None
        self.timeout_task = None
        self.closed: bool = False
        self.last_task_time: time = time()
        self._stopped: bool = False

        self.request_class = self.app.request_class
        self.router = self.app.router
        self.queue = self.stream.queue

    async def handle_request(self, request: Request, route: Route):
        """ Handles an incoming request.

        :return request: A `Request` object.
        :return route: The corresponding `Route` object.
        """
        response: Response = await route.call_handler(request)
        response.send(self)

    def cancel_request(self):
        """ Cancels a current task/request. """
        self.current_task.cancel()

    def connection_made(self, transport: Transport):
        """ Localizes the transport and adds the connection to the app.

        :param transport: The connection stream's `Transport` object.
        """
        self.transport: Transport = transport
        self.app.connections.add(self)

    def data_received(self, data: bytes):
        """ Sends received data to the parser.

        :param data: A `bytes` representation of the incoming data.
        """
        self.status = RECEIVING_STATUS

        try:
            self.parser.feed_data(data)
        except HttpParserError:
            self.pause_reading()
            self.close()

    def pause_reading(self):
        """ Pauses the transport reading the stream. """
        if self.readable:
            self.transport.pause_reading()
            self.readable = False

    def resume_reading(self):
        """ Resumes the transport reading the stream. """
        if not self.readable:
            self.transport.resume_reading()
            self.readable = True

    def on_headers_complete(self, headers: Headers, url: bytes, method: bytes):
        """ Carries out response flow once headers have been parsed.

        :param headers: A `Headers` object.
        :param url: A `bytes` representation of the URL.
        :param method: A `bytes` representation of the method.
        """
        request: Request = self.request_class(url, headers, method, self.stream, self)
        route: Route = self.router.get_route(request)

        self.last_task_time = time()
        self.current_task = Task(self.handle_request(request, route), loop=self.loop)

    def on_body(self, body: bytes):
        """ Reads the body of the request.

        This method pauses the reading of the socket while the response
        is being processed, helping prevent DoS, until the user explicitly
        consumes the stream.

        :param body:
        :return:
        """
        self.queue.put(body)
        self.pause_reading()

    def on_message_complete(self):
        """ Closes the queue and sets up the process for monitoring. """
        self.queue.end()
        self.status = PROCESSING_STATUS

    def after_response(self, response: Response):
        """ Handles after-response network flow.

        :param response: A `Response` object.
        """
        self.status: int = PENDING_STATUS

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
        """ Pauses the transport writing to the client. """
        self.writable = False

    def resume_writing(self):
        """ Resumes the transport writing to the client. """
        if not self.writable:
            self.writable = True
            self.write_permission.set()

    def close(self):
        """ Closes the transport connection. """
        if not self.closed:
            self.transport.close()
            self.app.connections.discard(self)
            self.closed = True

    async def scheduled_close(self, timeout: int = 30):
        """ Closes the connection after a scheduled timeout. """
        buffer_size = self.transport.get_write_buffer_size
        while buffer_size() > 0:
            await sleep(0.5)

        self.close()

    def stop(self):
        """ Closes the connection and sets the connection to stopped. """
        self._stopped = True
        if self.status == PENDING_STATUS:
            self.close()
