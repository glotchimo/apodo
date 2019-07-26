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
