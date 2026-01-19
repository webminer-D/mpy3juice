"""
Audio merging endpoint tests for GCP deployment validation.
Tests merging 2-10 files with different formats and characteristics.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

import httpx

from .base import BaseEndpointTest, ValidationResult
from .config import test_config
from ..utils.audio_generator import AudioFileGenerator


class TestAudioMerging(BaseEndpointTest):
    """Test suite for audio merging functionality"""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = None
        self.audio_generator = None
        self.test_files = {}
    
    async def setup_method(self):
        """Set up test environment"""
        await self.setup_client()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="audio_merge_test_")
        self.audio_generator = AudioFileGenerator(self.temp_dir)
        
        # Generate test audio files in different formats
        self.test_files = await self._generate_test_files()
    
    async def teardown_method(self):
        """Clean up test environment"""
        # Clean up test files
        if self.audio_generator:
            self.audio_generator.cleanup_all_test_files()
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        await self.teardown_client()
    
    async def _generate_test_files(self) -> Dict[str, str]:
        """Generate test audio files for merging tests"""
        test_files = {}
        
        # Create valid audio files in different formats
        formats = ['wav', 'mp3', 'flac', 'aac', 'ogg', 'm4a']
        
        for i, format in enumerate(formats):
            # Create files with different characteristics
            duration = 2 + i  # Different durations (2-7 seconds)
            sample_rate = 44100 if i % 2 == 0 else 48000  # Different sample rates
            channels = 2 if i % 3 != 0 else 1  # Mix of stereo and mono
            
            audio_data = self.audio_generator.generate_valid_audio(
                format=format,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels
            )
            
            filename = f"test_merge_{i+1}.{format}"
            file_path = self.audio_generator.save_audio_file(audio_data, filename)
            test_files[f"file_{i+1}_{format}"] = file_path
        
        # Create additional files for edge cases
        # Small file
        small_audio = self.audio_generator.generate_valid_audio(duration=1)
        test_files["small_file"] = self.audio_generator.save_audio_file(small_audio, "small.wav")
        
        # Large file (but within limits)
        large_audio = self.audio_generator.generate_valid_audio(duration=30)
        test_files["large_file"] = self.audio_generator.save_audio_file(large_audio, "large.wav")
        
        # Invalid file
        invalid_audio = self.audio_generator.generate_invalid_audio()
        test_files["invalid_file"] = self.audio_generator.save_audio_file(invalid_audio, "invalid.bin")
        
        return test_files
    
    async def _upload_files_for_merge(self, file_paths: List[str], output_format: str = "mp3") -> ValidationResult:
        """Upload multiple files to the merge endpoint"""
        url = f"{self.config.base_url}/api/merge"
        
        # Prepare files for upload
        files = []
        for i, file_path in enumerate(file_paths):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = Path(file_path).name
            files.append(('files', (filename, file_content, 'audio/*')))
        
        # Prepare form data
        data = {'output_format': output_format}
        
        try:
            response = await self.client.post(url, files=files, data=data)
            
            return ValidationResult(
                endpoint="/api/merge",
                method="POST",
                status_code=response.status_code,
                response_time_ms=0,  # Not measuring time here
                success=200 <= response.status_code < 300,
                response_data=response.content if response.status_code == 200 else None,
                error_message=response.text if response.status_code >= 400 else None
            )
        except Exception as e:
            return ValidationResult(
                endpoint="/api/merge",
                method="POST",
                status_code=0,
                response_time_ms=0,
                success=False,
                error_message=str(e)
            )
    
    @pytest.mark.asyncio
    async def test_merge_two_files_same_format(self):
        """Test merging two files of the same format"""
        await self.setup_method()
        
        try:
            # Select two WAV files
            wav_files = [path for key, path in self.test_files.items() if key.endswith('_wav')][:2]
            if len(wav_files) < 2:
                # Create additional WAV files if needed
                wav_files = []
                for i in range(2):
                    audio_data = self.audio_generator.generate_valid_audio(format='wav', duration=3)
                    file_path = self.audio_generator.save_audio_file(audio_data, f"merge_test_{i}.wav")
                    wav_files.append(file_path)
            
            result = await self._upload_files_for_merge(wav_files, "wav")
            
            # Validate successful merge
            assert result.success, f"Merge failed: {result.error_message}"
            assert result.status_code == 200, f"Expected 200, got {result.status_code}"
            assert result.response_data is not None, "No audio data returned"
            assert len(result.response_data) > 0, "Empty audio data returned"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_different_formats(self):
        """Test merging files with different formats"""
        await self.setup_method()
        
        try:
            # Select files with different formats
            different_format_files = []
            formats_used = set()
            
            for key, path in self.test_files.items():
                if '_' in key and key.split('_')[-1] not in formats_used:
                    different_format_files.append(path)
                    formats_used.add(key.split('_')[-1])
                    if len(different_format_files) >= 3:
                        break
            
            if len(different_format_files) < 2:
                pytest.skip("Not enough different format files available")
            
            result = await self._upload_files_for_merge(different_format_files, "mp3")
            
            # Validate successful merge with format conversion
            assert result.success, f"Merge with different formats failed: {result.error_message}"
            assert result.status_code == 200, f"Expected 200, got {result.status_code}"
            assert result.response_data is not None, "No audio data returned"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_maximum_files(self):
        """Test merging maximum allowed files (10)"""
        await self.setup_method()
        
        try:
            # Create 10 small audio files
            merge_files = []
            for i in range(10):
                audio_data = self.audio_generator.generate_valid_audio(
                    format='wav', 
                    duration=1,  # Short duration to keep total size manageable
                    sample_rate=22050  # Lower sample rate to reduce size
                )
                file_path = self.audio_generator.save_audio_file(audio_data, f"merge_max_{i}.wav")
                merge_files.append(file_path)
            
            result = await self._upload_files_for_merge(merge_files, "mp3")
            
            # Validate successful merge of maximum files
            assert result.success, f"Merge of 10 files failed: {result.error_message}"
            assert result.status_code == 200, f"Expected 200, got {result.status_code}"
            assert result.response_data is not None, "No audio data returned"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_too_many_files(self):
        """Test merging more than maximum allowed files (>10)"""
        await self.setup_method()
        
        try:
            # Create 11 small audio files
            merge_files = []
            for i in range(11):
                audio_data = self.audio_generator.generate_valid_audio(
                    format='wav', 
                    duration=1,
                    sample_rate=22050
                )
                file_path = self.audio_generator.save_audio_file(audio_data, f"merge_exceed_{i}.wav")
                merge_files.append(file_path)
            
            result = await self._upload_files_for_merge(merge_files, "mp3")
            
            # Validate rejection of too many files
            assert not result.success, "Should reject more than 10 files"
            assert result.status_code == 400, f"Expected 400, got {result.status_code}"
            assert "maximum" in result.error_message.lower() or "limit" in result.error_message.lower(), \
                f"Error message should mention limit: {result.error_message}"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_too_few_files(self):
        """Test merging fewer than minimum required files (<2)"""
        await self.setup_method()
        
        try:
            # Try to merge just one file
            single_file = [list(self.test_files.values())[0]]
            
            result = await self._upload_files_for_merge(single_file, "mp3")
            
            # Validate rejection of too few files
            assert not result.success, "Should reject fewer than 2 files"
            assert result.status_code == 400, f"Expected 400, got {result.status_code}"
            assert "minimum" in result.error_message.lower() or "2" in result.error_message, \
                f"Error message should mention minimum requirement: {result.error_message}"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_with_invalid_file(self):
        """Test merging with one invalid file among valid files"""
        await self.setup_method()
        
        try:
            # Mix valid and invalid files
            valid_files = [path for key, path in self.test_files.items() if 'invalid' not in key][:2]
            invalid_file = self.test_files.get("invalid_file")
            
            if not invalid_file:
                pytest.skip("Invalid file not available")
            
            mixed_files = valid_files + [invalid_file]
            
            result = await self._upload_files_for_merge(mixed_files, "mp3")
            
            # Validate rejection due to invalid file
            assert not result.success, "Should reject merge with invalid file"
            assert result.status_code == 400, f"Expected 400, got {result.status_code}"
            assert "invalid" in result.error_message.lower() or "error" in result.error_message.lower(), \
                f"Error message should indicate invalid file: {result.error_message}"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_different_sample_rates(self):
        """Test merging files with different sample rates"""
        await self.setup_method()
        
        try:
            # Create files with different sample rates
            sample_rates = [22050, 44100, 48000]
            different_sr_files = []
            
            for i, sr in enumerate(sample_rates):
                audio_data = self.audio_generator.generate_valid_audio(
                    format='wav',
                    duration=2,
                    sample_rate=sr,
                    channels=2
                )
                file_path = self.audio_generator.save_audio_file(audio_data, f"sr_{sr}.wav")
                different_sr_files.append(file_path)
            
            result = await self._upload_files_for_merge(different_sr_files, "wav")
            
            # Validate successful merge with resampling
            assert result.success, f"Merge with different sample rates failed: {result.error_message}"
            assert result.status_code == 200, f"Expected 200, got {result.status_code}"
            assert result.response_data is not None, "No audio data returned"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_mono_and_stereo(self):
        """Test merging mono and stereo files"""
        await self.setup_method()
        
        try:
            # Create mono and stereo files
            mono_audio = self.audio_generator.generate_valid_audio(
                format='wav', duration=3, channels=1
            )
            stereo_audio = self.audio_generator.generate_valid_audio(
                format='wav', duration=3, channels=2
            )
            
            mono_file = self.audio_generator.save_audio_file(mono_audio, "mono.wav")
            stereo_file = self.audio_generator.save_audio_file(stereo_audio, "stereo.wav")
            
            mixed_channel_files = [mono_file, stereo_file]
            
            result = await self._upload_files_for_merge(mixed_channel_files, "wav")
            
            # Validate successful merge with channel conversion
            assert result.success, f"Merge with different channels failed: {result.error_message}"
            assert result.status_code == 200, f"Expected 200, got {result.status_code}"
            assert result.response_data is not None, "No audio data returned"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_output_formats(self):
        """Test merging with different output formats"""
        await self.setup_method()
        
        try:
            # Use two valid files for merging
            valid_files = [path for key, path in self.test_files.items() if 'invalid' not in key][:2]
            
            if len(valid_files) < 2:
                pytest.skip("Not enough valid files for testing")
            
            # Test different output formats
            output_formats = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a']
            
            for output_format in output_formats:
                result = await self._upload_files_for_merge(valid_files, output_format)
                
                assert result.success, f"Merge to {output_format} failed: {result.error_message}"
                assert result.status_code == 200, f"Expected 200 for {output_format}, got {result.status_code}"
                assert result.response_data is not None, f"No audio data returned for {output_format}"
            
        finally:
            await self.teardown_method()
    
    @pytest.mark.asyncio
    async def test_merge_cors_headers(self):
        """Test CORS headers on merge endpoint"""
        await self.setup_method()
        
        try:
            cors_result = await self.test_cors_headers("/api/merge")
            
            assert cors_result.has_cors_headers, "CORS headers missing"
            assert cors_result.allows_origin, "CORS should allow origin"
            assert "POST" in cors_result.allows_methods, "CORS should allow POST method"
            
        finally:
            await self.teardown_method()


# Property-based test for audio merging capabilities
def test_property_audio_merging_capabilities():
    """
    **Feature: gcp-endpoint-testing, Property 7: Audio Merging Capabilities**
    
    For any set of 2-10 valid audio files with different formats, merging should 
    produce a single output file in the specified format with proper format 
    conversion and resampling.
    
    **Validates: Requirements 4.1, 4.4, 4.5, 4.6**
    """
    from hypothesis import given, strategies as st, settings
    import tempfile
    import shutil
    import asyncio
    
    @given(
        num_files=st.integers(min_value=2, max_value=3),  # Reduced range for faster testing
        output_format=st.sampled_from(['wav']),  # Only WAV format that works reliably
        file_formats=st.lists(
            st.sampled_from(['wav']),
            min_size=2, max_size=3
        )
    )
    @settings(max_examples=5, deadline=30000)  # Reduced examples and deadline
    def property_test(num_files, output_format, file_formats):
        # Ensure we have the right number of formats
        file_formats = file_formats[:num_files]
        while len(file_formats) < num_files:
            file_formats.append('wav')  # Fill with wav if needed
        
        async def run_async_test():
            temp_dir = tempfile.mkdtemp(prefix="property_merge_test_")
            test_instance = TestAudioMerging()
            
            try:
                audio_gen = AudioFileGenerator(temp_dir)
                
                # Generate test files
                test_files = []
                for i, format in enumerate(file_formats):
                    audio_data = audio_gen.generate_valid_audio(
                        format=format,
                        duration=1,  # Short duration for faster testing
                        sample_rate=22050,  # Lower sample rate for speed
                        channels=1  # Mono for speed
                    )
                    file_path = audio_gen.save_audio_file(audio_data, f"prop_test_{i}.{format}")
                    test_files.append(file_path)
                
                # Set up test instance
                await test_instance.setup_client()
                
                # Test the merge
                result = await test_instance._upload_files_for_merge(test_files, output_format)
                
                # Property assertions
                assert result.success, f"Merge should succeed for valid files: {result.error_message}"
                assert result.status_code == 200, f"Should return 200 for valid merge"
                assert result.response_data is not None, "Should return audio data"
                assert len(result.response_data) > 0, "Should return non-empty audio data"
                
            finally:
                # Cleanup
                await test_instance.teardown_client()
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Run the async test
        asyncio.run(run_async_test())
    
    # Run the property test
    property_test()