"""
apodo.connection
~~~~~~~~~~~~~~~~

This module contains the `Connection` class.
"""

from asyncio import CancelledError, Event, Task, Transport, sleep
from time import time

from .application import Application
from .headers.headers import Headers
from .parsers.errors import HttpParserError
from .parsers.parser import HttpParser
from .request.request import Request, Stream
from .responses.responses import Response
from .router import Route

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

    :param `app`: The current `Application` object.
    :param `loop`: An event loop.
    :param `protocol`: The `bytes` protocol of the connection.
    :param `parser`: An `HttpParser` object.
    """

    def __init__(self, app: Application, loop: object):
        self.app: Application = app
        self.loop: object = loop
        self.protocol: bytes = b"1.1"

        self.transport: Transport = None
        self.stream: Stream = Stream(self)

        self.parser: HttpParser = HttpParser(
            self, app.server_limits.max_headers_size, app.limits.max_body_size
        )

        self.status: int = PENDING_STATUS
        self.writable: bool = True
        self.readable: bool = True
        self.write_permission: Event = Event()
        self.current_task = None
        self.timeout_task = None
        self.closed: bool = False
        self.last_task_time: time = time()
        self._stopped: bool = False

        self.keep_alive = app.server_limits.keep_alive_timeout > 0
        self.request_class = self.app.request_class
        self.router = self.app.router
        self.log = self.app.log_handler
        self.queue = self.stream.queue
        self.write_buffer = app.server_limits.write_buffer

    async def handle_request(self, request: Request, route: Route) -> None:
        """ Handles an incoming request.

        :return `request`: A `Request` object.
        :return `route`: The corresponding `Route` object.
        """
        response: Response = await route.call_handler(request, self.components)
        response.send(self)

    def cancel_request(self) -> None:
        """ Cancels a current task/request. """
        self.current_task.cancel()

    def connection_made(self, transport: Transport) -> None:
        """ Localizes the transport and adds the connection to the app.

        :param `transport`: The connection stream's `Transport` object.
        """
        self.transport: Transport = transport
        self.app.connections.add(self)

    def data_received(self, data: bytes) -> None:
        """ Sends received data to the parser.

        :param `data`: A `bytes` representation of the incoming data.
        """
        self.status = RECEIVING_STATUS

        try:
            self.parser.feed_data(data)
        except HttpParserError:
            self.pause_reading()
            self.close()

    def pause_reading(self) -> None:
        """ Pauses the transport reading the stream. """
        if self.readable:
            self.transport.pause_reading()
            self.readable = False

    def resume_reading(self) -> None:
        """ Resumes the transport reading the stream. """
        if not self.readable:
            self.transport.resume_reading()
            self.readable = True

    def on_headers_complete(
        self, headers: Headers, url: bytes, method: bytes, upgrade: int
    ) -> None:
        """ Carries out response flow once headers have been parsed.

        :param `headers`: A `Headers` object.
        :param `url`: A `bytes` representation of the URL.
        :param `method`: A `bytes` representation of the method.
        """
        request: Request = self.request_class(url, headers, method, self.stream, self)
        route: Route = self.router.get_route(request)

        self.last_task_time = time()
        self.current_task = Task(self.handle_request(request, route), loop=self.loop)

        self.timeout_task = self.loop.call_later(
            route.limits.timeout, self.cancel_request
        )

    def on_body(self, body: bytes) -> None:
        """ Reads the body of the request.

        This method pauses the reading of the socket while the response
        is being processed, helping prevent DoS, until the user explicitly
        consumes the stream.

        :param body:
        :return:
        """
        self.queue.put(body)
        self.pause_reading()

    def on_message_complete(self) -> None:
        """ Closes the queue and sets up the process for monitoring. """
        self.queue.end()
        self.status = PROCESSING_STATUS

    def after_response(self, response: Response) -> None:
        """ Handles after-response network flow.

        :param `response`: A `Response` object.
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

    async def write(self, data: bytes) -> None:
        """ Writes data to the client.

        :param `data`: A `bytes` representation of data to return.
        """
        self.transport.write(data)

        if not self.writable:
            await self.write_permission.wait()

    def pause_writing(self) -> None:
        """ Pauses the transport writing to the client. """
        self.writable = False

    def resume_writing(self):
        """ Resumes the transport writing to the client. """
        if not self.writable:
            self.writable = True
            self.write_permission.set()

    def close(self) -> None:
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
