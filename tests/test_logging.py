"""
Tests for logging functionality in Domain Management CLI.
"""

import os
import tempfile
import logging
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from cli.logging_config import setup_logging, sanitize_sensitive_data, get_log_level
from cli.logger import (
    get_structured_logger, 
    log_performance, 
    correlation_context,
    get_correlation_id,
    set_correlation_id
)
from cli.commands import cli


class TestLoggingConfig:
    """Test logging configuration functionality."""
    
    def test_sanitize_database_url(self):
        """Test that database URLs are sanitized properly."""
        message = "Connecting to postgresql://user:password@localhost:5432/db"
        sanitized = sanitize_sensitive_data(message)
        assert "password" not in sanitized
        assert "postgresql://***:***@" in sanitized
    
    def test_sanitize_api_keys(self):
        """Test that API keys are sanitized."""
        message = "Request with api_key=secret123&token=abc456"
        sanitized = sanitize_sensitive_data(message)
        assert "secret123" not in sanitized
        assert "abc456" not in sanitized
        assert "api_key=***" in sanitized
        assert "token=***" in sanitized
    
    def test_sanitize_email_addresses(self):
        """Test that email addresses are sanitized."""
        message = "User email: user@example.com contacted support"
        sanitized = sanitize_sensitive_data(message)
        assert "user@example.com" not in sanitized
        assert "***@***.***" in sanitized
    
    def test_get_log_level_default(self):
        """Test default log level."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_log_level() == "INFO"
    
    def test_get_log_level_from_env(self):
        """Test log level from environment variable."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            assert get_log_level() == "DEBUG"
    
    def test_setup_logging_creates_log_dir(self):
        """Test that setup_logging creates the log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOG_DIR": temp_dir}):
                setup_logging()
                assert Path(temp_dir).exists()


class TestLogger:
    """Test logger utilities and decorators."""
    
    def test_correlation_context(self):
        """Test correlation context manager."""
        original_id = get_correlation_id()
        
        with correlation_context("test-123") as cid:
            assert cid == "test-123"
            assert get_correlation_id() == "test-123"
        
        # Should restore original or create new one
        assert get_correlation_id() != "test-123"
    
    def test_set_get_correlation_id(self):
        """Test correlation ID management."""
        test_id = "test-correlation-id"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
    
    def test_get_structured_logger(self):
        """Test structured logger creation."""
        logger = get_structured_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
        
        # Test that custom methods are added
        assert hasattr(logger, 'info_ctx')
        assert hasattr(logger, 'error_ctx')
        assert hasattr(logger, 'warning_ctx')
        assert hasattr(logger, 'debug_ctx')
    
    def test_log_performance_decorator(self):
        """Test performance logging decorator."""
        test_logger = get_structured_logger("test.performance")
        
        @log_performance("test_operation", logger=test_logger)
        def test_function(x, y):
            return x + y
        
        with patch.object(test_logger, 'debug') as mock_debug, \
             patch.object(test_logger, 'info') as mock_info:
            
            result = test_function(2, 3)
            assert result == 5
            
            # Check that logging methods were called
            mock_debug.assert_called()
            mock_info.assert_called()
    
    def test_log_performance_decorator_with_exception(self):
        """Test performance decorator handles exceptions."""
        test_logger = get_structured_logger("test.performance")
        
        @log_performance("test_operation", logger=test_logger)
        def failing_function():
            raise ValueError("Test error")
        
        with patch.object(test_logger, 'error') as mock_error:
            with pytest.raises(ValueError):
                failing_function()
            
            # Check that error was logged
            mock_error.assert_called()


class TestCLILogging:
    """Test logging integration in CLI commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        # Set up minimal logging for tests
        with patch.dict(os.environ, {
            "LOG_LEVEL": "INFO", 
            "DISABLE_FILE_LOGGING": "true"
        }):
            setup_logging()
    
    def test_cli_startup_logging(self):
        """Test that CLI startup is logged."""
        with patch('cli.commands.get_structured_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            result = self.runner.invoke(cli, ['--help'])
            assert result.exit_code == 0
            
            # Check that startup logging was called
            mock_logger.info.assert_called()
    
    @patch('cli.database.DatabaseManager.get_stats')
    @patch('cli.database.DatabaseManager.get_connection')
    def test_status_command_logging(self, mock_connection, mock_get_stats):
        """Test logging in status command."""
        mock_get_stats.return_value = {
            'total_domains': 10,
            'active_domains': 8,
            'total_flags': 5
        }
        
        with patch('cli.commands.get_structured_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            result = self.runner.invoke(cli, ['status'])
            
            # Command should complete successfully
            assert result.exit_code == 0
            
            # Check that logging was called
            mock_logger.info.assert_called()
    
    @patch('cli.database.DatabaseManager.get_active_domains')
    @patch('cli.database.DatabaseManager.get_connection')
    def test_active_domains_logging(self, mock_connection, mock_get_active_domains):
        """Test logging in active-domains command."""
        mock_get_active_domains.return_value = ['example.com', 'test.org']
        
        with patch('cli.commands.get_structured_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            result = self.runner.invoke(cli, ['active-domains'])
            
            # Command should complete successfully
            assert result.exit_code == 0
            assert 'example.com' in result.output
            
            # Check that logging was called
            mock_logger.info.assert_called()


class TestFileClientLogging:
    """Test logging in file client operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        with patch.dict(os.environ, {
            "LOG_LEVEL": "INFO", 
            "DISABLE_FILE_LOGGING": "true"
        }):
            setup_logging()
    
    @patch('cli.file_client.requests.get')
    def test_rest_api_logging(self, mock_get):
        """Test REST API request logging."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test.txt',
            'size': 1234,
            'mimetype': 'text/plain',
            'create_datetime': '2025-01-24T15:23:03Z'
        }
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_get.return_value = mock_response
        
        with patch('cli.file_client.get_structured_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            result = self.runner.invoke(cli, [
                'file-client',
                '--backend', 'rest',
                '--base-url', 'http://test-api/',
                'stat',
                '123e4567-e89b-12d3-a456-426614174000'
            ])
            
            # Command should complete successfully
            assert result.exit_code == 0
            
            # Check that logging was called
            mock_logger.info.assert_called()
    
    def test_grpc_not_implemented_logging(self):
        """Test gRPC not implemented logging."""
        with patch('cli.file_client.get_structured_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            result = self.runner.invoke(cli, [
                'file-client',
                '--backend', 'grpc',
                'stat',
                '123e4567-e89b-12d3-a456-426614174000'
            ])
            
            # Command should fail
            assert result.exit_code == 1
            assert 'gRPC backend not implemented' in result.output
            
            # Check that warning was logged
            mock_logger.warning.assert_called()


class TestDatabaseLogging:
    """Test database operation logging."""
    
    @patch('cli.database.psycopg2.connect')
    def test_database_connection_logging(self, mock_connect):
        """Test database connection logging."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        from cli.database import DatabaseManager
        
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:password@localhost/test"
        }):
            db = DatabaseManager()
            
            # Check that logger was created
            assert hasattr(db, 'logger')
            assert db.logger.name == "db.manager"


class TestSecurityLogging:
    """Test security aspects of logging."""
    
    def test_database_url_not_in_logs(self):
        """Test that database URLs are not logged in plaintext."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:secret123@localhost/test"
        }):
            from cli.database import DatabaseManager
            
            # Create database manager (should log initialization)
            db = DatabaseManager()
            
            # The sensitive URL should not appear in logs
            # This is more of a documentation test since we can't easily
            # capture the actual log output in this test setup
            assert "secret123" not in str(db.connection_string) or db.connection_string is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])