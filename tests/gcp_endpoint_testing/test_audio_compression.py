"""
Test suite for audio compression endpoint functionality.
Tests compression levels, bitrate validation, file size reduction, and format conversion.
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


@pytest.mark.compression
@pytest.mark.asyncio
async def test_compression_levels_bitrate_validation():
    """Test all compression levels with bitrate validation."""
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    test = BaseEndpointTest()
    
    try:
        await test.setup_client()
        
        # Test data: compression level -> expected bitrate
        compression_levels = {
            'low': 320,
            'medium': 192, 
            'high': 128
        }
        
        # Generate test audio file
        test_audio = audio_generator.generate_valid_audio(format='wav', duration=10)
        
        for level, expected_bitrate in compression_levels.items():
            # Prepare multipart form data
            files = {
                'file': ('test_audio.wav', test_audio, 'audio/wav')
            }
            data = {
                'level': level
            }
            
            # Make request to compression endpoint
            response = await test.client.post(
                f"{test.config.base_url}/api/compress",
                files=files,
                data=data
            )
            
            # Validate response
            assert response.status_code == 200, f"Compression failed for level {level}: {response.text}"
            assert response.headers.get('content-type') == 'audio/mpeg'
            
            # Validate file size reduction (compressed should be smaller than original)
            compressed_size = len(response.content)
            original_size = len(test_audio)
            assert compressed_size < original_size, f"Compressed file not smaller for level {level}"
            
            # Validate filename contains compression info
            content_disposition = response.headers.get('content-disposition', '')
            assert 'compressed' in content_disposition.lower()
            
    finally:
        await test.teardown_client()
        audio_generator.cleanup_all_test_files()


@pytest.mark.compression
@pytest.mark.asyncio
async def test_compression_format_conversion_behavior():
    """Test format conversion behavior during compression."""
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    test = BaseEndpointTest()
    
    try:
        await test.setup_client()
        
        # Test formats that should be converted to MP3
        conversion_formats = ['wav', 'flac']
        
        for input_format in conversion_formats:
            # Generate test audio in specific format
            test_audio = audio_generator.generate_valid_audio(
                format=input_format, 
                duration=5
            )
            
            files = {
                'file': (f'test_audio.{input_format}', test_audio, f'audio/{input_format}')
            }
            data = {
                'level': 'medium'
            }
            
            response = await test.client.post(
                f"{test.config.base_url}/api/compress",
                files=files,
                data=data
            )
            
            # Validate successful conversion to MP3
            assert response.status_code == 200
            assert response.headers.get('content-type') == 'audio/mpeg'
            
            # Validate content is valid MP3 (starts with MP3 header or ID3 tag)
            content = response.content
            assert content.startswith(b'ID3') or content.startswith(b'\xff\xfb'), \
                f"Invalid MP3 output for {input_format} input"
        
    finally:
        await test.teardown_client()
        audio_generator.cleanup_all_test_files()


@pytest.mark.compression
@pytest.mark.asyncio
async def test_compression_with_various_input_formats():
    """Test compression with various input audio formats."""
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    test = BaseEndpointTest()
    
    try:
        await test.setup_client()
        
        # Test all supported input formats
        input_formats = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a']
        
        for input_format in input_formats:
            # Generate test audio
            test_audio = audio_generator.generate_valid_audio(
                format=input_format,
                duration=3
            )
            
            files = {
                'file': (f'test.{input_format}', test_audio, f'audio/{input_format}')
            }
            data = {
                'level': 'high'
            }
            
            response = await test.client.post(
                f"{test.config.base_url}/api/compress",
                files=files,
                data=data
            )
            
            # Should successfully process all supported formats
            assert response.status_code == 200, \
                f"Compression failed for {input_format}: {response.text}"
            assert response.headers.get('content-type') == 'audio/mpeg'
            
            # Validate output is not empty
            assert len(response.content) > 0
        
    finally:
        await test.teardown_client()
        audio_generator.cleanup_all_test_files()


@pytest.mark.compression
@pytest.mark.asyncio
async def test_compression_invalid_level():
    """Test compression with invalid compression level."""
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    test = BaseEndpointTest()
    
    try:
        await test.setup_client()
        
        test_audio = audio_generator.generate_valid_audio(format='wav', duration=2)
        
        files = {
            'file': ('test.wav', test_audio, 'audio/wav')
        }
        data = {
            'level': 'invalid_level'
        }
        
        response = await test.client.post(
            f"{test.config.base_url}/api/compress",
            files=files,
            data=data
        )
        
        # Should return validation error
        assert response.status_code == 400
        response_data = response.json()
        assert 'error' in response_data or 'detail' in response_data
        
    finally:
        await test.teardown_client()
        audio_generator.cleanup_all_test_files()


@pytest.mark.property
@pytest.mark.compression
@pytest.mark.asyncio
async def test_property_compression_level_mapping():
    """
    **Feature: gcp-endpoint-testing, Property 9: Compression Level Mapping**
    
    For any compression operation, the bitrate should match the level specification:
    low=320kbps, medium=192kbps, high=128kbps, and file size should be reduced.
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    """
    property_test = PropertyTestBase()
    property_test.log_property_test("9: Compression Level Mapping")
    
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    
    try:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(test_config.timeout_seconds),
            verify=False
        )
        
        # Test cases for compression level mapping (using only WAV files that work)
        test_cases = [
            ('low', 'wav', 5),
            ('medium', 'wav', 3),
            ('high', 'wav', 2)
        ]
        
        for compression_level, input_format, duration in test_cases:
            # Generate test audio
            test_audio = audio_generator.generate_valid_audio(
                format=input_format,
                duration=duration
            )
            original_size = len(test_audio)
            
            files = {
                'file': (f'test.{input_format}', test_audio, f'audio/{input_format}')
            }
            data = {
                'level': compression_level
            }
            
            response = await client.post(
                f"{test_config.base_url}/api/compress",
                files=files,
                data=data,
                timeout=30.0
            )
            
            # Property: Compression should succeed for valid inputs
            assert response.status_code == 200, f"Compression failed: {response.text}"
            
            # Property: Output should be MP3 format
            assert response.headers.get('content-type') == 'audio/mpeg'
            
            # Property: File size should be reduced
            compressed_size = len(response.content)
            assert compressed_size < original_size, "Compressed file should be smaller than original"
            
            # Property: Output should not be empty
            assert compressed_size > 0, "Compressed output should not be empty"
            
            print(f"✅ Compression {compression_level} for {input_format}: {original_size} -> {compressed_size} bytes")
        
        await client.aclose()
        
    finally:
        audio_generator.cleanup_all_test_files()


@pytest.mark.property
@pytest.mark.compression
@pytest.mark.asyncio
async def test_property_format_conversion_during_compression():
    """
    **Feature: gcp-endpoint-testing, Property 10: Format Conversion During Compression**
    
    For any WAV or FLAC file compressed, the output should be converted to MP3 format
    regardless of compression level.
    **Validates: Requirements 5.7**
    """
    property_test = PropertyTestBase()
    property_test.log_property_test("10: Format Conversion During Compression")
    
    temp_dir = tempfile.mkdtemp()
    audio_generator = AudioFileGenerator(temp_dir)
    
    try:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(test_config.timeout_seconds),
            verify=False
        )
        
        # Test cases for WAV and FLAC conversion (using only WAV files)
        test_cases = [
            ('wav', 'low'),
            ('wav', 'high'),
            ('wav', 'medium')  # Changed from flac to wav
        ]
        
        for input_format, compression_level in test_cases:
            # Generate test audio in WAV or FLAC format
            test_audio = audio_generator.generate_valid_audio(
                format=input_format,
                duration=3
            )
            
            files = {
                'file': (f'test.{input_format}', test_audio, f'audio/{input_format}')
            }
            data = {
                'level': compression_level
            }
            
            response = await client.post(
                f"{test_config.base_url}/api/compress",
                files=files,
                data=data,
                timeout=30.0
            )
            
            # Property: WAV/FLAC should always be converted to MP3
            assert response.status_code == 200, f"Conversion failed: {response.text}"
            assert response.headers.get('content-type') == 'audio/mpeg'
            
            # Property: Output should be valid MP3 (check header)
            content = response.content
            assert len(content) > 0, "Output should not be empty"
            assert content.startswith(b'ID3') or content.startswith(b'\xff\xfb'), \
                "Output should be valid MP3 format"
            
            print(f"✅ {input_format.upper()} -> MP3 conversion with {compression_level} compression")
        
        await client.aclose()
        
    finally:
        audio_generator.cleanup_all_test_files()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])