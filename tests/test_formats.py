import pytest
from unittest.mock import patch, MagicMock
from cli.file_client import stat_rest


class TestDataFormats:
    """Test handling of different data formats"""
    
    @patch('cli.file_client.requests.get')
    @patch('cli.file_client.write_output')
    def test_stat_output_format(self, mock_write, mock_get):
        """Test that stat output follows expected format"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'document.pdf',
            'size': 1048576,
            'mimetype': 'application/pdf',
            'create_datetime': '2025-01-15T14:30:00Z'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        stat_rest(valid_uuid, 'http://localhost/', '-')
        
        mock_write.assert_called_once()
        output_content = mock_write.call_args[0][0]
        
        expected_lines = [
            'Name: document.pdf',
            'Size: 1048576 bytes',
            'MIME Type: application/pdf',
            'Created: 2025-01-15T14:30:00Z'
        ]
        
        for line in expected_lines:
            assert line in output_content
    
    @patch('cli.file_client.requests.get')
    @patch('cli.file_client.write_output')
    def test_stat_missing_fields_handling(self, mock_write, mock_get):
        """Test handling of missing fields in API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'partial.txt'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        stat_rest(valid_uuid, 'http://localhost/', '-')
        
        output_content = mock_write.call_args[0][0]
        
        assert 'Name: partial.txt' in output_content
        assert 'Size:' in output_content 
        assert 'MIME Type:' in output_content 
        assert 'Created:' in output_content 


if __name__ == '__main__':
    pytest.main([__file__, '-v'])