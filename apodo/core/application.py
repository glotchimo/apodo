"""
apodo.application
~~~~~~~~~~~~~~~~~

This module contains the `Application` class.
"""

from apodo.core.blueprint import Blueprint
from apodo.net.connection import Connection
from apodo.net.request import Request
from apodo.net.router import Router
from apodo.util.exceptions import DuplicatedBlueprint, ReverseNotFound


class Application(Blueprint):
    """ Implements `Application`.

    This is a subclass of `Blueprint`, which defines the base utilities
    for the app, with `Application` managing state and session.

    :param url_scheme: A `str` representing the URL scheme, default being http.
    :param request_class: A `Request` class.
    """

    current_time: str = None

    def __init__(self, url_scheme="http", request_class=Request):
        super().__init__()

        self.url_scheme = url_scheme

        self.router = Router()
        self.handler = Connection

        self.connections = set()
        self.workers = []

        self.loop = None

        self.initialized = False
        self.running = False

        if not issubclass(request_class, Request):
            raise ValueError(
                "request_class must be a child of the Apodo Request class. "
                "(from apodo.request import Request)"
            )
        self.request_class = request_class

    def add_blueprint(self, blueprint, prefixes: dict = None):
        """ Adds a top-level blueprint to the application.

        :param blueprint: A `Blueprint` object to add.
        :param prefixes: A `dict` of prefixes.
        """
        if blueprint.parent:
            raise DuplicatedBlueprint()
        elif blueprint != self:
            blueprint.parent = self

        prefixes = prefixes or {"": ""}

        self._register_routes(blueprint, prefixes)
        self.blueprints[blueprint] = prefixes

    def _register_routes(self, blueprint, prefixes):
        """ Registers routes from a `Blueprint`.

        This method first searches through the provided prefixes for nested blueprints,
        and recursively calls itself with those objects. Following that, the blueprint's
        app is set as well as any routes it has. Then, the routes are added to the app's
        router.

        :param blueprint: A `Blueprint` object.
        :param prefixes: (optional) A `dict` of prefixes.
        """
        for name, pattern in prefixes.items():
            for (nested_blueprint, nested_prefixes) in blueprint.blueprints.items():
                for nested_name, nested_pattern in nested_prefixes.items():
                    if name and nested_name:
                        merged_prefixes = {
                            name + ":" + nested_name: pattern + nested_pattern
                        }
                    else:
                        merged_prefixes = {
                            name or nested_name: pattern + nested_pattern
                        }

                    self._register_routes(nested_blueprint, prefixes=merged_prefixes)

        blueprint.app = self
        for route in blueprint.routes:
            route.app = self.app

    def clean_up(self):
        """ Kills all active worker processes. """
        for process in self.workers:
            process.terminate()

        self.running = False

    def url_for(self, _name, _external=False, *args, **kwargs) -> str:
        """ Creates a URL from a given route name.

        This method constructs a URL from a given route name, and will build a full
        URL from server_name and url_scheme if _external is set to True.

        :param _name: The `str` name of a route.
        :param _external: A `bool` determining the use of an external URL.

        :return url: A `str` URL.
        """
        if not self.initialized:
            raise ValueError("Routes are not yet registered.")

        route = self.router.reverses.get(_name)
        if not route:
            raise ReverseNotFound(_name)

        root = ""
        if _external:
            if not self.url_scheme:
                raise Exception("Please configure the server_name and url_scheme.")

            root = self.url_scheme + "://"

        return root + route.path.decode()
