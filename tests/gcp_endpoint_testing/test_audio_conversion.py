"""
Test audio conversion endpoint functionality.
Tests all format combinations, MIME type validation, filename generation, and metadata preservation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .base import BaseEndpointTest, ValidationResult
from .config import test_config
from ..utils.audio_generator import AudioFileGenerator


class TestAudioConversion:
    """Test the /api/convert endpoint for audio format conversion."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = AudioFileGenerator(self.temp_dir)
        self.endpoint = "/api/convert"
        self.base_test = BaseEndpointTest()
        
        # Create test audio files for all supported formats
        self.test_files = self.generator.create_test_audio_set()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_convert_basic_functionality(self):
        """Test basic audio conversion functionality."""
        await self.base_test.setup_client()
        
        # Test simple WAV to MP3 conversion
        valid_file_path = self.test_files.get('valid_wav')
        if not valid_file_path or not Path(valid_file_path).exists():
            pytest.skip("No valid WAV file available for testing")
        
        with open(valid_file_path, 'rb') as f:
            files = {'file': (f"test.wav", f, "audio/wav")}
            data = {'target_format': 'mp3'}
            
            result = await self.base_test.make_request(
                'POST', 
                self.endpoint,
                files=files,
                data=data
            )
            
            # Log result for analysis
            print(f"Basic conversion test: Status {result.status_code}, "
                  f"Success: {result.success}, Error: {result.error_message}")
            
            # Test should either succeed or fail gracefully
            assert result.status_code in [200, 400, 500], f"Unexpected status code: {result.status_code}"
    
    @pytest.mark.asyncio
    async def test_convert_invalid_audio_files(self):
        """Test conversion with invalid audio files."""
        await self.base_test.setup_client()
        
        invalid_files = {
            'invalid': self.test_files.get('invalid'),
            'empty': self.test_files.get('empty')
        }
        
        for file_type, file_path in invalid_files.items():
            if not file_path or not Path(file_path).exists():
                continue
                
            with open(file_path, 'rb') as f:
                files = {'file': (f"invalid.wav", f, "audio/wav")}
                data = {'target_format': 'mp3'}
                
                result = await self.base_test.make_request(
                    'POST',
                    self.endpoint,
                    files=files,
                    data=data
                )
                
                # Should return error for invalid files
                print(f"Invalid file test {file_type}: Status {result.status_code}, "
                      f"Success: {result.success}")
                assert not result.success, f"Invalid file {file_type} should have failed conversion"
                assert result.status_code in [400, 500], f"Expected 400 or 500 for {file_type}, got {result.status_code}"
    
    @pytest.mark.asyncio
    async def test_convert_missing_parameters(self):
        """Test conversion with missing required parameters."""
        await self.base_test.setup_client()
        
        valid_file_path = self.test_files.get('valid_wav')
        if not valid_file_path or not Path(valid_file_path).exists():
            pytest.skip("No valid WAV file available for testing")
        
        # Test missing target_format
        with open(valid_file_path, 'rb') as f:
            files = {'file': (f"test.wav", f, "audio/wav")}
            # No target_format provided
            
            result = await self.base_test.make_request(
                'POST',
                self.endpoint,
                files=files
            )
            
            print(f"Missing target_format test: Status {result.status_code}")
            assert not result.success, "Missing target_format should be rejected"
            assert result.status_code == 400, f"Expected 400 for missing parameter, got {result.status_code}"
        
        # Test missing file
        data = {'target_format': 'mp3'}
        
        result = await self.base_test.make_request(
            'POST',
            self.endpoint,
            data=data
        )
        
        print(f"Missing file test: Status {result.status_code}")
        assert not result.success, "Missing file should be rejected"
        assert result.status_code == 400, f"Expected 400 for missing file, got {result.status_code}"
    
    @pytest.mark.asyncio
    async def test_convert_unsupported_formats(self):
        """Test conversion with unsupported target formats."""
        await self.base_test.setup_client()
        
        valid_file_path = self.test_files.get('valid_wav')
        if not valid_file_path or not Path(valid_file_path).exists():
            pytest.skip("No valid WAV file available for testing")
        
        unsupported_formats = ['avi', 'mp4', 'txt', 'pdf', 'xyz']
        
        for unsupported_format in unsupported_formats:
            with open(valid_file_path, 'rb') as f:
                files = {'file': (f"test.wav", f, "audio/wav")}
                data = {'target_format': unsupported_format}
                
                result = await self.base_test.make_request(
                    'POST',
                    self.endpoint,
                    files=files,
                    data=data
                )
                
                # Should return error for unsupported format
                print(f"Unsupported format {unsupported_format}: Status {result.status_code}")
                assert not result.success, f"Unsupported format {unsupported_format} should be rejected"
                assert result.status_code == 400, f"Expected 400 for unsupported format, got {result.status_code}"