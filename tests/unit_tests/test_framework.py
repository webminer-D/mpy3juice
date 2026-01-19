"""
Unit tests for testing framework components.
Validates configuration, utilities, and base classes.
"""

import pytest
import tempfile
from pathlib import Path

from tests.config import TestConfig, PerformanceThresholds
from tests.utils.audio_generator import AudioFileGenerator
from tests.utils.youtube_helper import YouTubeTestHelper


class TestFrameworkConfiguration:
    """Test framework configuration and setup."""
    
    def test_config_initialization(self):
        """Test that configuration initializes with valid defaults."""
        config = TestConfig()
        
        # Validate required fields
        assert config.base_url is not None
        assert config.base_url.startswith(("http://", "https://"))
        assert config.timeout_seconds > 0
        assert config.max_concurrent_requests > 0
        
        # Validate derived properties
        assert config.health_endpoint.endswith("/api/health")
        assert config.api_base.endswith("/api")
    
    def test_config_validation(self):
        """Test configuration validation logic."""
        # Test invalid base URL
        with pytest.raises(ValueError):
            TestConfig(base_url="")
        
        with pytest.raises(ValueError):
            TestConfig(base_url="invalid-url")
    
    def test_performance_thresholds(self):
        """Test performance threshold configuration."""
        thresholds = PerformanceThresholds()
        
        assert thresholds.health_check_max_ms > 0
        assert thresholds.file_upload_max_seconds > 0
        assert thresholds.processing_max_seconds > 0


class TestAudioGenerator:
    """Test audio file generation utilities."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def generator(self, temp_dir):
        """Create audio generator for testing."""
        return AudioFileGenerator(temp_dir)
    
    def test_generator_initialization(self, generator):
        """Test audio generator initializes correctly."""
        assert generator.temp_dir.exists()
        assert len(generator.SUPPORTED_FORMATS) > 0
        assert 'wav' in generator.SUPPORTED_FORMATS
    
    def test_valid_audio_generation(self, generator):
        """Test generation of valid audio files."""
        audio_data = generator.generate_valid_audio(format='wav', duration=1)
        
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
        
        # Basic WAV file validation (should start with RIFF header)
        assert audio_data.startswith(b'RIFF')
    
    def test_invalid_audio_generation(self, generator):
        """Test generation of invalid audio files."""
        invalid_data = generator.generate_invalid_audio()
        
        assert isinstance(invalid_data, bytes)
        assert len(invalid_data) > 0
        assert not invalid_data.startswith(b'RIFF')  # Should not be valid WAV
    
    def test_edge_case_generation(self, generator):
        """Test generation of edge case audio files."""
        edge_cases = generator.generate_edge_case_audio()
        
        assert isinstance(edge_cases, list)
        assert len(edge_cases) > 0
        
        for case_name, case_data in edge_cases:
            assert isinstance(case_name, str)
            assert isinstance(case_data, bytes)
            assert len(case_data) > 0


class TestYouTubeHelper:
    """Test YouTube helper utilities."""
    
    @pytest.fixture
    def helper(self):
        """Create YouTube helper for testing."""
        return YouTubeTestHelper()
    
    def test_helper_initialization(self, helper):
        """Test YouTube helper initializes correctly."""
        valid_urls = helper.get_valid_test_urls()
        invalid_urls = helper.get_invalid_test_urls()
        
        assert isinstance(valid_urls, list)
        assert isinstance(invalid_urls, list)
        assert len(valid_urls) > 0
        assert len(invalid_urls) > 0
    
    def test_url_validation(self, helper):
        """Test URL validation logic."""
        # Test valid YouTube URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
        ]
        
        for url in valid_urls:
            assert helper.is_valid_youtube_url(url), f"Should recognize {url} as valid"
        
        # Test invalid URLs
        invalid_urls = [
            "https://www.google.com",
            "not_a_url",
            "https://www.youtube.com/watch",
        ]
        
        for url in invalid_urls:
            assert not helper.is_valid_youtube_url(url), f"Should recognize {url} as invalid"
    
    def test_video_id_extraction(self, helper):
        """Test video ID extraction from URLs."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            extracted_id = helper.extract_video_id(url)
            assert extracted_id == expected_id, f"Expected {expected_id}, got {extracted_id}"
    
    def test_bulk_test_data_generation(self, helper):
        """Test bulk test data generation."""
        test_data = helper.create_bulk_test_data()
        
        assert isinstance(test_data, dict)
        assert 'valid_urls' in test_data
        assert 'invalid_urls' in test_data
        assert 'mixed_urls' in test_data
        
        assert len(test_data['valid_urls']) > 0
        assert len(test_data['invalid_urls']) > 0
        assert len(test_data['mixed_urls']) > 0