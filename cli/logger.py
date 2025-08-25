"""
Logger utilities and decorators for Domain Management CLI.

This module provides:
- Performance measurement decorators
- Correlation ID management
- Structured logging helpers
- Database query logging utilities
- API request logging utilities
"""

import logging
import time
import functools
import uuid
from typing import Any, Callable, Dict, Optional, TypeVar, cast
from contextlib import contextmanager
import threading
from dataclasses import dataclass, field
from datetime import datetime

# Type hints
F = TypeVar('F', bound=Callable[..., Any])

# Thread-local storage for correlation IDs
_thread_local = threading.local()


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark the operation as finished."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error_message = error_message


def get_correlation_id() -> str:
    """Get the current correlation ID, creating one if it doesn't exist."""
    if not hasattr(_thread_local, 'correlation_id'):
        _thread_local.correlation_id = str(uuid.uuid4())
    return _thread_local.correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current thread."""
    _thread_local.correlation_id = correlation_id


@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """Context manager for correlation ID scoping."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    old_id = getattr(_thread_local, 'correlation_id', None)
    try:
        set_correlation_id(correlation_id)
        yield correlation_id
    finally:
        if old_id is not None:
            _thread_local.correlation_id = old_id
        elif hasattr(_thread_local, 'correlation_id'):
            delattr(_thread_local, 'correlation_id')


def get_structured_logger(name: str) -> logging.Logger:
    """Get a logger with structured logging capabilities."""
    logger = logging.getLogger(name)
    
    # Add custom methods for structured logging
    def log_with_context(level: int, message: str, **kwargs) -> None:
        """Log with additional context."""
        extra_fields = kwargs.copy()
        extra_fields['correlation_id'] = get_correlation_id()
        
        logger.log(level, message, extra={'extra_fields': extra_fields})
    
    def info_with_context(message: str, **kwargs) -> None:
        """Log info with context."""
        log_with_context(logging.INFO, message, **kwargs)
    
    def error_with_context(message: str, **kwargs) -> None:
        """Log error with context."""
        log_with_context(logging.ERROR, message, **kwargs)
    
    def warning_with_context(message: str, **kwargs) -> None:
        """Log warning with context."""
        log_with_context(logging.WARNING, message, **kwargs)
        
    def debug_with_context(message: str, **kwargs) -> None:
        """Log debug with context."""
        log_with_context(logging.DEBUG, message, **kwargs)
    
    # Monkey patch the logger (not ideal but works for this demo)
    logger.info_ctx = info_with_context
    logger.error_ctx = error_with_context
    logger.warning_ctx = warning_with_context
    logger.debug_ctx = debug_with_context
    
    return logger


def log_performance(
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    log_args: bool = False,
    log_result: bool = False,
    min_duration_ms: float = 0.0
) -> Callable[[F], F]:
    """
    Decorator to log function performance metrics.
    
    Args:
        operation_name: Name of the operation for logging
        logger: Logger to use (if None, creates one based on function module)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        min_duration_ms: Only log if duration exceeds this threshold
    """
    def decorator(func: F) -> F:
        if logger is None:
            func_logger = get_structured_logger(f"{func.__module__}.{func.__name__}")
        else:
            func_logger = logger
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = PerformanceMetrics(operation_name)
            correlation_id = get_correlation_id()
            
            # Log function entry
            log_data = {
                'operation': operation_name,
                'function': func.__name__,
                'correlation_id': correlation_id,
            }
            
            if log_args:
                log_data['args'] = str(args)[:500]  # Limit arg length
                log_data['kwargs'] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            func_logger.debug("Operation started", extra={'extra_fields': log_data})
            
            try:
                result = func(*args, **kwargs)
                metrics.finish(success=True)
                
                # Log successful completion
                if metrics.duration_ms >= min_duration_ms:
                    log_data.update({
                        'duration_ms': metrics.duration_ms,
                        'success': True,
                    })
                    
                    if log_result and result is not None:
                        log_data['result_type'] = type(result).__name__
                        if hasattr(result, '__len__'):
                            log_data['result_length'] = len(result)
                    
                    func_logger.info("Operation completed", extra={'extra_fields': log_data})
                
                return result
                
            except Exception as e:
                metrics.finish(success=False, error_message=str(e))
                
                # Log error
                log_data.update({
                    'duration_ms': metrics.duration_ms,
                    'success': False,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                })
                
                func_logger.error("Operation failed", extra={'extra_fields': log_data}, exc_info=True)
                raise
                
        return cast(F, wrapper)
    return decorator


