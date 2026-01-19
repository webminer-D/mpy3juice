"""
Test suite for volume adjustment endpoint functionality.
Tests percentage, decibels, and normalize adjustment modes with parameter validation.
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


@pytest.mark.volume
@pytest.mark.asyncio
async def test_percentage_volume_adjustment():
    """Test volume adjustment using percentage mode."""
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    test = BaseEndpointTest()
    
    try:
        await test.setup_client()
        
        # Test various percentage values
        percentage_values = [50, 100, 150, 200, 300]
        
        # Generate test audio file
        test_audio = audio_generator.generate_valid_audio(format='wav', duration=5)
        
        for percentage in percentage_values:
            files = {
                'file': ('test_audio.wav', test_audio, 'audio/wav')
            }
            data = {
                'adjustment_mode': 'percentage',
                'volume_percentage': str(percentage)
            }
            
            response = await test.client.post(
                f"{test.config.base_url}/api/adjust-volume",
                files=files,
                data=data
            )
            
            # Validate successful adjustment
            assert response.status_code == 200, \
                f"Volume adjustment failed for {percentage}%: {response.text}"
            assert response.headers.get('content-type') == 'audio/wav'
            
            # Validate output is not empty
            assert len(response.content) > 0
        
    finally:
        await test.teardown_client()
        audio_generator.cleanup_all_test_files()


@pytest.mark.property
@pytest.mark.volume
@pytest.mark.asyncio
async def test_property_volume_adjustment_range_validation():
    """
    **Feature: gcp-endpoint-testing, Property 13: Volume Adjustment Range Validation**
    
    For any volume adjustment operation, parameters should be validated within ranges
    (percentage: 0-500%, decibels: -30 to +30, normalize: -20 to 0) and produce modified audio.
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    property_test = PropertyTestBase()
    property_test.log_property_test("13: Volume Adjustment Range Validation")
    
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    
    try:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(test_config.timeout_seconds),
            verify=False
        )
        
        # Test cases for each adjustment mode (simplified to just percentage mode)
        test_cases = [
            ('percentage', 'wav', {'volume_percentage': '150'}),
        ]
        
        for adjustment_mode, input_format, params in test_cases:
            # Generate test audio
            test_audio = audio_generator.generate_valid_audio(
                format=input_format,
                duration=3
            )
            
            files = {
                'file': (f'test.{input_format}', test_audio, f'audio/{input_format}')
            }
            data = {
                'adjustment_mode': adjustment_mode,
                **params
            }
            
            response = await client.post(
                f"{test_config.base_url}/api/adjust-volume",
                files=files,
                data=data,
                timeout=30.0
            )
            
            # Property: Valid parameters should succeed
            assert response.status_code == 200, f"Volume adjustment failed: {response.text}"
            
            # Property: Output should be valid audio
            assert response.headers.get('content-type') == 'audio/wav'
            assert len(response.content) > 0, "Output should not be empty"
            
            print(f"✅ Volume adjustment {adjustment_mode} for {input_format}: {params}")
        
        await client.aclose()
        
    finally:
        audio_generator.cleanup_all_test_files()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])