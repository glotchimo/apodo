"""
apodo.net.request
~~~~~~~~~~~~~~~~~

This module contains the `Request` class.
"""

import json
from typing import Callable
from urllib.parse import ParseResult, parse_qs, urlparse

from apodo.net.connection import Connection
from apodo.net.headers import Headers
from apodo.util.stream import Stream
from apodo.util.exceptions import InvalidJSON, StreamAlreadyConsumed
from apodo.util.utils import RequestParams


class Request:
    """ Implements the `Request` class.

    :param url: A `bytes` representation of the URL.
    :param headers: A `Headers` object.
    :param method: A `bytes` representation of the request method.
    :param stream: A `Stream` object.
    :param connection: A `Connection` object.
    """

    def __init__(
        self,
        url: bytes,
        headers: Headers,
        method: bytes,
        stream: Stream,
        connection: Connection,
    ):
        self.url = url
        self.method = method
        self.headers = headers
        self.context = {}

        self.connection = connection
        self.stream = stream

        self._cookies = None
        self._args = None
        self._parsed_url = None
        self._form = None
        self._session = None

    @property
    def app(self):
        return self.connection.app

    @property
    def parsed_url(self) -> ParseResult:
        if not self._parsed_url:
            self._parsed_url = urlparse(self.url)

        return self._parsed_url

    @property
    def args(self) -> RequestParams:
        if not self._args:
            self._args = RequestParams(parse_qs(self.parsed_url.query))

        return self._args

    @property
    def cookies(self) -> dict:
        if self._cookies is None:
            self._cookies = self.headers.parse_cookies()

        return self._cookies

    async def json(self, loads: Callable = None, strict: bool = False) -> dict:
        """ Wraps the JSON `loads` method and returns deserialized JSON data.

        :param loads: A `Callable` loads method.
        :param strict: A `bool` switch determining whether or not to deserialize strict.

        :return:
        """
        if strict:
            ct = self.headers.get("Content-Type")

            conditions = (
                ct == "application/json"
                and ct.startswith("application/")
                and ct.endswith("+json")
            )
            if not any(conditions):
                raise InvalidJSON(
                    "JSON strict mode is enabled "
                    "and HTTP header does not match the required format."
                )

        loads = loads or json.loads

        try:
            return loads((await self.stream.read()).decode())
        except ValueError:
            raise InvalidJSON("HTTP request body is not a valid JSON.", 400)
