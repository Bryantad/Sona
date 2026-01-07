"""
logging - Logging utilities for Sona stdlib

Provides structured logging with multiple levels:
- logger: Create a named logger instance
- Supports: debug, info, warn, error levels
- Context-aware logging with structured data
"""

import sys
import datetime
import json


class Logger:
    """Logger instance with multiple log levels."""
    
    def __init__(self, name):
        """
        Create a new logger.
        
        Args:
            name: Logger name (typically module or component name)
        """
        self.name = name
        self.level = 'INFO'  # Default level
    
    def _log(self, level, message, context=None):
        """Internal method to format and write log messages."""
        timestamp = datetime.datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'logger': self.name,
            'message': message
        }
        
        if context:
            log_entry['context'] = context
        
        # Format as JSON for structured logging
        log_line = json.dumps(log_entry, default=str)
        
        # Write to appropriate stream
        if level in ('ERROR', 'WARN'):
            print(log_line, file=sys.stderr)
        else:
            print(log_line, file=sys.stdout)
    
    def debug(self, message, context=None):
        """
        Log debug message.
        
        Args:
            message: Debug message
            context: Optional dict with additional context
        
        Example:
            logger.debug("Processing item", context={"item_id": 123})
        """
        self._log('DEBUG', message, context)
    
    def info(self, message, context=None):
        """
        Log info message.
        
        Args:
            message: Info message
            context: Optional dict with additional context
        
        Example:
            logger.info("Application started", context={"version": "1.0"})
        """
        self._log('INFO', message, context)
    
    def warn(self, message, context=None):
        """
        Log warning message.
        
        Args:
            message: Warning message
            context: Optional dict with additional context
        
        Example:
            logger.warn("Deprecated API used", context={"api": "old_func"})
        """
        self._log('WARN', message, context)
    
    def error(self, message, context=None):
        """
        Log error message.
        
        Args:
            message: Error message
            context: Optional dict with additional context
        
        Example:
            logger.error("Failed to connect", context={"host": "db.example.com"})
        """
        self._log('ERROR', message, context)


def logger(name):
    """
    Create a named logger instance.
    
    Args:
        name: Logger name (typically module or component name)
    
    Returns:
        Logger instance
    
    Example:
        log = logging.logger("myapp")
        log.info("Starting application")
        log.error("Something went wrong", context={"error": "timeout"})
    """
    return Logger(name)


# Global logger registry for reuse
_loggers = {}


def get_logger(name):
    """
    Get or create a cached logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Cached Logger instance
    """
    if name not in _loggers:
        _loggers[name] = Logger(name)
    return _loggers[name]


def set_level(logger_obj, level):
    """
    Set logging level for logger.
    
    Args:
        logger_obj: Logger instance
        level: Level string (DEBUG, INFO, WARN, ERROR)
    
    Example:
        logging.set_level(log, "DEBUG")
    """
    logger_obj.level = level.upper()


def log_to_file(filename, logger_obj=None):
    """
    Redirect logger output to file.
    
    Args:
        filename: Output file path
        logger_obj: Logger instance (None = all loggers)
    
    Example:
        logging.log_to_file("app.log", log)
    """
    # Note: Simplified implementation for Sona
    # In production, would redirect sys.stdout/stderr
    pass


def with_context(**context):
    """
    Create logging context manager.
    
    Args:
        context: Context key-value pairs
    
    Returns:
        Context manager
    
    Example:
        with logging.with_context(user_id=123, request_id="abc"):
            log.info("Processing request")
    """
    class LogContext:
        def __init__(self, ctx):
            self.ctx = ctx
            self.old_context = {}
        
        def __enter__(self):
            return self.ctx
        
        def __exit__(self, *args):
            pass
    
    return LogContext(context)


def exception(logger_obj, exc, message=None):
    """
    Log exception with traceback.
    
    Args:
        logger_obj: Logger instance
        exc: Exception object
        message: Optional message
    
    Example:
        try:
            risky_operation()
        except Exception as e:
            logging.exception(log, e, "Operation failed")
    """
    import traceback
    context = {
        'exception_type': type(exc).__name__,
        'exception_message': str(exc),
        'traceback': traceback.format_exc()
    }
    msg = message or "Exception occurred"
    logger_obj.error(msg, context=context)


def metric(logger_obj, name, value, tags=None):
    """
    Log metric/measurement.
    
    Args:
        logger_obj: Logger instance
        name: Metric name
        value: Metric value
        tags: Optional dict of tags
    
    Example:
        logging.metric(log, "response_time", 0.123, {"endpoint": "/api"})
    """
    context = {'metric': name, 'value': value}
    if tags:
        context['tags'] = tags
    logger_obj.info(f"METRIC: {name}", context=context)


__all__ = [
    'Logger',
    'logger',
    'get_logger',
    'set_level',
    'log_to_file',
    'with_context',
    'exception',
    'metric'
]
