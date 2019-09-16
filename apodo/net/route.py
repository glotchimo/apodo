"""
apodo.net.route
~~~~~~~~~~~~~~~

This module contains the `Route` class.
"""

from typing import List, Tuple

from ..core.application import Application
from ..core.blueprint import Blueprint
from ..util.exceptions import MethodNotAllowed, ReverseNotFound
from ..util.utils import clean_methods, clean_route_name
from .connection import Connection
from .request import Request
from .response import Response


class Route:
    """ Implements the `Route` class.

    :param path: A `bytes`-like representation of the path.
    :param handler: I have no clue what this object is.
    :param app: The active `Application` instance.
    :param parent: The `Route`'s parent, a `Blueprint` object.
    """

    def __init__(
        self,
        path: bytes,
        handler: Connection,
        app: Application = None,
        parent: Blueprint = None,
        methods: Tuple = None,
        name: str = None,
        hosts: List = None,
    ):
        self.path = path
        self.handler = handler
        self.app = app
        self.parent = parent
        self.methods = clean_methods(methods)
        self.hosts = hosts

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(
                [
                    other.path == self.path,
                    other.handler == self.handler,
                    other.methods == self.methods,
                ]
            )
        else:
            return False

    def __str__(self):
        return f"<Route ('{self.path}', methods={self.methods})>"

    def call_handler(self, request: Request) -> Response:
        return self.handler()

    def clone(self, path=None, name=None, handler=None, methods=None):
        return Route(
            path=path or self.path,
            handler=handler or self.handler,
            methods=methods or self.methods,
            parent=self.parent,
            app=self.app,
            limits=self.limits,
            hosts=self.hosts,
            name=name or self.name,
            cache=self.cache,
        )
