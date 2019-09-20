"""
apodo.net.route
~~~~~~~~~~~~~~~

This module contains the `Route` class.
"""

from typing import List, Tuple, Callable

from apodo.core.application import Application
from apodo.core.blueprint import Blueprint
from apodo.util.utils import clean_methods


class Route:
    """ Implements the `Route` class.

    :param path: A `bytes`-like representation of the path.
    :param view: I have no clue what this object is.
    :param app: (optional) The active `Application` instance.
    :param parent: (optional) The `Route`'s parent, a `Blueprint` object.
    :param name: (optional) A `str` name for the route.
    :param methods: (optional) A `tuple` of request methods for the route.
    :param hosts: (optional) A `list` of hosts to attach to the route.
    """

    def __init__(
        self,
        path: bytes,
        view: Callable,
        app: Application = None,
        parent: Blueprint = None,
        name: str = None,
        methods: Tuple = None,
        hosts: List = None,
    ):
        self.app: Application = app
        self.parent: Blueprint = parent
        self.view: Callable = view

        self.name: str = name
        self.path: bytes = path
        self.methods: Tuple = clean_methods(methods)
        self.hosts: List = hosts

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all([other.path == self.path, other.view == self.view, other.methods == self.methods])
        else:
            return False

    def __str__(self):
        return f"<Route ('{self.path}', methods={self.methods})>"

    def clone(self, path=None, name=None, view=None, methods=None):
        return Route(
            path=path or self.path,
            view=view or self.view,
            methods=methods or self.methods,
            parent=self.parent,
            app=self.app,
            hosts=self.hosts,
            name=name or self.name,
        )
