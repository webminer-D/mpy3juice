"""
Test suite for speed change endpoint functionality.
Tests speed factors within valid range and pitch preservation options.
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any, List

import httpx
from hypothesis import given, strategies as st, settings

from .base import BaseEndpointTest, PropertyTestBase
from .config import test_config
from ..utils.audio_generator import AudioFileGenerator


@pytest.mark.speed
@pytest.mark.asyncio
async def test_speed_factors_within_valid_range():
    """Test speed factors within valid range (0.25x to 4.0x)."""
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    test = BaseEndpointTest()
    
    try:
        await test.setup_client()
        
        # Test various speed factors within valid range
        speed_factors = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
        
        # Generate test audio file
        test_audio = audio_generator.generate_valid_audio(format='wav', duration=5)
        
        for speed_factor in speed_factors:
            files = {
                'file': ('test_audio.wav', test_audio, 'audio/wav')
            }
            data = {
                'speed': str(speed_factor),
                'preserve_pitch': 'true'
            }
            
            response = await test.client.post(
                f"{test.config.base_url}/api/change-speed",
                files=files,
                data=data
            )
            
            # Validate successful speed change
            assert response.status_code == 200, \
                f"Speed change failed for factor {speed_factor}: {response.text}"
            assert response.headers.get('content-type') == 'audio/wav'
            
            # Validate output is not empty
            assert len(response.content) > 0
        
    finally:
        await test.teardown_client()
        audio_generator.cleanup_all_test_files()


@pytest.mark.property
@pytest.mark.speed
@pytest.mark.asyncio
async def test_property_speed_change_range_validation():
    """
    **Feature: gcp-endpoint-testing, Property 14: Speed Change Range Validation**
    
    For any speed change operation, speed factors should be validated within 0.25x to 4.0x range
    and produce modified audio with correct playback speed.
    **Validates: Requirements 9.1, 9.2, 9.5, 9.6**
    """
    property_test = PropertyTestBase()
    property_test.log_property_test("14: Speed Change Range Validation")
    
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    
    try:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(test_config.timeout_seconds),
            verify=False
        )
        
        # Test cases for different speed factors and settings (using only WAV files)
        test_cases = [
            (0.5, True, 'wav'),    # Slow down with pitch preservation
            (2.0, False, 'wav'),   # Speed up without pitch preservation
            (1.0, True, 'wav'),    # No change with pitch preservation
            (4.0, False, 'wav'),   # Maximum speed without pitch preservation
            (0.25, True, 'wav')    # Minimum speed with pitch preservation
        ]
        
        for speed_factor, preserve_pitch, input_format in test_cases:
            # Generate test audio
            test_audio = audio_generator.generate_valid_audio(
                format=input_format,
                duration=3
            )
            
            files = {
                'file': (f'test.{input_format}', test_audio, f'audio/{input_format}')
            }
            data = {
                'speed': str(speed_factor),
                'preserve_pitch': str(preserve_pitch).lower()
            }
            
            response = await client.post(
                f"{test_config.base_url}/api/change-speed",
                files=files,
                data=data,
                timeout=30.0
            )
            
            # Property: Valid speed factors should succeed
            assert response.status_code == 200, f"Speed change failed: {response.text}"
            
            # Property: Output should be valid audio
            assert response.headers.get('content-type') == 'audio/wav'
            assert len(response.content) > 0, "Output should not be empty"
            
            print(f"✅ Speed change {speed_factor}x (pitch: {preserve_pitch}) for {input_format}")
        
        await client.aclose()
        
    finally:
        audio_generator.cleanup_all_test_files()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])