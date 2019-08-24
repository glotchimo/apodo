"""
apodo.server
~~~~~~~~~~~

This module contains the `Apodo` core server class.
"""

from typing import MethodDescriptorType, MethodWrapperType
from asyncio import run, start_server, Server, StreamReader, StreamWriter

from .request import Request


class Apodo:
    """ Implements the `Apodo` application class.

    This class serves as the central instance and interface for the application.
    It is the interface through which the user creates views, and also controls
    views, routing, sessions, etc.

    :param `name`: a `str` name for the server.
    :param `host`: a `str` host URI.
    :param `port`: a `str` port number.
    """

    def __init__(
        self, name: str = "Apodo", host: str = "127.0.0.1", port: str = "7777"
    ):
        self.name: str = name
        self.host: str = host
        self.port: str = port

        self.views: dict = {}

    def view(self, path: str) -> MethodWrapperType:
        """ Registers a view function.

        :param `path`: the `str` `path` of the given view.
        """

        def decorator(f: MethodDescriptorType):
            self.views.update({path: f})
            return f

        return decorator

    def serve(self) -> None:
        """ Runs the server. """
        print(f"Running {self.name} at {self.host} on {self.port}.")
        run(self._catch())

    async def _catch(self) -> None:
        """ Sets up a server to catch incoming connections. """
        server: Server = await start_server(self._route, self.host, self.port)
        await server.serve_forever()

    async def _route(self, reader: StreamReader, writer: StreamWriter) -> None:
        """ Routes new connections to the proper views.

        This method serves as the `client_connected_cb` callback
        parameter of `asyncio.start_server`.

        :param `reader`: a `StreamReader` object.
        :param `writer`: a `StreamWriter` object.
        """
        data: bytes = await reader.read(10000)
        event: str = self._parse(data.decode())

        view: MethodDescriptorType = self.views.get(event.get("path"))

        await Request(view, reader, writer, **event).view()

    def _parse(self, http: str) -> dict:
        """ Parses an HTTP string and returns the body of the event.

        :param `http`: a decoded `str` HTTP request.
        """
        request, *headers, _, body = http.split("\r\n")
        method, path, protocol = request.split(" ")
        headers = dict(line.split(":", maxsplit=1) for line in headers)

        return {
            "method": method,
            "path": path,
            "protocol": protocol,
            "headers": headers,
            "body": body,
        }
