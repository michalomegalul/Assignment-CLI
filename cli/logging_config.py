"""
Centralized logging configuration for Domain Management CLI.

This module provides:
- Structured JSON logging for production
- Colorized console logging for development
- Configurable log levels via environment variables
- Log rotation to prevent disk space issues
- Security-conscious logging (sensitive data filtering)
- Performance tracking capabilities
"""

import os
import sys
import logging
import logging.config
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
import colorlog
import json
import re
from functools import wraps


# Security patterns to sanitize from logs
SENSITIVE_PATTERNS = [
    # Database URLs with credentials
    re.compile(r'postgresql://[^:]+:[^@]+@', re.IGNORECASE),
    # Email addresses (optional privacy measure)  
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
]


def sanitize_sensitive_data(message: str) -> str:
    """Remove sensitive information from log messages."""
    sanitized = message
    for pattern in SENSITIVE_PATTERNS:
        if 'postgresql://' in sanitized:
            sanitized = pattern.sub('postgresql://***:***@', sanitized)
        elif any(keyword in sanitized.lower() for keyword in ['api_key=', 'token=', 'password=']):
            # Use a simpler replacement for API keys and tokens
            sanitized = re.sub(r'(api_key|token|password)=[^&\s]+', r'\1=***', sanitized, flags=re.IGNORECASE)
        elif '@' in sanitized and '.' in sanitized:
            sanitized = pattern.sub('***@***.***', sanitized)
    return sanitized


class SecurityFilter(logging.Filter):
    """Filter to sanitize sensitive information from log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = sanitize_sensitive_data(record.msg)
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                sanitize_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
            
        # Add performance metrics if present
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
            
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_entry, ensure_ascii=False)


def get_log_level() -> str:
    """Get log level from environment variable."""
    return os.getenv('LOG_LEVEL', 'INFO').upper()


def get_log_format() -> str:
    """Get log format preference from environment."""
    return os.getenv('LOG_FORMAT', 'console').lower()  # console or json


def get_log_dir() -> Path:
    """Get log directory, creating it if necessary."""
    log_dir = Path(os.getenv('LOG_DIR', 'logs'))
    log_dir.mkdir(exist_ok=True)
    return log_dir


def should_enable_sql_logging() -> bool:
    """Check if SQL query logging should be enabled."""
    return os.getenv('LOG_SQL_QUERIES', 'false').lower() in ('true', '1', 'yes')


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = get_log_level()
    log_format = get_log_format()
    log_dir = get_log_dir()
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Create formatters
    if log_format == 'json':
        formatter = JSONFormatter()
        console_formatter = JSONFormatter()
    else:
        # Colorized console formatter
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        # Simple formatter for file logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SecurityFilter())
    
    # File handlers with rotation
    if not os.getenv('DISABLE_FILE_LOGGING', '').lower() in ('true', '1', 'yes'):
        # Main application log
        app_log_file = log_dir / 'app.log'
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(getattr(logging, log_level, logging.INFO))
        app_handler.setFormatter(formatter)
        app_handler.addFilter(SecurityFilter())
        
        # Error log (ERROR and CRITICAL only)
        error_log_file = log_dir / 'error.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(SecurityFilter())
        
        # Configure root logger
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))
        root_logger.addHandler(console_handler)
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
    else:
        # Console only
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))
        root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('psycopg2').setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            'extra_fields': {
                'log_level': log_level,
                'log_format': log_format,
                'file_logging_enabled': not os.getenv('DISABLE_FILE_LOGGING', '').lower() in ('true', '1', 'yes'),
                'sql_logging_enabled': should_enable_sql_logging()
            }
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def setup_request_logging():
    """Setup request-specific logging with correlation IDs."""
    import uuid
    correlation_id = str(uuid.uuid4())
    
    class CorrelationFilter(logging.Filter):
        def filter(self, record):
            record.correlation_id = correlation_id
            return True
    
    # Add correlation filter to all handlers
    for handler in logging.getLogger().handlers:
        handler.addFilter(CorrelationFilter())
    
    return correlation_id


# Configuration dictionary for logging.config.dictConfig (alternative approach)
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': JSONFormatter,
        },
        'console': {
            '()': colorlog.ColoredFormatter,
            'format': '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        },
        'file': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'filters': {
        'security': {
            '()': SecurityFilter,
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': get_log_level(),
            'formatter': 'console',
            'filters': ['security'],
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': get_log_level(),
            'formatter': 'file',
            'filters': ['security'],
            'filename': str(get_log_dir() / 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'file',
            'filters': ['security'],
            'filename': str(get_log_dir() / 'error.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        '': {  # root logger
            'level': get_log_level(),
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        },
        'cli': {
            'level': get_log_level(),
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        }
    }
}