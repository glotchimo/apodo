"""
apodo.blueprint
~~~~~~~~~~~~~~~

This module contains the `Blueprint` class.
"""

from inspect import iscoroutinefunction
from typing import Callable

from apodo.net.route import Route
from apodo.util.exceptions import ConflictingPrefixes, DuplicatedBlueprint


class Blueprint:
    """ Implements the `Blueprint` class.

    This class enables the modularization of an application by
    delegating routes to separate `Blueprint` objects at runtime.

    :param hosts: A `list` of `str` hosts.
    """

    def __init__(self, hosts: list = None):
        self.blueprints = {}

        self.default_routes = {}
        self.routes = []
        self.hosts = hosts

        self.app = None
        self.parent = None

    def route(self, path, name=None, methods=None, hosts: list = None) -> Callable:
        """ Wraps a method to register a new route.

        :param path: A `str` URL path.
        :param name: A `str` name for the route.
        :param methods: A `list` of accepted `str` HTTP methods.
        :param hosts: A `list` of `str` hosts.
        """

        def register(view):
            if not iscoroutinefunction(view):
                raise TypeError(f"Your view method must be an async function. (View: {view})")

            self.add_route(
                Route(
                    path._encode(),
                    view,
                    methods=tuple(methods or (b"GET",)),
                    parent=self,
                    name=view.__name__ or name,
                    hosts=hosts or self.hosts,
                )
            )

            return view

        return register

    def add_route(self, route: Route):
        self.routes.append(route)

    def add_blueprint(self, blueprint, prefixes: dict = None):
        """ Adds a nested blueprint to the current blueprint.

        :param blueprint: A `Blueprint` to nest.
        :param prefixes: A `dict` of prefixes.
        """
        if blueprint.parent:
            raise DuplicatedBlueprint("You cannot add a blueprint twice. Use more prefixes or different hierarchy.")

        prefixes = prefixes or {"": ""}

        for key in prefixes.keys():
            for prefix in self.blueprints.values():
                if key == prefix:
                    raise ConflictingPrefixes(f'Prefix "{key}" conflicts with an already existing prefix: {prefix}')

        blueprint.parent = self
        self.blueprints[blueprint] = prefixes
