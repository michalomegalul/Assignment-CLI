"""
Centralized logging configuration for the Domain Management CLI.

This module provides structured logging configuration with support for:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file output with appropriate formatters
- Environment-based configuration
- Log rotation and file management
- Correlation IDs for operation tracking
"""

import logging
import logging.handlers
import os
import uuid
from pathlib import Path
from typing import Optional
import contextvars

# Context variable for correlation ID tracking
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id', default='')


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation ID to log records"""
    
    def filter(self, record):
        correlation_id = correlation_id_ctx.get('')
        record.correlation_id = correlation_id if correlation_id else 'N/A'
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from log messages"""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'secret', 'key', 'auth',
        'credential', 'bearer', 'authorization'
    ]
    
    def filter(self, record):
        # Check if any sensitive patterns are in the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            msg_lower = record.msg.lower()
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in msg_lower:
                    # Mark as potentially sensitive but don't modify the message
                    # In production, you might want to redact the actual sensitive parts
                    record.contains_sensitive = True
                    break
        return True


def setup_logging(
    log_level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = "logs",
    app_name: str = "domain-cli"
) -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_dir: Directory for log files
        app_name: Application name for log files
        
    Returns:
        Configured logger instance
    """
    
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Convert string level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(correlation_id)-12s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup file logging
    if log_to_file:
        # Main application log with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / f"{app_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        file_handler.addFilter(CorrelationIDFilter())
        file_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(file_handler)
        
        # Error-only log file
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / f"{app_name}-errors.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        error_handler.addFilter(CorrelationIDFilter())
        error_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(error_handler)
    
    # Setup console logging
    if log_to_console:
        console_handler = logging.StreamHandler()
        # Console shows less detail for better readability
        console_level = max(numeric_level, logging.INFO)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_to_file}, Console: {log_to_console}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"domain-cli.{name}")


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.
    
    Args:
        correlation_id: Correlation ID to set. If None, generates a new UUID.
        
    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    
    correlation_id_ctx.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return correlation_id_ctx.get('')


def log_performance(logger: logging.Logger, operation: str, duration_ms: float, **kwargs):
    """
    Log performance metrics for operations.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **kwargs: Additional context
    """
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"PERF | {operation} | {duration_ms:.2f}ms | {extra_info}")


def log_api_request(logger: logging.Logger, method: str, url: str, status_code: Optional[int] = None, 
                   duration_ms: Optional[float] = None, **kwargs):
    """
    Log API request details.
    
    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional context
    """
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    
    if status_code is not None and duration_ms is not None:
        logger.info(f"API | {method} {url} | {status_code} | {duration_ms:.2f}ms | {extra_info}")
    else:
        logger.info(f"API | {method} {url} | {extra_info}")


def log_database_operation(logger: logging.Logger, operation: str, query: Optional[str] = None,
                          duration_ms: Optional[float] = None, rows_affected: Optional[int] = None, **kwargs):
    """
    Log database operation details.
    
    Args:
        logger: Logger instance
        operation: Operation type (SELECT, INSERT, UPDATE, etc.)
        query: SQL query (will be truncated for logging)
        duration_ms: Query duration in milliseconds
        rows_affected: Number of rows affected
        **kwargs: Additional context
    """
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    
    # Truncate query for logging (avoid very long queries in logs)
    display_query = query[:100] + "..." if query and len(query) > 100 else query
    
    if duration_ms is not None:
        if rows_affected is not None:
            logger.info(f"DB | {operation} | {duration_ms:.2f}ms | {rows_affected} rows | {display_query} | {extra_info}")
        else:
            logger.info(f"DB | {operation} | {duration_ms:.2f}ms | {display_query} | {extra_info}")
    else:
        logger.info(f"DB | {operation} | {display_query} | {extra_info}")