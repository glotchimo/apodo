"""
apodo.blueprint
~~~~~~~~~~~~~~~

This module contains the `Blueprint` class.
"""

from inspect import iscoroutinefunction
from typing import Callable

from .exceptions import ConflictingPrefixes, DuplicatedBlueprint
from .router import Route


class Blueprint:
    """ Implements the `Blueprint` class.

    This class enables the modularization of an application by
    delegating routes to seperate `Blueprint` objects at runtime.

    :param `hosts`: A `list` of `str` hosts.
    """

    def __init__(self, hosts: list = None):
        self.blueprints = {}

        self.default_routes = {}
        self.routes = []
        self.hosts = hosts

        self.exception_handlers = {}

        self.app = None
        self.parent = None

    def route(self, path, name=None, methods=None, hosts: list = None) -> Callable:
        """ Wraps a method to register a new route.

        :param `path`: A `str` URL path.
        :param `name`: A `str` name for the route.
        :param `methods`: A `list` of accepted `str` HTTP methods.
        :param `hosts`: A `list` of `str` hosts.
        """

        def register(handler):
            """ Creates and returns a new `Route` object. """

            if not iscoroutinefunction(handler):
                raise TypeError(
                    f"Your route handler must be an async function. (Handler: {handler})"
                )

            self.add_route(
                Route(
                    path.encode(),
                    handler,
                    tuple(methods or (b"GET",)),
                    parent=self,
                    name=handler.__name__ or name,
                    hosts=hosts or self.hosts,
                )
            )

            return handler

        return register

    def add_route(self, route: Route) -> None:
        """ Adds a `Route` to the instance. """
        self.routes.append(route)

    def add_blueprint(self, blueprint, prefixes: dict = None) -> None:
        """ Adds a nested `Blueprint` to the instance.

        :param `blueprint`: A `Blueprint` object.
        :param `prefixes`: A `dict` of route prefixes.
        """
        if not prefixes:
            prefixes = {"": ""}

        if blueprint.parent:
            raise DuplicatedBlueprint(
                "You cannot add a blueprint twice. Use more prefixes or different hierarchy."
            )

        for key in prefixes.keys():
            for prefix in self.blueprints.values():
                if key == prefix:
                    raise ConflictingPrefixes(
                        f'Prefix "{key}" conflicts with an already existing prefix: {prefix}'
                    )

        blueprint.parent = self
        self.blueprints[blueprint] = prefixes
