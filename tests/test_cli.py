import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.file_client import file_client

class TestFileClient:
    """Test file client functionality"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test help command shows usage"""
        result = self.runner.invoke(file_client, ['--help'])
        
        assert result.exit_code == 0
        assert 'File client for REST/gRPC operations' in result.output
        assert 'stat' in result.output
        assert 'read' in result.output
    
    @patch('cli.file_client.requests.get')
    def test_stat_rest_success(self, mock_get):
        """Test successful stat command with REST backend"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test.txt',
            'size': 1234,
            'mimetype': 'text/plain',
            'create_datetime': '2025-08-24T15:23:03Z'
        }
        mock_get.return_value = mock_response
        
        result = self.runner.invoke(file_client, [
            '--backend', 'rest',
            '--base-url', 'http://test-api/',
            'stat', 
            '123e4567-e89b-12d3-a456-426614174000'
        ])
        
        assert result.exit_code == 0
        assert 'File Metadata:' in result.output
        assert 'test.txt' in result.output
        assert '1234 bytes' in result.output
        assert 'text/plain' in result.output
    
    @patch('cli.file_client.requests.get')
    def test_stat_rest_not_found(self, mock_get):
        """Test stat command when file not found"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.runner.invoke(file_client, [
            '--backend', 'rest',
            'stat', 
            '123e4567-e89b-12d3-a456-426614174000'
        ])
        
        assert result.exit_code == 1
        assert 'File not found' in result.output
    
    @patch('cli.file_client.requests.get')
    def test_read_rest_success(self, mock_get):
        """Test successful read command with REST backend"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Hello, world!'
        mock_get.return_value = mock_response
        
        result = self.runner.invoke(file_client, [
            '--backend', 'rest',
            'read', 
            '123e4567-e89b-12d3-a456-426614174000'
        ])
        
        assert result.exit_code == 0
        assert 'Hello, world!' in result.output
    
    def test_grpc_not_implemented(self):
        """Test that gRPC shows not implemented message"""
        result = self.runner.invoke(file_client, [
            '--backend', 'grpc',
            'stat', 
            '123e4567-e89b-12d3-a456-426614174000'
        ])
        
        assert result.exit_code == 1
        assert 'gRPC backend not implemented yet' in result.output

if __name__ == '__main__':
    pytest.main([__file__, '-v'])