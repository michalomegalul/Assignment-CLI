import pytest
import requests
from unittest.mock import patch, MagicMock
from cli.file_client import stat_rest, read_rest


class TestRestClient:
    """Test REST client logic and error handling"""
    
    @patch('cli.file_client.requests.get')
    @patch('cli.file_client.write_output')
    def test_stat_rest_url_construction(self, mock_write, mock_get):
        """Test that URLs are constructed correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test',
            'size': 100,
            'mimetype': 'text/plain',
            'create_datetime': '2025-08-27T14:52:50Z'
        }
        mock_get.return_value = mock_response

        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'

        test_cases = [
            ('http://localhost/', f'http://localhost/file/{valid_uuid}/stat/'),
            ('http://localhost', f'http://localhost/file/{valid_uuid}/stat/'),
            ('https://api.example.com/', f'https://api.example.com/file/{valid_uuid}/stat/'),
            ('https://api.example.com/v1/', f'https://api.example.com/v1/file/{valid_uuid}/stat/'),
        ]
        
        for base_url, expected_url in test_cases:
            mock_get.reset_mock()
            
            stat_rest(valid_uuid, base_url, '-')
            mock_get.assert_called_with(expected_url, timeout=10)
    
    @patch('cli.file_client.requests.get')
    @patch('cli.file_client.write_output')
    def test_stat_rest_response_parsing(self, mock_write, mock_get):
        """Test parsing of different response formats"""
        test_responses = [
            {
                'name': 'document.pdf',
                'size': 1024,
                'mimetype': 'application/pdf',
                'create_datetime': '2025-01-01T00:00:00Z'
            },
            {
                'name': 'image.jpg',
                'size': 2048576,
                'mimetype': 'image/jpeg',
                'create_datetime': '2025-12-31T23:59:59Z'
            }
        ]
        
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        
        for response_data in test_responses:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_get.return_value = mock_response
            
            stat_rest(valid_uuid, 'http://localhost/', '-')
    
    @patch('cli.file_client.requests.get')
    def test_rest_error_handling(self, mock_get):
        """Test error handling for different HTTP status codes"""
        error_cases = [
            (404, 'File not found'),
            (500, 'Internal server error'),
            (403, 'Forbidden'),
            (401, 'Unauthorized')
        ]
        
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        
        for status_code, expected_behavior in error_cases:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.reason = expected_behavior
            mock_get.return_value = mock_response
            
            with pytest.raises(SystemExit):
                stat_rest(valid_uuid, 'http://localhost/', '-')
    
    @patch('cli.file_client.requests.get')
    def test_rest_timeout_handling(self, mock_get):
        """Test timeout handling"""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        
        with pytest.raises(SystemExit):
            stat_rest(valid_uuid, 'http://localhost/', '-')
    
    @patch('cli.file_client.requests.get')
    def test_rest_connection_error(self, mock_get):
        """Test connection error handling"""
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        
        with pytest.raises(SystemExit):
            stat_rest(valid_uuid, 'http://localhost/', '-')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])