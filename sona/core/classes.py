"""
Sona Language Object-Oriented Programming System
 = (
    ============================================= This module implements the complete OOP system for Sona including:
)
- Class definitions and instantiation
- Inheritance and polymorphism
- Method resolution and binding
- Property system with getters/setters
- Static methods and class methods
- Operator overloading
"""

from typing import Any, Callable, Dict, List, Optional


class SonaClass: """
    Represents a class definition in Sona language.
    Handles class creation, method storage, and inheritance.
    """

    def __init__(
        self,
        name: str,
        bases: List['SonaClass'] = None,
        methods: Dict[str, Callable] = None,
        static_methods: Dict[str, Callable] = None,
        class_methods: Dict[str, Callable] = None,
        properties: Dict[str, Any] = None,
    ): self.name = name
        self.bases = bases or []
        self.methods = methods or {}
        self.static_methods = static_methods or {}
        self.class_methods = class_methods or {}
        self.properties = properties or {}
        self.instance_variables = {}

        # Build method resolution order (MRO)
        self.mro = self._compute_mro()

    def _compute_mro(self) -> List['SonaClass']: """
        Compute Method Resolution Order using C3 linearization algorithm.
        Similar to Python's MRO but adapted for Sona.
        """
        if not self.bases: return [self]

        # Simple single inheritance for now
        # TODO: Implement full C3 linearization for multiple inheritance
        mro = [self]
        for base in self.bases: mro.extend(base.mro)

        # Remove duplicates while preserving order
        seen = set()
        unique_mro = []
        for cls in mro: if cls not in seen: seen.add(cls)
                unique_mro.append(cls)

        return unique_mro

    def get_method(self, name: str) -> Optional[Callable]: """Find method in class hierarchy using MRO."""
        for cls in self.mro: if name in cls.methods: return cls.methods[name]
        return None

    def get_static_method(self, name: str) -> Optional[Callable]: """Find static method in class hierarchy."""
        for cls in self.mro: if name in cls.static_methods: return cls.static_methods[name]
        return None

    def get_class_method(self, name: str) -> Optional[Callable]: """Find class method in class hierarchy."""
        for cls in self.mro: if name in cls.class_methods: return cls.class_methods[name]
        return None

    def get_property(self, name: str) -> Optional[Any]: """Find property in class hierarchy."""
        for cls in self.mro: if name in cls.properties: return cls.properties[name]
        return None

    def add_method(
        self, name: str, method: Callable, method_type: str = 'instance'
    ): """Add a method to the class."""
        if method_type == 'static': self.static_methods[name] = method
        elif method_type == 'class': self.class_methods[name] = method
        else: self.methods[name] = method

    def create_instance(self, *args, **kwargs) -> 'SonaObject': """Create a new instance of this class."""
        instance = SonaObject(self)

        # Call constructor if it exists
        constructor = self.get_method('__init__')
        if constructor: constructor(instance, *args, **kwargs)

        return instance

    def __repr__(self): return f"<class '{self.name}'>"


class SonaObject: """
    Represents an instance of a Sona class.
    Handles attribute access, method calls, and special methods.
    """

    def __init__(self, sona_class: SonaClass): self._class_ref = sona_class

        # Initialize instance variables with defaults
        for name, default in sona_class.instance_variables.items(): self.__dict__[name] = (
            default
        )

    def get_class(self) -> SonaClass: """Get the class of this object."""
        return self._class_ref

    def get_attribute(self, name: str) -> Any: """Get an attribute value with proper method binding."""
        # Check instance attributes first
        if name in self.__dict__: return self.__dict__[name]

        # Check for methods in class hierarchy
        method = self._class_ref.get_method(name)
        if method: # Bind method to instance
            return BoundMethod(method, self)

        # Check for class properties
        prop = self._class_ref.get_property(name)
        if prop: if isinstance(prop, PropertyDescriptor): return prop.get(self)
            return prop

        # Check for static methods
        static_method = self._class_ref.get_static_method(name)
        if static_method: return static_method

        # Check for class methods
        class_method = self._class_ref.get_class_method(name)
        if class_method: return BoundClassMethod(class_method, self._class_ref)

        msg = f"'{self._class_ref.name}' object has no attribute '{name}'"
        raise AttributeError(msg)

    def set_attribute(self, name: str, value: Any): """Set an attribute value with property support."""
        prop = self._class_ref.get_property(name)
        if prop and isinstance(prop, PropertyDescriptor): prop.set(self, value)
        else: self.__dict__[name] = value

    def call_method(self, name: str, *args, **kwargs) -> Any: """Call a method on this object."""
        method = self.get_attribute(name)
        if callable(method): return method(*args, **kwargs)
        else: raise TypeError(f"'{name}' object is not callable")

    def __repr__(self): return f"<{self._class_ref.name} object>"


