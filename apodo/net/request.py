"""
apodo.net.request
~~~~~~~~~~~~~~~~~

This module contains the `StreamQueue`, `Stream`, and `Request` classes.
"""

import json
from asyncio import Event
from queue import deque
from typing import List
from urllib.parse import ParseResult, parse_qs, urlparse

from ..util.exceptions import InvalidJSON, StreamAlreadyConsumed
from .connection import Connection
from ..util.utils import RequestParams
from .headers import Headers


class Stream(deque):
    def __init__(self, connection):
        self.event = Event()
        self.waiting = False
        self.dirty = False
        self.consumed = False
        self.connection = connection

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
            self.put(None)
        self.consumed = True
        
    async def read(self) -> bytearray:
        if self.consumed:
            raise StreamAlreadyConsumed()
        data = bytearray()
        async for chunk in self:
            data.extend(chunk)
        return data

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


class Request:
    def __init__(
        self,
        url: bytes,
        headers: Headers,
        method: bytes,
        stream: Stream,
        protocol: Connection,
    ):
        """

        :param url:
        :param headers:
        :param method:
        :param stream:
        :param protocol:
        """
        self.url = url
        self.protocol = protocol
        self.method = method
        self.headers = headers
        self.context = {}
        self.stream = stream
        self._cookies = None
        self._args = None
        self._parsed_url = None
        self._form = None
        self._session = None

    @property
    def app(self):
        return self.protocol.app

    def client_ip(self):
        return self.protocol.client_ip()

    @property
    def parsed_url(self) -> ParseResult:
        """

        :return:
        """
        if not self._parsed_url:
            self._parsed_url = urlparse(self.url)
        return self._parsed_url

    @property
    def args(self) -> RequestParams:
        """

        :return:
        """
        if not self._args:
            self._args = RequestParams(parse_qs(self.parsed_url.query))
        return self._args

    @property
    def cookies(self) -> dict:
        """

        :return:
        """
        if self._cookies is None:
            self._cookies = self.headers.parse_cookies()
        return self._cookies

    async def json(self, loads=None, strict: bool = False) -> dict:
        """

        :param loads:
        :param strict:
        :return:
        """
        if strict:
            ct = self.headers.get("Content-Type")
            conditions = (
                ct == "application/json",
                ct.startswith("application/") and ct.endswith("+json"),
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

    async def form(self) -> dict:
        """

        :return:
        """
        if self._form is None:
            await self._load_form()
        return self._form
