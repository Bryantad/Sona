"""
signal - Signal/event system for Sona stdlib

Provides signal handling:
- Signal: Create and emit signals
- connect: Connect handlers
- emit: Emit events
"""


class Signal:
    """Signal/Event emitter."""
    
    def __init__(self):
        """Initialize signal."""
        self.handlers = []
    
    def connect(self, handler):
        """
        Connect handler to signal.
        
        Args:
            handler: Callback function
        
        Example:
            sig = signal.Signal()
            sig.connect(my_handler)
        """
        if handler not in self.handlers:
            self.handlers.append(handler)
    
    def disconnect(self, handler):
        """
        Disconnect handler from signal.
        
        Args:
            handler: Callback function
        
        Example:
            sig.disconnect(my_handler)
        """
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def emit(self, *args, **kwargs):
        """
        Emit signal to all handlers.
        
        Args:
            args: Positional arguments for handlers
            kwargs: Keyword arguments for handlers
        
        Example:
            sig.emit("data", count=5)
        """
        for handler in self.handlers:
            handler(*args, **kwargs)
    
    def clear(self):
        """Clear all handlers."""
        self.handlers.clear()
    
    def count(self):
        """Get handler count."""
        return len(self.handlers)


def create():
    """
    Create new signal.
    
    Returns:
        Signal object
    
    Example:
        on_data_received = signal.create()
        on_data_received.connect(process_data)
        on_data_received.emit(data)
    """
    return Signal()


# Global signal registry
_signals = {}


def register(name):
    """
    Register named signal.
    
    Args:
        name: Signal name
    
    Returns:
        Signal object
    
    Example:
        signal.register("user_login")
        signal.emit_global("user_login", user_id=123)
    """
    if name not in _signals:
        _signals[name] = Signal()
    return _signals[name]


def get(name):
    """
    Get registered signal.
    
    Args:
        name: Signal name
    
    Returns:
        Signal object or None
    
    Example:
        sig = signal.get("user_login")
        sig.connect(on_login)
    """
    return _signals.get(name)


def emit_global(name, *args, **kwargs):
    """
    Emit named signal.
    
    Args:
        name: Signal name
        args: Signal arguments
        kwargs: Signal keyword arguments
    
    Example:
        signal.emit_global("data_updated", key="value")
    """
    if name in _signals:
        _signals[name].emit(*args, **kwargs)


def unregister(name):
    """
    Unregister named signal.
    
    Args:
        name: Signal name
    
    Returns:
        True if unregistered, False if not found
    
    Example:
        signal.unregister("old_signal")
    """
    if name in _signals:
        del _signals[name]
        return True
    return False


def clear_all():
    """
    Clear all registered signals.
    
    Example:
        signal.clear_all()
    """
    _signals.clear()


def list_signals():
    """
    List all registered signal names.
    
    Returns:
        List of signal names
    
    Example:
        names = signal.list_signals()
    """
    return list(_signals.keys())


def connect_global(name, handler):
    """
    Connect handler to named signal (auto-creates if needed).
    
    Args:
        name: Signal name
        handler: Callback function
    
    Example:
        signal.connect_global("user_login", on_login)
    """
    sig = register(name)
    sig.connect(handler)


def disconnect_global(name, handler):
    """
    Disconnect handler from named signal.
    
    Args:
        name: Signal name
        handler: Callback function
    
    Example:
        signal.disconnect_global("user_login", on_login)
    """
    if name in _signals:
        _signals[name].disconnect(handler)


def once(handler):
    """
    Create one-time handler wrapper.
    
    Args:
        handler: Callback function
    
    Returns:
        Wrapped handler that disconnects after first call
    
    Example:
        sig = signal.create()
        sig.connect(signal.once(my_handler))
        sig.emit("data")  # Handler called
        sig.emit("data")  # Handler not called
    """
    called = [False]
    
    def wrapper(*args, **kwargs):
        if not called[0]:
            called[0] = True
            return handler(*args, **kwargs)
    
    return wrapper


def throttle(handler, interval=1.0):
    """
    Create throttled handler (limits call frequency).
    
    Args:
        handler: Callback function
        interval: Minimum time between calls (seconds)
    
    Returns:
        Throttled handler
    
    Example:
        sig = signal.create()
        sig.connect(signal.throttle(my_handler, 0.5))
    """
    import time
    last_call = [0]
    
    def wrapper(*args, **kwargs):
        now = time.time()
        if now - last_call[0] >= interval:
            last_call[0] = now
            return handler(*args, **kwargs)
    
    return wrapper


def debounce(handler, delay=0.5):
    """
    Create debounced handler (delays execution).
    
    Args:
        handler: Callback function
        delay: Delay in seconds
    
    Returns:
        Debounced handler
    
    Example:
        sig = signal.create()
        sig.connect(signal.debounce(my_handler, 0.3))
    """
    import threading
    timer = [None]
    
    def wrapper(*args, **kwargs):
        if timer[0]:
            timer[0].cancel()
        
        def delayed_call():
            handler(*args, **kwargs)
        
        timer[0] = threading.Timer(delay, delayed_call)
        timer[0].start()
    
    return wrapper


__all__ = [
    'Signal', 'create', 'register', 'get', 'emit_global',
    'unregister', 'clear_all', 'list_signals',
    'connect_global', 'disconnect_global', 'once', 'throttle', 'debounce'
]
