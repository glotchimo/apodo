"""
gato.response
~~~~~~~~~~~~~

This module contains the `Response` class.
"""

from datetime import datetime


class Response:
    """ Implements the `Response` class.

    This object is used to store and build response data before
    it is written via the active `StreamWriter`.

    :param `headers`: (optional) A `dict` of header values to send.
    :param `body`: (optional) Data to send back in the response body.
    """

    def __init__(self, body=None, headers: dict = None):
        self.headers = headers
        self.body = body

    def build(self):
        """ Builds raw response data. """
        self.headers.update(
            {
                "Date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "Content-Length": len(self.body),
            }
        )
        header_str = "\r\n".join([f"{k}: {v}" for k, v in self.headers.items()])

        raw = bytes(f"HTTP/1.1 200 OK\r\n{header_str}\r\n\r\n{self.body}", "utf-8")

        return raw
