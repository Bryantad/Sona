"""Top-level Sona package.

Lightweight import to support commands (like credential management)
that don't require the full interpreter or parser stack. Heavy
interpreter components are loaded lazily on first access.
"""

__version__ = "0.10.3"
__author__ = "Sona Development Team"

_LAZY_SYMBOLS = {
    'SonaUnifiedInterpreter': 'interpreter',
    'default_interpreter': 'interpreter',
    'SonaFunction': 'interpreter',
    'SonaMemoryManager': 'interpreter',
    'SonaRuntimeError': 'interpreter',
    'SonaInterpreter': 'interpreter',
}

__all__ = list(_LAZY_SYMBOLS.keys()) + ['__version__', '__author__']


def __getattr__(name):  # pragma: no cover - thin lazy loader
    module_name = _LAZY_SYMBOLS.get(name)
    if module_name is None:
        raise AttributeError(name)
    from importlib import import_module
    mod = import_module(f'.{module_name}', __name__)
    value = getattr(mod, name)
    globals()[name] = value  # cache
    return value