def log_database_query(
    query_name: str,
    logger: Optional[logging.Logger] = None,
    log_query: bool = None,
    log_params: bool = False
) -> Callable[[F], F]:
    """
    Decorator specifically for database query logging.
    
    Args:
        query_name: Name of the database query
        logger: Logger to use
        log_query: Whether to log the SQL query (respects LOG_SQL_QUERIES env var)
        log_params: Whether to log query parameters
    """
    if log_query is None:
        from .logging_config import should_enable_sql_logging
        log_query = should_enable_sql_logging()
    
    def decorator(func: F) -> F:
        if logger is None:
            func_logger = get_structured_logger(f"db.{func.__name__}")
        else:
            func_logger = logger
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_id = get_correlation_id()
            
            log_data = {
                'query_name': query_name,
                'correlation_id': correlation_id,
                'operation_type': 'database_query'
            }
            
            if log_params and args:
                log_data['params'] = str(args[1:])[:500]  # Skip 'self' parameter
            
            func_logger.debug("Database query started", extra={'extra_fields': log_data})
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                log_data.update({
                    'duration_ms': duration_ms,
                    'success': True,
                })
                
                if result is not None and hasattr(result, '__len__'):
                    log_data['result_count'] = len(result)
                
                func_logger.info("Database query completed", extra={'extra_fields': log_data})
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_data.update({
                    'duration_ms': duration_ms,
                    'success': False,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                })
                
                func_logger.error("Database query failed", extra={'extra_fields': log_data}, exc_info=True)
                raise
                
        return cast(F, wrapper)
    return decorator


def log_api_request(
    service_name: str,
    logger: Optional[logging.Logger] = None,
    log_request: bool = True,
    log_response: bool = True
) -> Callable[[F], F]:
    """
    Decorator for API request logging.
    
    Args:
        service_name: Name of the external service
        logger: Logger to use
        log_request: Whether to log request details
        log_response: Whether to log response details
    """
    def decorator(func: F) -> F:
        if logger is None:
            func_logger = get_structured_logger(f"api.{func.__name__}")
        else:
            func_logger = logger
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_id = get_correlation_id()
            
            log_data = {
                'service_name': service_name,
                'correlation_id': correlation_id,
                'operation_type': 'api_request'
            }
            
            if log_request:
                # Try to extract URL and method from common patterns
                if 'url' in kwargs:
                    log_data['request_url'] = kwargs['url']
                if 'method' in kwargs:
                    log_data['request_method'] = kwargs['method']
            
            func_logger.debug("API request started", extra={'extra_fields': log_data})
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                log_data.update({
                    'duration_ms': duration_ms,
                    'success': True,
                })
                
                if log_response and hasattr(result, 'status_code'):
                    log_data['response_status'] = result.status_code
                if log_response and hasattr(result, 'headers'):
                    log_data['response_content_type'] = result.headers.get('content-type')
                
                func_logger.info("API request completed", extra={'extra_fields': log_data})
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_data.update({
                    'duration_ms': duration_ms,
                    'success': False,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                })
                
                func_logger.error("API request failed", extra={'extra_fields': log_data}, exc_info=True)
                raise
                
        return cast(F, wrapper)
    return decorator


def log_cli_command(command_name: str, logger: Optional[logging.Logger] = None) -> Callable[[F], F]:
    """
    Decorator for CLI command logging.
    
    Args:
        command_name: Name of the CLI command
        logger: Logger to use
    """
    def decorator(func: F) -> F:
        if logger is None:
            func_logger = get_structured_logger(f"cli.{command_name}")
        else:
            func_logger = logger
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create new correlation ID for each command
            with correlation_context() as correlation_id:
                start_time = time.time()
                
                log_data = {
                    'command': command_name,
                    'correlation_id': correlation_id,
                    'operation_type': 'cli_command',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                
                func_logger.info("CLI command started", extra={'extra_fields': log_data})
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    log_data.update({
                        'duration_ms': duration_ms,
                        'success': True,
                    })
                    
                    func_logger.info("CLI command completed", extra={'extra_fields': log_data})
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    log_data.update({
                        'duration_ms': duration_ms,
                        'success': False,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                    })
                    
                    func_logger.error("CLI command failed", extra={'extra_fields': log_data}, exc_info=True)
                    raise
                    
        return cast(F, wrapper)
    return decorator


@contextmanager
def performance_timer(operation_name: str, logger: Optional[logging.Logger] = None):
    """Context manager for timing operations."""
    if logger is None:
        logger = get_structured_logger(__name__)
    
    start_time = time.time()
    correlation_id = get_correlation_id()
    
    logger.debug("Operation started", extra={
        'extra_fields': {
            'operation': operation_name,
            'correlation_id': correlation_id
        }
    })
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        logger.info("Operation completed", extra={
            'extra_fields': {
                'operation': operation_name,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'success': True
            }
        })
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Operation failed", extra={
            'extra_fields': {
                'operation': operation_name,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'success': False,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }, exc_info=True)
        raise


def create_audit_log_entry(
    action: str,
    resource: str,
    user: Optional[str] = None,
    **additional_data
) -> None:
    """Create an audit log entry for important operations."""
    audit_logger = get_structured_logger("audit")
    
    audit_data = {
        'action': action,
        'resource': resource,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'correlation_id': get_correlation_id(),
        **additional_data
    }
    
    if user:
        audit_data['user'] = user
    
    audit_logger.info("Audit log entry", extra={'extra_fields': audit_data})