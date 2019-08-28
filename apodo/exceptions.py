from inspect import signature
from typing import Callable, get_type_hints


class ApodoException(Exception):
    pass


class ReverseNotFound(ApodoException):
    def __init__(self, route_name):
        super().__init__("{0}\nCheck your function names.".format(route_name))


class DuplicatedBlueprint(ApodoException):
    pass


class ConflictingPrefixes(ApodoException):
    pass
