import pytest
import uuid
from cli.file_client import validate_uuid


class TestValidators:
    """Test data validation functions"""
    
    def test_validate_uuid_valid_formats(self):
        """Test valid UUID formats are accepted"""
        valid_uuids = [
            '123e4567-e89b-12d3-a456-426614174000',
            'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
            str(uuid.uuid4()),
            '00000000-0000-0000-0000-000000000000'
        ]
        
        for valid_uuid in valid_uuids:
            assert validate_uuid(valid_uuid) == True, f"Should accept {valid_uuid}"
    
    def test_validate_uuid_invalid_formats(self):
        """Test invalid UUID formats are rejected"""
        invalid_uuids = [
            'not-a-uuid',
            '123e4567-e89b-12d3-a456',  # Too short
            '123e4567-e89b-12d3-a456-426614174000-extra',  # Too long
            '',
            None,
            '123e4567_e89b_12d3_a456_426614174000',  # Wrong separators
            'gggggggg-gggg-gggg-gggg-gggggggggggg'  # Invalid characters
        ]
        
        for invalid_uuid in invalid_uuids:
            assert validate_uuid(invalid_uuid) == False, f"Should reject {invalid_uuid}"
    
    def test_validate_uuid_case_insensitive(self):
        """Test UUID validation is case insensitive"""
        uuid_lower = '123e4567-e89b-12d3-a456-426614174000'
        uuid_upper = '123E4567-E89B-12D3-A456-426614174000'
        uuid_mixed = '123e4567-E89B-12d3-A456-426614174000'
        
        assert validate_uuid(uuid_lower) == True
        assert validate_uuid(uuid_upper) == True
        assert validate_uuid(uuid_mixed) == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])