import pytest
import time
from unittest.mock import patch, MagicMock
from cli.file_client import validate_uuid, stat_rest


class TestPerformance:
    """Test performance characteristics"""
    
    def test_uuid_validation_performance(self):
        """Test UUID validation is fast enough for large batches"""
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        invalid_uuid = 'not-a-uuid'
        
        start_time = time.time()
        
        # Validate 1000 UUIDs
        for _ in range(1000):
            validate_uuid(valid_uuid)
            validate_uuid(invalid_uuid)
        
        elapsed = time.time() - start_time
        
        # Should process 2000 validations in under 1 second
        assert elapsed < 1.0, f"UUID validation took {elapsed:.3f}s for 2000 operations"
    
    @patch('cli.file_client.requests.get')
    @patch('cli.file_client.write_output')
    def test_rest_client_timeout_configuration(self, mock_write, mock_get):
        """Test that REST client has appropriate timeout"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'name': 'test'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Use valid UUID instead of 'test-uuid'
        valid_uuid = '123e4567-e89b-12d3-a456-426614174000'
        
        stat_rest(valid_uuid, 'http://localhost/')
        
        # Verify timeout is set to 30 seconds
        mock_get.assert_called_with(f'http://localhost/file/{valid_uuid}/stat/', timeout=30)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])