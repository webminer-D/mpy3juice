"""
Test the AudioFileGenerator utility for creating test audio files.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from ..utils.audio_generator import AudioFileGenerator


class TestAudioFileGenerator:
    """Test the AudioFileGenerator class functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = AudioFileGenerator(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_valid_audio_formats(self):
        """Test generating valid audio in all supported formats."""
        for format in AudioFileGenerator.SUPPORTED_FORMATS:
            audio_data = self.generator.generate_valid_audio(format=format, duration=1)
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0
            
            # Save and validate
            file_path = self.generator.save_audio_file(audio_data, f"test.{format}")
            validation = self.generator.validate_generated_file(file_path, format)
            assert validation['exists']
            assert validation['size_bytes'] > 0
    
    def test_generate_invalid_audio(self):
        """Test generating invalid audio data."""
        invalid_data = self.generator.generate_invalid_audio()
        assert isinstance(invalid_data, bytes)
        assert len(invalid_data) > 0
        assert invalid_data.startswith(b'INVALID_AUDIO_DATA')
    
    def test_generate_empty_audio(self):
        """Test generating empty audio file."""
        empty_data = self.generator.generate_empty_audio()
        assert isinstance(empty_data, bytes)
        assert len(empty_data) == 0
    
    def test_generate_corrupted_audio(self):
        """Test generating corrupted audio files."""
        for format in ['wav', 'mp3', 'flac']:
            corrupted_data = self.generator.generate_corrupted_audio(format=format)
            assert isinstance(corrupted_data, bytes)
            assert len(corrupted_data) > 0
    
    def test_generate_edge_case_audio(self):
        """Test generating edge case audio files."""
        edge_cases = self.generator.generate_edge_case_audio()
        assert isinstance(edge_cases, list)
        assert len(edge_cases) > 0
        
        for case_name, case_data in edge_cases:
            assert isinstance(case_name, str)
            assert isinstance(case_data, bytes)
    
    def test_generate_with_metadata(self):
        """Test generating audio with custom metadata."""
        custom_metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'year': '2024'
        }
        
        audio_data = self.generator.generate_valid_audio(
            format='wav', 
            duration=2, 
            metadata=custom_metadata
        )
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
    
    def test_generate_large_audio_near_limit(self):
        """Test generating large audio file near the size limit."""
        # Use smaller size for testing to avoid creating huge files
        large_data = self.generator.generate_large_audio(size_mb=1)
        assert isinstance(large_data, bytes)
        assert len(large_data) > 500000  # Should be reasonably large
    
    def test_malformed_headers(self):
        """Test generating files with malformed headers."""
        malformed_cases = self.generator.generate_malformed_headers('wav')
        assert isinstance(malformed_cases, list)
        assert len(malformed_cases) > 0
        
        for case_name, case_data in malformed_cases:
            assert isinstance(case_name, str)
            assert isinstance(case_data, bytes)
            assert 'wav' in case_name
    
    def test_create_test_audio_set(self):
        """Test creating a comprehensive set of test audio files."""
        test_files = self.generator.create_test_audio_set()
        assert isinstance(test_files, dict)
        assert len(test_files) > 0
        
        # Check that files were actually created
        for file_type, file_path in test_files.items():
            assert Path(file_path).exists(), f"File {file_type} was not created: {file_path}"
    
    def test_create_format_test_set(self):
        """Test creating format-specific test sets."""
        for format in ['wav', 'mp3', 'flac']:
            test_files = self.generator.create_format_test_set(format)
            assert isinstance(test_files, dict)
            assert len(test_files) > 0
            
            # All files should be for the specified format
            for file_type, file_path in test_files.items():
                assert format in file_type
                assert Path(file_path).exists()
    
    def test_file_validation(self):
        """Test file validation functionality."""
        # Create a valid WAV file
        audio_data = self.generator.generate_valid_audio('wav', duration=1)
        file_path = self.generator.save_audio_file(audio_data, 'test.wav')
        
        validation = self.generator.validate_generated_file(file_path, 'wav')
        assert validation['exists']
        assert validation['is_valid']
        assert validation['format_detected'] == 'wav'
        assert validation['size_bytes'] > 0
        assert validation['size_mb'] > 0
    
    def test_cleanup_functionality(self):
        """Test file cleanup functionality."""
        # Create some test files
        test_files = []
        for i in range(3):
            audio_data = self.generator.generate_valid_audio('wav', duration=1)
            file_path = self.generator.save_audio_file(audio_data, f'cleanup_test_{i}.wav')
            test_files.append(file_path)
            assert Path(file_path).exists()
        
        # Clean up specific files
        self.generator.cleanup_test_files(test_files)
        
        # Check files are gone
        for file_path in test_files:
            assert not Path(file_path).exists()
    
    def test_unsupported_format_error(self):
        """Test error handling for unsupported formats."""
        with pytest.raises(ValueError, match="Unsupported format"):
            self.generator.generate_valid_audio(format='unsupported')
        
        with pytest.raises(ValueError, match="Unsupported format"):
            self.generator.create_format_test_set('unsupported')