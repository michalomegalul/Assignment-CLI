"""
Example usage and configuration for the Domain Management CLI logging system.

This file demonstrates how to configure and use the logging system in different
environments and scenarios.
"""

import os
from cli.logging_config import setup_logging
from cli.logger import get_structured_logger, correlation_context
from cli.commands import cli

# Environment variable examples
example_configs = {
    "development": {
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "console", 
        "LOG_SQL_QUERIES": "true",
        "DISABLE_FILE_LOGGING": "false"
    },
    "production": {
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "json",
        "LOG_SQL_QUERIES": "false", 
        "LOG_DIR": "/var/log/domain-cli",
        "DISABLE_FILE_LOGGING": "false"
    },
    "testing": {
        "LOG_LEVEL": "WARNING",
        "LOG_FORMAT": "console",
        "DISABLE_FILE_LOGGING": "true"
    }
}

def demonstrate_logging():
    """Demonstrate various logging features."""
    print("=== Domain Management CLI Logging System Demo ===\n")
    
    # Set up logging
    setup_logging()
    logger = get_structured_logger("demo")
    
    # Basic logging
    print("1. Basic structured logging:")
    logger.info("Application started", extra={
        'extra_fields': {
            'version': '1.0.0',
            'environment': 'demo'
        }
    })
    
    # Correlation context
    print("\n2. Correlation context example:")
    with correlation_context("demo-operation-123") as cid:
        logger.info("Processing request", extra={
            'extra_fields': {
                'user_id': 'demo_user',
                'action': 'list_domains'
            }
        })
        
        # Simulate error
        try:
            raise ValueError("Demo error for logging")
        except Exception as e:
            logger.error("Operation failed", extra={
                'extra_fields': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
    
    # Performance logging
    print("\n3. Performance metrics example:")
    import time
    from cli.logger import performance_timer
    
    with performance_timer("demo_operation", logger):
        time.sleep(0.1)  # Simulate work
        logger.info("Work completed")
    
    print("\n4. Security sanitization example:")
    # This will be sanitized in logs
    logger.info("Database connection: postgresql://user:secretpass@localhost:5432/db")
    logger.info("API request with api_key=super_secret_key")
    
    print("\n=== Demo completed ===")

def show_environment_examples():
    """Show different environment configurations."""
    print("\n=== Environment Configuration Examples ===\n")
    
    for env_name, config in example_configs.items():
        print(f"{env_name.upper()} Environment:")
        for key, value in config.items():
            print(f"  export {key}={value}")
        print()
    
    print("Usage examples:")
    print("# Development with debug logging")
    print("LOG_LEVEL=DEBUG LOG_SQL_QUERIES=true python -m cli.commands status")
    print()
    print("# Production with JSON logging")  
    print("LOG_FORMAT=json LOG_LEVEL=INFO python -m cli.commands active-domains")
    print()
    print("# Testing with minimal logging")
    print("LOG_LEVEL=WARNING DISABLE_FILE_LOGGING=true python -m cli.commands --help")

if __name__ == "__main__":
    demonstrate_logging()
    show_environment_examples()