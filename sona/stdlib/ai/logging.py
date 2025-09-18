"""
AI Logging System - Enterprise Grade
===================================

Comprehensive logging framework for AI operations with
structured logging, metrics collection, and audit trails.

Features:
- Structured logging with JSON format
- Performance metrics and timing
- Request/response correlation
- Audit trails for compliance
- Configurable log levels
- Integration with monitoring systems
"""

# Import standard library json avoiding local conflicts
import importlib
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


json = importlib.import_module('json')


@dataclass
class AILogEntry:
    """Structured log entry for AI operations"""
    timestamp: str
    correlation_id: str
    operation: str
    user_id: str | None
    session_id: str | None
    provider: str
    model: str
    prompt_length: int
    response_length: int
    latency_ms: float
    cache_hit: bool
    tokens_used: int
    cost_estimate: float
    status: str
    metadata: dict[str, Any]


class AILogger:
    """
    Enterprise AI logging system
    
    Provides structured logging for AI operations with:
    - Request/response correlation
    - Performance metrics
    - Cost tracking
    - Audit compliance
    """
    
    def __init__(self, log_level: str = "INFO", log_dir: Path | None = None):
        self.log_level = log_level.upper()
        self.log_dir = log_dir or Path.home() / '.sona' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up structured logger
        self.logger = self._setup_logger()
        
        # Metrics collection
        self.metrics = {
            'total_operations': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'avg_latency_ms': 0.0,
            'cache_hit_rate': 0.0,
            'error_rate': 0.0
        }
        
        self._operation_history = []
    
    def _setup_logger(self) -> logging.Logger:
        """Set up structured JSON logger"""
        logger = logging.getLogger('sona.ai.operations')
        logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler for structured logs
        log_file = self.log_dir / 'ai_operations.jsonl'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, self.log_level))
        
        # JSON formatter
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler for human-readable logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors
        
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_operation(self,
                     operation: str,
                     provider: str,
                     model: str,
                     prompt: str,
                     response: str,
                     latency_ms: float,
                     cache_hit: bool = False,
                     tokens_used: int = 0,
                     cost_estimate: float = 0.0,
                     user_id: str | None = None,
                     session_id: str | None = None,
                     correlation_id: str | None = None,
                     metadata: dict[str, Any] | None = None) -> str:
        """
        Log AI operation with full context
        
        Returns:
            Correlation ID for tracking
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        # Create structured log entry
        log_entry = AILogEntry(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            correlation_id=correlation_id,
            operation=operation,
            user_id=user_id,
            session_id=session_id,
            provider=provider,
            model=model,
            prompt_length=len(prompt),
            response_length=len(response),
            latency_ms=round(latency_ms, 2),
            cache_hit=cache_hit,
            tokens_used=tokens_used,
            cost_estimate=round(cost_estimate, 4),
            status='success',
            metadata=metadata or {}
        )
        
        # Log as JSON
        self.logger.info(json.dumps(asdict(log_entry)))
        
        # Update metrics
        self._update_metrics(log_entry)
        
        return correlation_id
    
    def log_error(self,
                 operation: str,
                 error: Exception,
                 prompt: str = "",
                 user_id: str | None = None,
                 session_id: str | None = None,
                 correlation_id: str | None = None,
                 metadata: dict[str, Any] | None = None) -> str:
        """Log AI operation error"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        error_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'correlation_id': correlation_id,
            'operation': operation,
            'user_id': user_id,
            'session_id': session_id,
            'status': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'prompt_length': len(prompt),
            'metadata': metadata or {}
        }
        
        self.logger.error(json.dumps(error_entry))
        
        return correlation_id
    
    def log_security_event(self,
                          event_type: str,
                          description: str,
                          threat_level: str,
                          user_id: str | None = None,
                          metadata: dict[str, Any] | None = None) -> None:
        """Log security-related events"""
        security_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': 'security_event',
            'security_event_type': event_type,
            'description': description,
            'threat_level': threat_level,
            'user_id': user_id,
            'metadata': metadata or {}
        }
        
        self.logger.warning(json.dumps(security_entry))
    
    def log_performance_metric(self,
                             metric_name: str,
                             value: float,
                             unit: str,
                             metadata: dict[str, Any] | None = None) -> None:
        """Log performance metrics"""
        metric_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': 'performance_metric',
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'metadata': metadata or {}
        }
        
        self.logger.info(json.dumps(metric_entry))
    
    def _update_metrics(self, log_entry: AILogEntry) -> None:
        """Update running metrics"""
        self.metrics['total_operations'] += 1
        self.metrics['total_tokens'] += log_entry.tokens_used
        self.metrics['total_cost'] += log_entry.cost_estimate
        
        # Store operation for rolling calculations
        self._operation_history.append(log_entry)
        
        # Keep only last 1000 operations for metrics
        if len(self._operation_history) > 1000:
            self._operation_history = self._operation_history[-1000:]
        
        # Calculate rolling averages
        if self._operation_history:
            total_ops = len(self._operation_history)
            
            # Average latency
            avg_latency = sum(op.latency_ms for op in self._operation_history) / total_ops
            self.metrics['avg_latency_ms'] = round(avg_latency, 2)
            
            # Cache hit rate
            cache_hits = sum(1 for op in self._operation_history if op.cache_hit)
            self.metrics['cache_hit_rate'] = round((cache_hits / total_ops) * 100, 2)
            
            # Error rate (based on status)
            errors = sum(1 for op in self._operation_history if op.status == 'error')
            self.metrics['error_rate'] = round((errors / total_ops) * 100, 2)
    
    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics"""
        return dict(self.metrics)
    
    def get_operation_history(self, limit: int = 100) -> list:
        """Get recent operation history"""
        return [asdict(op) for op in self._operation_history[-limit:]]
    
    def search_logs(self,
                   start_time: str | None = None,
                   end_time: str | None = None,
                   user_id: str | None = None,
                   operation: str | None = None,
                   status: str | None = None,
                   limit: int = 100) -> list:
        """Search operation logs with filters"""
        # This would typically query a database or search index
        # For now, search the in-memory history
        filtered_ops = []
        
        for op in self._operation_history:
            # Apply filters
            if start_time and op.timestamp < start_time:
                continue
            if end_time and op.timestamp > end_time:
                continue
            if user_id and op.user_id != user_id:
                continue
            if operation and op.operation != operation:
                continue
            if status and op.status != status:
                continue
            
            filtered_ops.append(asdict(op))
            
            if len(filtered_ops) >= limit:
                break
        
        return filtered_ops


class ContextManager:
    """Manages logging context for request correlation"""
    
    def __init__(self, logger: AILogger):
        self.logger = logger
        self._context_stack = []
    
    def start_operation(self,
                       operation: str,
                       user_id: str | None = None,
                       session_id: str | None = None) -> str:
        """Start a new operation context"""
        correlation_id = str(uuid.uuid4())
        
        context = {
            'correlation_id': correlation_id,
            'operation': operation,
            'user_id': user_id,
            'session_id': session_id,
            'start_time': time.time()
        }
        
        self._context_stack.append(context)
        
        # Log operation start
        start_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': 'operation_start',
            'correlation_id': correlation_id,
            'operation': operation,
            'user_id': user_id,
            'session_id': session_id
        }
        
        self.logger.logger.info(json.dumps(start_entry))
        
        return correlation_id
    
    def end_operation(self, correlation_id: str, status: str = 'success') -> None:
        """End operation context"""
        # Find context
        context = None
        for i, ctx in enumerate(self._context_stack):
            if ctx['correlation_id'] == correlation_id:
                context = self._context_stack.pop(i)
                break
        
        if not context:
            return
        
        # Calculate duration
        duration_ms = (time.time() - context['start_time']) * 1000
        
        # Log operation end
        end_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': 'operation_end',
            'correlation_id': correlation_id,
            'operation': context['operation'],
            'user_id': context['user_id'],
            'session_id': context['session_id'],
            'duration_ms': round(duration_ms, 2),
            'status': status
        }
        
        self.logger.logger.info(json.dumps(end_entry))


# Global logger instance
_global_logger: AILogger | None = None


def get_global_logger() -> AILogger:
    """Get or create global AI logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AILogger()
    return _global_logger


def configure_logging(log_level: str = "INFO",
                     log_dir: Path | None = None) -> AILogger:
    """Configure global AI logging"""
    global _global_logger
    _global_logger = AILogger(log_level, log_dir)
    return _global_logger
