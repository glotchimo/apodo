"""
gato.application
~~~~~~~~~~~~~~~~

This module implements the Application class.
"""

from itertools import chain
from typing import Callable, Type, List, Optional

from .request import Request
from .blueprints import Blueprint
from .sessions import SessionEngine
from .router import Router, RouterStrategy, RouteLimits
from .protocol import Connection
from .responses import Response
from .components import ComponentsEngine
from .exceptions import ReverseNotFound, DuplicatedBlueprint
from .templates.engine import TemplateEngine
from .templates.extensions import GatoNodes
from .static import StaticHandler
from .limits import ServerLimits


class Application(Blueprint):
    """ Implements Application.

    This is a sublass of Blueprint, which defines the base utilities
    for the app, with Application managing state and session.

    :param template_dirs: A list of template directives.
    :param router_strategy: A RouterStrategy object.
    :param sessions_engine: A SessionEngine object.
    :param server_name: A str representing the name of the server.
    :param url_scheme: A str repressenting the URL scheme, default being http.
    :param static: A StaticHandler object.
    :param log_handler: A Callable object.
    :param server_limits: A ServerLimits object.
    :param route_limits: A RouteLimits object.
    :param request_class: A Request class.
    """

    current_time: str = None

    def __init__(
        self,
        template_dirs,
        router_strategy=RouterStrategy.CLONE,
        sessions_engine=None,
        server_name=None,
        url_scheme="http",
        static=None,
        log_handler=None,
        access_logs=None,
        server_limits=None,
        route_limits=None,
        request_class=Request,
    ):
        super().__init__(template_dirs=template_dirs, limits=route_limits)
        self.debug_mode = False
        self.test_mode = False
        self.server_name = server_name
        self.url_scheme = url_scheme
        self.handler = Connection
        self.router = Router(strategy=router_strategy)
        self.session_engine = sessions_engine
        self.template_engine = TemplateEngine(extensions=[GatoNodes(self)])
        self.static = static or StaticHandler([])
        self.connections = set()
        self.workers = []
        self.components = ComponentsEngine()
        self.loop = None
        self.access_logs = access_logs
        self.log_handler = log_handler
        self.initialized = False
        self.server_limits = server_limits or ServerLimits()
        self.running = False
        if not issubclass(request_class, Request):
            raise ValueError(
                "request_class must be a child of the Gato Request class. "
                "(from gato.request import Request)"
            )
        self.request_class = request_class
        self._test_client = None

    def add_blueprint(self, blueprint, prefixes=None):
        """ Adds a blueprint to the application.

        This method ensures that a given blueprint is new, configures its
        parent and prefixes, registers any existing routes, and then sets up
        any hooks.

        :param blueprint: A Blueprint object to add.
        :param prefixes: A dict of prefixes.
        """
        if blueprint.parent:
            raise DuplicatedBlueprint()
        elif blueprint != self:
            blueprint.parent = self

        prefixes = prefixes or {}

        self._register_routes(blueprint, prefixes)

        self.blueprints[blueprint] = prefixes

        if blueprint != self:
            for collection, name in (
                (blueprint.hooks, "hooks"),
                (blueprint.async_hooks, "async_hooks"),
            ):
                local_hooks = {}
                for hook_type, hooks in collection.items():
                    for hook in hooks:
                        if not hook.local:
                            self.add_hook(hook)
                        else:
                            local_hooks.setdefault(hook.event_type, []).append(hook)

                setattr(blueprint, name, local_hooks)

    def _register_routes(self, blueprint, prefixes=None):
        """ Registers routes from a Blueprint.

        This method first saerches through the provided prefixes for nested blueprints,
        and recursively calls itself with those objects. Following that, the blueprint's
        app is set as well as any routes it has. Then, the routes are added to the app's
        router.

        :param blueprint: A Blueprint object.
        :param prefixes: A dict of prefixes.
        """
        for name, pattern in prefixes.items():
            for nested_blueprint, nested_prefixes in blueprint.blueprints.items():
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

    def check_hook(self, hook_id):
        """ Checks for the existence of a given hook.

        This method first searches any nested blueprints and returns
        at first discovery of the hook, then defaults to checking hook collections
        on the blueprint.

        :param hook_id: The int ID of a given hook.

        :return: Boolean depending on whether or not the given hook was found.
        """

        for blueprint in self.blueprints.keys():
            if bool(blueprint.hooks.get(hook_id)):
                return True

            if bool(blueprint.async_hooks.get(hook_id)):
                return True

        return bool(self.hooks.get(hook_id) or self.async_hooks.get(hook_id))

    async def call_hook(self, hook_id, components, route=None):
        """ Calls a given hook, returning a response if caught.

        This method collects the existing app, or an additional route and
        the existing app, then iterates through the hooks and calls the handler
        if the given hook is found. If the hook is not found, or the response fails,
        it returns None.

        :param hook_id: The int ID of a given hook.
        :param components: List of existing components to pull hooks from.
        :param route: (optional) An additional Route object to call hooks on.

        :return response: (optional) A Response object.
        """
        objects = (route.parent, self) if route and route.parent != self else (self,)
        for object in objects:
            for hook in object.hooks.get(hook_id, ()):
                return hook.call_handler(components) or None

            for hook in object.async_hooks.get(hook_id, ()):
                return await hook.call_handler(components) or None

    def clean_up(self):
        """ Kills all active worker processes. """
        for process in self.workers:
            process.terminate()

        self.running = False

    def url_for(self, _name, _external=False, *args, **kwargs):
        """ Creates a URL from a given route name.

        This method constructs a URL from a given route name, and will build a full
        URL from server_name and url_scheme if _external is set to True.

        :param _name: The str name of a route.
        :param _external: A bool determining the use of an external URL.

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
