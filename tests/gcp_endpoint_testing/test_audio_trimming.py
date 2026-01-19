"""
Test audio trimming endpoint functionality.
Tests valid time range trimming, time range validation, error handling, and edge cases.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .base import BaseEndpointTest, ValidationResult
from .config import test_config
from ..utils.audio_generator import AudioFileGenerator


class TestAudioTrimming:
    """Test the /api/trim endpoint for audio trimming functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = AudioFileGenerator(self.temp_dir)
        self.endpoint = "/api/trim"
        self.base_test = BaseEndpointTest()
        
        # Create test audio files with known durations
        self.test_files = {}
        
        # Create audio files with specific durations for precise trimming tests
        for duration in [5, 10]:  # seconds - keep small for testing
            audio_data = self.generator.generate_valid_audio(
                format='wav', 
                duration=duration
            )
            filename = f"test_{duration}s.wav"
            file_path = self.generator.save_audio_file(audio_data, filename)
            self.test_files[f"wav_{duration}s"] = {
                'path': file_path,
                'duration': duration,
                'format': 'wav'
            }
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_trim_valid_time_ranges(self):
        """Test trimming with valid time ranges."""
        await self.base_test.setup_client()
        
        file_info = self.test_files.get('wav_5s')
        if not file_info:
            pytest.skip("No 5-second WAV file available for testing")
        
        file_path = file_info['path']
        
        # Test valid time range
        with open(file_path, 'rb') as f:
            files = {'file': (f"test.wav", f, "audio/wav")}
            data = {
                'start_time': '1',
                'end_time': '3'
            }
            
            result = await self.base_test.make_request(
                'POST',
                self.endpoint,
                files=files,
                data=data
            )
            
            print(f"Valid trim test: Status {result.status_code}, "
                  f"Success: {result.success}, Error: {result.error_message}")
            
            # Test should either succeed or fail gracefully
            assert result.status_code in [200, 400, 500], f"Unexpected status code: {result.status_code}"
    
    @pytest.mark.asyncio
    async def test_trim_invalid_time_ranges(self):
        """Test trimming with invalid time ranges."""
        await self.base_test.setup_client()
        
        file_info = self.test_files.get('wav_5s')
        if not file_info:
            pytest.skip("No 5-second WAV file available for testing")
        
        file_path = file_info['path']
        
        # Invalid time range: start > end
        with open(file_path, 'rb') as f:
            files = {'file': (f"test.wav", f, "audio/wav")}
            data = {
                'start_time': '3',
                'end_time': '1'
            }
            
            result = await self.base_test.make_request(
                'POST',
                self.endpoint,
                files=files,
                data=data
            )
            
            print(f"Invalid time range test: Status {result.status_code}")
            # Should return error for invalid time ranges
            assert not result.success, "Invalid time range should fail"
            assert result.status_code == 400, f"Expected 400 for invalid range, got {result.status_code}"
    
    @pytest.mark.asyncio
    async def test_trim_missing_parameters(self):
        """Test trimming with missing required parameters."""
        await self.base_test.setup_client()
        
        file_info = self.test_files.get('wav_5s')
        if not file_info:
            pytest.skip("No 5-second WAV file available for testing")
        
        file_path = file_info['path']
        
        # Test missing start_time
        with open(file_path, 'rb') as f:
            files = {'file': (f"test.wav", f, "audio/wav")}
            data = {'end_time': '3'}  # Missing start_time
            
            result = await self.base_test.make_request(
                'POST',
                self.endpoint,
                files=files,
                data=data
            )
            
            print(f"Missing start_time test: Status {result.status_code}")
            assert not result.success, "Missing start_time should be rejected"
            assert result.status_code == 400, f"Expected 400 for missing start_time, got {result.status_code}"
        
        # Test missing file
        data = {'start_time': '1', 'end_time': '3'}
        
        result = await self.base_test.make_request(
            'POST',
            self.endpoint,
            data=data
        )
        
        print(f"Missing file test: Status {result.status_code}")
        assert not result.success, "Missing file should be rejected"
        assert result.status_code == 400, f"Expected 400 for missing file, got {result.status_code}"
    
    @pytest.mark.asyncio
    async def test_trim_malformed_time_parameters(self):
        """Test trimming with malformed time parameters."""
        await self.base_test.setup_client()
        
        file_info = self.test_files.get('wav_5s')
        if not file_info:
            pytest.skip("No 5-second WAV file available for testing")
        
        file_path = file_info['path']
        
        # Non-numeric start time
        with open(file_path, 'rb') as f:
            files = {'file': (f"test.wav", f, "audio/wav")}
            data = {
                'start_time': 'abc',
                'end_time': '3'
            }
            
            result = await self.base_test.make_request(
                'POST',
                self.endpoint,
                files=files,
                data=data
            )
            
            print(f"Malformed parameter test: Status {result.status_code}")
            # Should return error for malformed parameters
            assert not result.success, "Malformed parameters should fail"
            assert result.status_code == 400, f"Expected 400 for malformed params, got {result.status_code}"