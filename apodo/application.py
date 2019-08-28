"""
apodo.application
~~~~~~~~~~~~~~~~~

This module contains the `Application` class.
"""

from .request import Request
from .protocol import Connection
from .blueprints import Blueprint
from .components import ComponentsEngine
from .exceptions import ReverseNotFound, DuplicatedBlueprint


class Application(Blueprint):
    """ Implements `Application`.

    This is a subclass of `Blueprint`, which defines the base utilities
    for the app, with `Application` managing state and session.

    :param `url_scheme`: A `str` repressenting the URL scheme, default being http.
    :param `request_class`: A `Request` class.
    """

    current_time: str = None

    def __init__(self, url_scheme="http", request_class=Request):
        super().__init__()

        self.url_scheme = url_scheme

        self.handler = Connection
        self.connections = set()
        self.workers = []

        self.components = ComponentsEngine()

        self.loop = None

        self.initialized = False
        self.running = False

        if not issubclass(request_class, Request):
            raise ValueError(
                "request_class must be a child of the Apodo Request class. "
                "(from apodo.request import Request)"
            )
        self.request_class = request_class

    def add_blueprint(self, blueprint, prefixes=None) -> None:
        """ Adds a blueprint to the application.

        This method ensures that a given blueprint is new, configures its
        parent and prefixes, registers any existing routes, and then sets up
        any hooks.

        :param `blueprint`: A `Blueprint` object to add.
        :param `prefixes`: A `dict` of prefixes.
        """
        if blueprint.parent:
            raise DuplicatedBlueprint()
        elif blueprint != self:
            blueprint.parent = self

        prefixes = prefixes or {"": ""}

        self._register_routes(blueprint, prefixes)
        self.blueprints[blueprint] = prefixes

    def _register_routes(self, blueprint, prefixes=None) -> None:
        """ Registers routes from a `Blueprint`.

        This method first saerches through the provided prefixes for nested blueprints,
        and recursively calls itself with those objects. Following that, the blueprint's
        app is set as well as any routes it has. Then, the routes are added to the app's
        router.

        :param `blueprint`: A `Blueprint` object.
        :param `prefixes`: (optional) A `dict` of prefixes.
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
            route.limits = route.limits or self.limits

            self.router.add_route(route, prefixes=prefixes)

    def clean_up(self) -> None:
        """ Kills all active worker processes. """
        for process in self.workers:
            process.terminate()

        self.running = False

    def url_for(self, _name, _external=False, *args, **kwargs) -> str:
        """ Creates a URL from a given route name.

        This method constructs a URL from a given route name, and will build a full
        URL from server_name and url_scheme if _external is set to True.

        :param `_name`: The `str` name of a route.
        :param `_external`: A `bool` determining the use of an external URL.

        :return url: A str URL.
        """
        if not self.initialized:
            raise ValueError("Routes are not yet registered.")

        route = self.router.reverse_index.get(_name)
        if not route:
            raise ReverseNotFound(_name)

        root = ""
        if _external:
            if not self.server_name or not self.url_scheme:
                raise Exception("Please configure the server_name and url_scheme.")

            root = self.url_scheme + "://" + self.server_name

        return root + route.build_url(*args, **kwargs).decode()
