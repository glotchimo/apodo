from typing import Callable, Type, get_type_hints
from inspect import isclass
from ..exceptions import MissingComponent


class Component:
    """
    The `Component` class validates components for use in the `ComponentEngine`,
    and through the `build` method returns a component ready for use.
    
    :param `builder`: is a function component from which classes will be returned for use.
    The function must be annotated with the return type (which is the class returned).
    :param `cache`: is a `bool` which determines whether or not the class stored in component
    will be stored as a variable.
    :param `prebuilt`: is a class passed directly into the `Component` class. It is
    cached by definition.
    """

    __slots__ = ('builder', 'cache_enabled', 'cache', 'type')

    def __init__(self, builder: Callable = None, cache=False, prebuilt=None):
        try:
            if builder:
                self.type = get_type_hints(builder)['return']
            elif prebuilt:
                self.type = prebuilt.__class__.__name__
            else:
                raise ValueError('You need to pass either builder or prebuilt param.')
            self.builder = builder
            self.cache_enabled = cache
            self.cache = prebuilt
        except KeyError:
            raise ValueError(f'Please type hint the return type of your function. ({builder})')

    def build(self):
        """
        :return: an instance of `self.builder`.
        """
        if self.cache is not None:
            return self.cache
        if self.cache_enabled:
            self.cache = self.builder()
            return self.cache
        return self.builder()


cdef class ComponentsEngine:
    """
    ephemeral components are those used internally and are reset every request/response cycle.
    """
    def __init__(self):
        self.index = {}
        self.ephemeral_index = {}

    def __getitem__(self, item):
        """
        Wrapper for the `get` method.
        
        :param `item`: is the requested component type.
        """
        return self.get(item)

    def add(self, *components, bint ephemeral=False):
        """
        Method for adding components to the `ComponentEngine`. Builds a `Component` instance if
        the *`components` argument contains an instance of a class instead of a `Component` instance.
        Raises a `ValueError` if attempting to add a class, or a component in *`components` is already
        registered.
        
        :param *`components`: the components to be added.
        :param `ephemeral`: `bool` indicating whether or not the added components are ephemeral.
        ephemeral components are those used internally and are reset every request/response cycle.
        :return:
        """
        cdef dict index = self.index
        if ephemeral is True:
            index = self.ephemeral_index
        for component in components:
            if isinstance(component, Component):
                if component.type in self.index:
                    raise ValueError('There is already a component that provides this type. '
                                     'You probably should create a subtype.')
                index[component.type] = component
            elif isclass(component):
                raise ValueError("You shouldn't add class objects to ComponentsEngine. "
                                 "Try an instance of this class or wrap it around a Component object.")
            else:
                type_ = type(component)
                if type_ in self.index:
                    raise ValueError('There is already a component that provides this type. '
                                     'You probably should create a subtype.')
                index[type_] = Component(prebuilt=component)

    @staticmethod
    def search_type(dict index, object required_type):
        """
        Searches for a subclass of `required_type` in `index`.
        Raises a `ValueError` if there is more than one subclass.
        
        :param `index`: the dict of instances to search through.
        :param `required_type`: a parent class.
        :return: the instance which is a subclass of `required_type`.
        """
        element = None
        for key in index.keys():
            if issubclass(key, required_type):
                if element is None:
                    element = key
                else:
                    raise ValueError("Gato can't decide which component do you want, "
                                     f"because there at least two types who are a subclass of {required_type}")
        return element

    def get(self, required_type: Type):
        """
        Returns the instance of `required_type`. If none exists, then `search_type` checks for a subclass.
        
        Should there be two subclasses of `required_type`, a `ValueError` will be raised. If no instance
        exists for `required_type`, a `MissingComponent` error is raised.
        
        :param `required_type`: is the `Type` key of the component instance required.
        :return: the instance of `required type`.
        """
        # Ephemeral index is where Request/Route and other internal framework components are stored.
        # They are reset every request/response cycle so they are keep separated
        # to keep recycling faster.
        if required_type in self.ephemeral_index:
            return self.ephemeral_index[required_type]
        try:
            return self.index[required_type].build()
        except KeyError:
            key = self.search_type(self.index, required_type)
            second_key = self.search_type(self.ephemeral_index, required_type)
            if key is not None and second_key is not None:
                raise MissingComponent("Gato can't decide which component do you want, "
                                       f"because there at least two types who are a subclass of {required_type}",
                                       component=required_type)
            elif key is not None:
                return self.index[key].build()
            elif second_key is not None:
                return self.ephemeral_index[second_key]
        raise MissingComponent(f'ComponentsEngine missing a component of type: {required_type}', component=required_type)

    cpdef ComponentsEngine clone(self):
        """
        Creates a new copy of the current `ComponentsEngine` instance, with references to the instances
        contained in `self.index`.
        
        :return: `ComponentsEngine`
        """
        new = ComponentsEngine()
        new.index = self.index.copy()
        return new

    cdef void reset(self):
        """
        Clears the `ephemeral_index`.
        """
        self.ephemeral_index.clear()
