"""
apodo.exceptions
~~~~~~~~~~~~~~~~

This module contains custom exceptions.
"""

from inspect import signature
from typing import Callable, get_type_hints


class ApodoException(Exception):
    pass


class RouteConfigurationError(ApodoException):
    pass


class ReverseNotFound(ApodoException):
    def __init__(self, route_name):
        super().__init__(f"{route_name}\nCheck your function names.")


class DuplicatedBlueprint(ApodoException):
    pass


class ConflictingPrefixes(ApodoException):
    pass
