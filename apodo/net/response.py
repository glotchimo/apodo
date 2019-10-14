"""
apodo.net.response
~~~~~~~~~~~~~~~~~~

This module implements the `Response` class.
"""

from email.utils import formatdate

from apodo.net.connection import Connection
from apodo.util.constants import ALL_STATUS_CODES

current_time: str = formatdate(timeval=None, localtime=False, usegmt=True)


class Response:
    """ Implements the `Response` class.

    :param content: A `bytes` representation of the response's content.
    :param status_code: (default 200) An `int` HTTP status code.
    :param headers: (optional) A `dict` of headers to send with the response.
    :param cookies: (optional) A `dict` of cookie headers to send with the response.
    """

    def __init__(
        self,
        content: bytes,
        status_code: int = 200,
        headers: dict = None,
        cookies: list = None,
    ):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.cookies = cookies or []

    def clone(self, **kwargs):
        """ Clones the current response.

        This method generates a dictionary of parameters from the current instance's attributes,
        overridden by any keyword arguments submitted by the caller.
        """
        params = {
            "content": self.content,
            "status_code": self.status_code,
            "headers": self.headers,
            "cookies": self.cookies,
        }
        params.update(kwargs)

        return self.__class__(**params)

    def send(self, connection: Connection):
        """ Sends the response back to the client.

        This is a sensitive method - if implemented differently, it could blow up server memory.
        First, we must check that the connection is writable such that we don't pass the buffer's high mark.
        To process the next response, but to ensure memory isn't consumed in the event that the client doesn't
        consume the response, we schedule the call of the post-response procedure.

        :param connection: The corresponding `Connection` instance.
        """
        if self.headers or self.cookies:
            connection.transport.write(self._encode() + self.content)
        else:
            connection.transport.write(
                f"HTTP/1.1 {self.status_code} {ALL_STATUS_CODES[self.status_code]}\r\n"
                f"Content-Length: {len(self.content)}\r\n"
                "Date: {current_time}\r\n\r\n".encode() + self.content
            )

        if connection.writable:
            connection.after_response(self)
        else:
            connection.loop.create_task(self._wait_client_consume(self, connection))

    def _encode(self) -> bytes:
        """ Encodes the entirety of the response content.

        :return: A `bytes` representation of the response content.
        """
        headers = self.headers
        headers["Content-Length"] = len(self.content)
        headers["Date"] = current_time

        content = (
            f"HTTP/1.1 {self.status_code} {ALL_STATUS_CODES[self.status_code]}\r\n"
        )

        for header, value in headers.items():
            content += f"{header}: {value}\r\n"

        if self.cookies:
            for cookie in self.cookies:
                content += cookie.header + "\r\n"

        content += "\r\n"

        return content.encode()

    async def _wait_client_consume(self, protocol):
        """ Waits for the client to consume the response. """
        if not protocol.writable:
            await protocol.write_premission()
        else:
            protocol.after_response(self)
