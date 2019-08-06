"""
gato.components.context
~~~~~~~~~~~~~~~~~~~~~~~
This module contains an abstraction that allows for easy
access to the components used in the current async task.
"""

from typing import Type
from asyncio import Task


def get_component(type_: Type):
    """
    Get the component of type `type_`
    :param `type_`: the type of component to return
    :return: the component of type `type_` used in the current task.
    """
    current_task = Task.current_task()
    return current_task.components.get(type_)
