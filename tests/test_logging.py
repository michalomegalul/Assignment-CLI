"""
Test cases for the logging system functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli.logging_config import (
    setup_logging, 
    get_logger, 
    set_correlation_id, 
    get_correlation_id,
    log_performance,
    log_api_request,
    log_database_operation
)


class TestLoggingSystem(unittest.TestCase):
    """Test cases for the logging system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        self.addCleanup(self._cleanup_logs)
    
    def _cleanup_logs(self):
        """Clean up test log files"""
        import shutil
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
    
    def test_logging_setup(self):
        """Test basic logging setup"""
        logger = setup_logging(
            log_level='INFO',
            log_to_file=True,
            log_to_console=False,
            log_dir=self.test_log_dir,
            app_name='test-app'
        )
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test-app')
        
        # Check that log files are created
        log_file = Path(self.test_log_dir) / 'test-app.log'
        error_log_file = Path(self.test_log_dir) / 'test-app-errors.log'
        
        # Log a message to trigger file creation
        test_logger = get_logger('test')
        test_logger.info('Test message')
        
        self.assertTrue(log_file.exists())
        self.assertTrue(error_log_file.exists())
    
    def test_correlation_id_management(self):
        """Test correlation ID functionality"""
        # Test automatic generation
        correlation_id1 = set_correlation_id()
        self.assertIsNotNone(correlation_id1)
        self.assertEqual(get_correlation_id(), correlation_id1)
        
        # Test manual setting
        manual_id = "TEST-123"
        correlation_id2 = set_correlation_id(manual_id)
        self.assertEqual(correlation_id2, manual_id)
        self.assertEqual(get_correlation_id(), manual_id)
        
        # Test new auto-generation
        correlation_id3 = set_correlation_id()
        self.assertNotEqual(correlation_id3, correlation_id1)
        self.assertNotEqual(correlation_id3, manual_id)
    
    def test_log_levels(self):
        """Test different log levels"""
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            with self.subTest(level=level):
                logger = setup_logging(
                    log_level=level,
                    log_to_file=True,
                    log_to_console=False,
                    log_dir=self.test_log_dir,
                    app_name=f'test-{level.lower()}'
                )
                
                test_logger = get_logger('level_test')
                
                # All these should work without error
                test_logger.debug('Debug message')
                test_logger.info('Info message')
                test_logger.warning('Warning message')
                test_logger.error('Error message')
                test_logger.critical('Critical message')
    
    def test_performance_logging(self):
        """Test performance logging helper"""
        setup_logging(
            log_level='INFO',
            log_to_file=False,
            log_to_console=False,
            log_dir=self.test_log_dir
        )
        
        logger = get_logger('perf_test')
        
        # Mock the logger to capture calls
        with patch.object(logger, 'info') as mock_info:
            log_performance(
                logger, 
                'test_operation', 
                123.45, 
                param1='value1', 
                param2='value2'
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            self.assertIn('PERF', call_args)
            self.assertIn('test_operation', call_args)
            self.assertIn('123.45ms', call_args)
            self.assertIn('param1=value1', call_args)
            self.assertIn('param2=value2', call_args)
    
    def test_api_request_logging(self):
        """Test API request logging helper"""
        setup_logging(
            log_level='INFO',
            log_to_file=False,
            log_to_console=False,
            log_dir=self.test_log_dir
        )
        
        logger = get_logger('api_test')
        
        # Mock the logger to capture calls
        with patch.object(logger, 'info') as mock_info:
            log_api_request(
                logger,
                'GET',
                'https://api.example.com/test',
                200,
                45.67,
                request_id='req-123'
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            self.assertIn('API', call_args)
            self.assertIn('GET', call_args)
            self.assertIn('https://api.example.com/test', call_args)
            self.assertIn('200', call_args)
            self.assertIn('45.67ms', call_args)
            self.assertIn('request_id=req-123', call_args)
    
    def test_database_operation_logging(self):
        """Test database operation logging helper"""
        setup_logging(
            log_level='INFO',
            log_to_file=False,
            log_to_console=False,
            log_dir=self.test_log_dir
        )
        
        logger = get_logger('db_test')
        
        # Mock the logger to capture calls
        with patch.object(logger, 'info') as mock_info:
            log_database_operation(
                logger,
                'SELECT',
                'SELECT * FROM users WHERE id = ?',
                15.23,
                5,
                table='users'
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            self.assertIn('DB', call_args)
            self.assertIn('SELECT', call_args)
            self.assertIn('15.23ms', call_args)
            self.assertIn('5 rows', call_args)
            self.assertIn('SELECT * FROM users WHERE id = ?', call_args)
            self.assertIn('table=users', call_args)
    
    def test_sensitive_data_filter(self):
        """Test that sensitive data filter is working"""
        from cli.logging_config import SensitiveDataFilter
        
        filter_instance = SensitiveDataFilter()
        
        # Create mock log record
        class MockRecord:
            def __init__(self, msg):
                self.msg = msg
        
        # Test with sensitive data
        record = MockRecord("User password is secret123")
        result = filter_instance.filter(record)
        self.assertTrue(result)  # Filter should not block the record
        self.assertTrue(hasattr(record, 'contains_sensitive'))
        
        # Test with non-sensitive data
        record = MockRecord("User logged in successfully")
        result = filter_instance.filter(record)
        self.assertTrue(result)
        self.assertFalse(hasattr(record, 'contains_sensitive'))
    
    def test_environment_configuration(self):
        """Test environment variable configuration"""
        # Test with environment variables
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'LOG_TO_FILE': 'false',
            'LOG_TO_CONSOLE': 'true'
        }):
            # This should use environment values
            logger = setup_logging(log_dir=self.test_log_dir)
            
            # Verify that environment settings are respected
            # (This is mostly to ensure no exceptions are raised)
            self.assertIsNotNone(logger)


if __name__ == '__main__':
    unittest.main()