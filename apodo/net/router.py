"""
apodo.net.router
~~~~~~~~~~~~~~~~

This module contains the `RouterStrategy` and `Router` classes.
"""

import re

from apodo.net.request import Request
from apodo.net.route import Route
from apodo.util.exceptions import MethodNotAllowed, ReverseNotFound


class Router:
    """ Implements the `Router` class. """

    def __init__(self):
        self.reverses = {}
        self.routes = {}

        self.check_host = False
        self.hosts = {}

    def build_url(self, _name: str, *args, **kwargs):
        """ Builds a full URL from the reverse of a given route. """
        try:
            route = self.reverses[_name]
            return route.build_url(*args, **kwargs)
        except KeyError:
            raise ReverseNotFound(f"Failed to build url for {_name}")

    def add_route(self, route: Route, prefixes: dict = None, check_slashes: bool = True):
        """ Adds a route with the given prefixes to the instance.

        This is a complicated process/result that is still being worked out
        and documented. Handle with care.
        """
        if not prefixes:
            prefixes = {"": ""}

        for name_prefix, pattern_prefix in prefixes.items():
            if route.hosts:
                self.check_host = True

                for host in route.hosts:
                    host = re.compile(host)
                    routes = self.hosts.setdefault(host, {})

                    for method in route.methods:
                        routes.setdefault(method, []).append(route)

            else:
                for method in route.methods:
                    self.routes.setdefault(method, {})[route.pattern] = route

            self.reverse_index[route.name] = route

    def get_route(self, request: Request) -> Route:
        """ Gets the route correspondent to the given `Request`. """
        if self.check_host:
            return self._find_route_by_host(request.url, request.method, request.headers.get("host"))
        else:
            return self._find_route(request.url, request.method)

    def _find_route_by_host(self, url: bytes, method: bytes, host: str) -> Route:
        """ Finds a route by a specific host. """
        for pattern, routes in self.hosts.items():
            if pattern.fullmatch(host):
                for route in routes.get(method, []):
                    return route

                allowed = []
                for method_name in self.hosts[host]:
                    if method_name == method:
                        continue

                    for route in self.hosts[host][method_name]:
                        if not route.is_dynamic and route.pattern == url:
                            allowed.append(method_name)
                        elif route.is_dynamic and re.compile(route.path).fullmatch(url):
                            allowed.append(method_name)

                if allowed:
                    raise MethodNotAllowed(allowed=allowed)

        return self._find_route(url, method)

    def _find_route(self, url: bytes, method: bytes) -> Route:
        """ Finds a route by its URL and method. """
        try:
            route = self.routes[method][url]
            return route
        except KeyError:
            pass

        self._check_method(url, method)

        raise ReverseNotFound()

    def _check_method(self, url: bytes, method: bytes):
        """ Checks the validity of a method for a given URL.

        :param url: A `bytes` representation of the URL.
        :param method: A `bytes` representation of the method.
        """
        allowed = []

        for current_method in self.routes.items():
            if current_method == method:
                continue

            if url in self.routes[current_method]:
                allowed.append(allowed)

        for current_method, routes in self.dynamic_routes.items():
            if current_method == method:
                continue

            for route in routes:
                if route.regex.fullmatch(url):
                    allowed.append(current_method)

        if allowed:
            raise MethodNotAllowed(allowed=allowed)