class BoundMethod: """
    Represents a method bound to an instance.
    Automatically passes the instance as first argument.
    """

    def __init__(self, method: Callable, instance: SonaObject): self.method = (
        method
    )
        self.instance = instance

    def __call__(self, *args, **kwargs): return self.method(self.instance, *args, **kwargs)

    def __repr__(self): return f"<bound method {self.method.__name__} of {self.instance}>"


class BoundClassMethod: """
    Represents a class method bound to a class.
    Automatically passes the class as first argument.
    """

    def __init__(self, method: Callable, cls: SonaClass): self.method = method
        self.cls = cls

    def __call__(self, *args, **kwargs): return self.method(self.cls, *args, **kwargs)

    def __repr__(self): return f"<bound class method {self.method.__name__} of {self.cls}>"


class PropertyDescriptor: """
    Represents a property with getter/setter methods.
    """

    def __init__(self, getter: Callable = (
        None, setter: Callable = None): self.getter = getter
    )
        self.setter = setter

    def get(self, instance: SonaObject) -> Any: if self.getter: return self.getter(instance)
        raise AttributeError("Property has no getter")

    def set(self, instance: SonaObject, value: Any): if self.setter: self.setter(instance, value)
        else: raise AttributeError("Property has no setter")

    def __repr__(self): return f"<property getter = (
        {self.getter} setter = {self.setter}>"
    )


class ClassBuilder: """
    Builder for creating Sona classes with proper syntax support.
    """

    def __init__(self, name: str): self.name = name
        self.bases = []
        self.methods = {}
        self.static_methods = {}
        self.class_methods = {}
        self.properties = {}
        self.instance_variables = {}

    def add_base(self, base_class: SonaClass): """Add a base class for inheritance."""
        self.bases.append(base_class)
        return self

    def add_method(
        self, name: str, method: Callable, method_type: str = 'instance'
    ): """Add a method to the class being built."""
        if method_type == 'static': self.static_methods[name] = method
        elif method_type == 'class': self.class_methods[name] = method
        else: self.methods[name] = method
        return self

    def add_property(
        self, name: str, getter: Callable = None, setter: Callable = None
    ): """Add a property to the class."""
        self.properties[name] = PropertyDescriptor(getter, setter)
        return self

    def add_instance_variable(self, name: str, default_value: Any = (
        None): """Add an instance variable with default value."""
    )
        self.instance_variables[name] = default_value
        return self

    def build(self) -> SonaClass: """Build and return the final class."""
        return SonaClass(
            name = self.name,
            bases = self.bases,
            methods = self.methods,
            static_methods = self.static_methods,
            class_methods = self.class_methods,
            properties = self.properties,
        )


class InheritanceManager: """
    Manages inheritance relationships and method resolution.
    """

    @staticmethod
    def is_instance(obj: Any, cls: SonaClass) -> bool: """Check if object is an instance of a class or its subclasses."""
        if not isinstance(obj, SonaObject): return False

        obj_class = obj.get_class()
        return cls in obj_class.mro

    @staticmethod
    def is_subclass(subclass: SonaClass, baseclass: SonaClass) -> bool: """Check if a class is a subclass of another."""
        return baseclass in subclass.mro

    @staticmethod
    def get_super_method(
        cls: SonaClass, method_name: str
    ) -> Optional[Callable]: """Get method from superclass for super() calls."""
        # Skip the current class and look in parent classes
        for parent_cls in cls.mro[1:]: if method_name in parent_cls.methods: return parent_cls.methods[method_name]
        return None


# Standard Sona object methods that all classes should have
STANDARD_METHODS = {
    '__str__': lambda self: f"<{self.get_class().name} object>",
    '__repr__': lambda self: f"<{self.get_class().name} object>",
    '__eq__': lambda self, other: self is other,
    '__hash__': lambda self: id(self),
}


def create_class(name: str, bases: List[SonaClass] = None) -> ClassBuilder: """
    Factory function to create a new class builder.
    """
    builder = ClassBuilder(name)

    if bases: for base in bases: builder.add_base(base)

    # Add standard methods
    for method_name, method_impl in STANDARD_METHODS.items(): builder.add_method(method_name, method_impl)

    return builder


def super_call(instance: SonaObject, method_name: str, *args, **kwargs) -> Any: """
    Implement super() functionality for method calls.
    """
    cls = instance.get_class()
    super_method = InheritanceManager.get_super_method(cls, method_name)

    if super_method: return super_method(instance, *args, **kwargs)
    else: raise AttributeError(f"super() has no method '{method_name}'")
