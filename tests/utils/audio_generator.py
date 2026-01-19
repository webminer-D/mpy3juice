"""
Audio file generator for creating test data.
Generates valid, invalid, and edge case audio files for comprehensive testing.
"""

import io
import os
import wave
import struct
import random
import json
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime


class AudioFileGenerator:
    """Creates test audio files in various formats, sizes, and characteristics."""
    
    SUPPORTED_FORMATS = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a']
    
    # File size limits for testing (in MB)
    MAX_FILE_SIZE_MB = 100
    LARGE_FILE_SIZE_MB = 95  # Just under limit
    OVERSIZED_FILE_SIZE_MB = 105  # Over limit
    
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Default metadata for test files
        self.default_metadata = {
            'title': 'Test Audio File',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'year': '2024',
            'genre': 'Test',
            'comment': 'Generated for testing purposes'
        }
    
    def generate_valid_audio(self, format: str = 'wav', duration: int = 5, 
                           sample_rate: int = 44100, channels: int = 2,
                           metadata: Optional[Dict[str, str]] = None) -> bytes:
        """Generate a valid audio file in the specified format with optional metadata."""
        if format.lower() not in [f.lower() for f in self.SUPPORTED_FORMATS]:
            raise ValueError(f"Unsupported format: {format}")
        
        # Use default metadata if none provided
        if metadata is None:
            metadata = self.default_metadata.copy()
        
        # Generate audio data based on format
        if format.lower() == 'wav':
            return self._generate_wav_audio(duration, sample_rate, channels, metadata)
        else:
            # For other formats, generate WAV first then convert
            # Note: In a real implementation, you'd use libraries like pydub or ffmpeg
            # For testing purposes, we'll create format-specific headers
            return self._generate_format_specific_audio(format, duration, sample_rate, channels, metadata)
    
    def _generate_wav_audio(self, duration: int, sample_rate: int, channels: int, 
                          metadata: Dict[str, str]) -> bytes:
        """Generate WAV audio data with metadata."""
        frames = duration * sample_rate
        
        # Generate sine wave data (440 Hz)
        audio_data = []
        for i in range(frames):
            t = i / sample_rate
            # Generate a 440 Hz sine wave with some variation
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * t))
            
            if channels == 2:
                audio_data.extend([sample, int(sample * 0.9)])  # Slightly different L/R
            else:
                audio_data.append(sample)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Pack audio data as 16-bit signed integers
            packed_data = struct.pack('<' + 'h' * len(audio_data), *audio_data)
            wav_file.writeframes(packed_data)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _generate_format_specific_audio(self, format: str, duration: int, 
                                      sample_rate: int, channels: int,
                                      metadata: Dict[str, str]) -> bytes:
        """Generate format-specific audio data (simplified for testing)."""
        # Generate base WAV data
        wav_data = self._generate_wav_audio(duration, sample_rate, channels, metadata)
        
        # Create format-specific headers/wrappers
        format_lower = format.lower()
        
        if format_lower == 'mp3':
            return self._create_mock_mp3(wav_data, metadata)
        elif format_lower == 'flac':
            return self._create_mock_flac(wav_data, metadata)
        elif format_lower == 'aac':
            return self._create_mock_aac(wav_data, metadata)
        elif format_lower == 'ogg':
            return self._create_mock_ogg(wav_data, metadata)
        elif format_lower == 'm4a':
            return self._create_mock_m4a(wav_data, metadata)
        else:
            return wav_data
    
    def _add_wav_metadata(self, wav_data: bytes, metadata: Dict[str, str]) -> bytes:
        """Add metadata to WAV file (simplified approach)."""
        # For testing purposes, we'll append metadata as a comment
        # In real implementation, this would use proper INFO chunks
        metadata_json = json.dumps(metadata).encode('utf-8')
        return wav_data + b'META' + len(metadata_json).to_bytes(4, 'little') + metadata_json
    
    def _create_mock_mp3(self, wav_data: bytes, metadata: Dict[str, str]) -> bytes:
        """Create mock MP3 file with ID3 header."""
        # Simplified MP3 header with ID3v2 tag
        id3_header = b'ID3\x03\x00\x00\x00\x00\x00\x00'
        mp3_header = b'\xff\xfb\x90\x00'  # MP3 frame header
        metadata_bytes = json.dumps(metadata).encode('utf-8')
        return id3_header + metadata_bytes[:100] + mp3_header + wav_data[44:]  # Skip WAV header
    
    def _create_mock_flac(self, wav_data: bytes, metadata: Dict[str, str]) -> bytes:
        """Create mock FLAC file."""
        flac_header = b'fLaC'
        metadata_block = json.dumps(metadata).encode('utf-8')[:100]
        return flac_header + metadata_block + wav_data[44:]
    
    def _create_mock_aac(self, wav_data: bytes, metadata: Dict[str, str]) -> bytes:
        """Create mock AAC file."""
        aac_header = b'\xff\xf1\x50\x80'  # ADTS header
        return aac_header + wav_data[44:]
    
    def _create_mock_ogg(self, wav_data: bytes, metadata: Dict[str, str]) -> bytes:
        """Create mock OGG file."""
        ogg_header = b'OggS\x00\x02\x00\x00'
        metadata_bytes = json.dumps(metadata).encode('utf-8')[:100]
        return ogg_header + metadata_bytes + wav_data[44:]
    
    def _create_mock_m4a(self, wav_data: bytes, metadata: Dict[str, str]) -> bytes:
        """Create mock M4A file."""
        m4a_header = b'\x00\x00\x00\x20ftypM4A '
        return m4a_header + wav_data[44:]
    
    def generate_invalid_audio(self) -> bytes:
        """Generate invalid/corrupted audio data."""
        # Return random bytes that don't form a valid audio file
        return b'INVALID_AUDIO_DATA' + bytes([random.randint(0, 255) for _ in range(1000)])
    
    def generate_empty_audio(self) -> bytes:
        """Generate empty audio file."""
        return b''
    
    def generate_oversized_audio(self) -> bytes:
        """Generate audio file exceeding the 100MB limit."""
        # Calculate duration needed for ~105MB file
        # WAV: ~10MB per minute for stereo 44.1kHz 16-bit
        duration_minutes = self.OVERSIZED_FILE_SIZE_MB // 10 + 1
        duration_seconds = duration_minutes * 60
        
        return self.generate_valid_audio(duration=duration_seconds)
    
    def generate_large_audio_near_limit(self) -> bytes:
        """Generate large audio file just under the 100MB limit."""
        # Calculate duration for ~95MB file
        duration_minutes = self.LARGE_FILE_SIZE_MB // 10
        duration_seconds = duration_minutes * 60
        
        return self.generate_valid_audio(duration=duration_seconds)
    
    def generate_large_audio(self, size_mb: int) -> bytes:
        """Generate large audio file of specified size in MB."""
        # Calculate duration needed for target size (approximate)
        # WAV file: ~10MB per minute for stereo 44.1kHz 16-bit
        duration_minutes = max(1, size_mb // 10)
        duration_seconds = duration_minutes * 60
        
        return self.generate_valid_audio(duration=duration_seconds)
    
    def generate_corrupted_audio(self, format: str = 'wav') -> bytes:
        """Generate corrupted audio file with valid header but corrupted data."""
        valid_audio = self.generate_valid_audio(format=format, duration=2)
        
        # Corrupt the middle portion of the file
        audio_bytes = bytearray(valid_audio)
        start_corrupt = len(audio_bytes) // 3
        end_corrupt = 2 * len(audio_bytes) // 3
        
        for i in range(start_corrupt, end_corrupt):
            audio_bytes[i] = random.randint(0, 255)
        
        return bytes(audio_bytes)
    
    def generate_malformed_headers(self, format: str = 'wav') -> List[Tuple[str, bytes]]:
        """Generate files with malformed headers for each format."""
        malformed_files = []
        
        # Truncated header
        valid_audio = self.generate_valid_audio(format=format, duration=1)
        truncated = valid_audio[:10]  # Only first 10 bytes
        malformed_files.append((f"truncated_{format}", truncated))
        
        # Wrong magic bytes
        wrong_magic = b'WRONG' + valid_audio[5:]
        malformed_files.append((f"wrong_magic_{format}", wrong_magic))
        
        # Invalid size fields
        if len(valid_audio) > 8:
            invalid_size = bytearray(valid_audio)
            invalid_size[4:8] = b'\xff\xff\xff\xff'  # Invalid size
            malformed_files.append((f"invalid_size_{format}", bytes(invalid_size)))
        
        return malformed_files
    
    def generate_edge_case_audio(self) -> List[Tuple[str, bytes]]:
        """Generate edge case audio files for testing."""
        edge_cases = []
        
        # Zero duration audio (minimal WAV file)
        try:
            zero_duration = self.generate_valid_audio(duration=0)
            edge_cases.append(("zero_duration", zero_duration))
        except Exception:
            # Create minimal valid WAV file
            minimal_wav = self._create_minimal_wav()
            edge_cases.append(("minimal_duration", minimal_wav))
        
        # Mono audio
        mono_audio = self.generate_valid_audio(channels=1, duration=2)
        edge_cases.append(("mono_audio", mono_audio))
        
        # High sample rate audio
        high_sample_rate = self.generate_valid_audio(sample_rate=96000, duration=1)
        edge_cases.append(("high_sample_rate", high_sample_rate))
        
        # Low sample rate audio
        low_sample_rate = self.generate_valid_audio(sample_rate=8000, duration=2)
        edge_cases.append(("low_sample_rate", low_sample_rate))
        
        # Very short audio (1 second)
        short_audio = self.generate_valid_audio(duration=1)
        edge_cases.append(("short_audio", short_audio))
        
        # Empty file
        edge_cases.append(("empty_file", self.generate_empty_audio()))
        
        # File with only header (no audio data)
        header_only = self._create_header_only_wav()
        edge_cases.append(("header_only", header_only))
        
        return edge_cases
    
    def _create_minimal_wav(self) -> bytes:
        """Create minimal valid WAV file."""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b'\x00\x00')  # Single silent sample
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_header_only_wav(self) -> bytes:
        """Create WAV file with header but no audio data."""
        # WAV header without data
        header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        return header
    
    def save_audio_file(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to a file and return the file path."""
        file_path = self.temp_dir / filename
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        return str(file_path)
    
    def create_test_audio_set(self) -> Dict[str, str]:
        """Create a comprehensive set of test audio files and return their paths."""
        test_files = {}
        
        # Valid audio files in all supported formats
        for format in self.SUPPORTED_FORMATS:
            # Create with default metadata
            audio_data = self.generate_valid_audio(format=format, duration=3)
            filename = f"test_audio_valid.{format}"
            file_path = self.save_audio_file(audio_data, filename)
            test_files[f"valid_{format}"] = file_path
            
            # Create with custom metadata
            custom_metadata = {
                'title': f'Test {format.upper()} File',
                'artist': f'{format.upper()} Test Artist',
                'album': f'{format.upper()} Test Album',
                'year': '2024',
                'genre': 'Electronic Test',
                'comment': f'Generated {format} file for metadata testing'
            }
            audio_with_metadata = self.generate_valid_audio(
                format=format, duration=2, metadata=custom_metadata
            )
            metadata_filename = f"test_audio_metadata.{format}"
            metadata_path = self.save_audio_file(audio_with_metadata, metadata_filename)
            test_files[f"metadata_{format}"] = metadata_path
        
        # Invalid audio files
        invalid_data = self.generate_invalid_audio()
        invalid_path = self.save_audio_file(invalid_data, "invalid_audio.bin")
        test_files["invalid"] = invalid_path
        
        # Empty audio file
        empty_data = self.generate_empty_audio()
        empty_path = self.save_audio_file(empty_data, "empty_audio.wav")
        test_files["empty"] = empty_path
        
        # Corrupted audio files for each format
        for format in ['wav', 'mp3', 'flac']:
            corrupted_data = self.generate_corrupted_audio(format=format)
            corrupted_path = self.save_audio_file(corrupted_data, f"corrupted_audio.{format}")
            test_files[f"corrupted_{format}"] = corrupted_path
        
        # Large audio file (near limit)
        large_data = self.generate_large_audio_near_limit()
        large_path = self.save_audio_file(large_data, "large_audio_near_limit.wav")
        test_files["large_near_limit"] = large_path
        
        # Oversized audio file (exceeds limit) - only create if needed for testing
        # Note: This creates a very large file, so we'll create a smaller version for testing
        oversized_data = self.generate_large_audio(size_mb=10)  # 10MB for testing instead of 105MB
        oversized_path = self.save_audio_file(oversized_data, "oversized_audio.wav")
        test_files["oversized"] = oversized_path
        
        # Edge case files
        edge_cases = self.generate_edge_case_audio()
        for case_name, case_data in edge_cases:
            case_path = self.save_audio_file(case_data, f"{case_name}.wav")
            test_files[case_name] = case_path
        
        # Malformed header files
        for format in ['wav', 'mp3']:
            malformed_cases = self.generate_malformed_headers(format=format)
            for malformed_name, malformed_data in malformed_cases:
                malformed_path = self.save_audio_file(malformed_data, f"{malformed_name}.{format}")
                test_files[malformed_name] = malformed_path
        
        return test_files
    
    def create_format_test_set(self, format: str) -> Dict[str, str]:
        """Create a test set focused on a specific audio format."""
        if format.lower() not in [f.lower() for f in self.SUPPORTED_FORMATS]:
            raise ValueError(f"Unsupported format: {format}")
        
        test_files = {}
        format_lower = format.lower()
        
        # Valid file with different characteristics
        test_files[f"valid_{format_lower}"] = self.save_audio_file(
            self.generate_valid_audio(format=format, duration=5),
            f"valid.{format_lower}"
        )
        
        # Short duration
        test_files[f"short_{format_lower}"] = self.save_audio_file(
            self.generate_valid_audio(format=format, duration=1),
            f"short.{format_lower}"
        )
        
        # Mono
        test_files[f"mono_{format_lower}"] = self.save_audio_file(
            self.generate_valid_audio(format=format, channels=1, duration=3),
            f"mono.{format_lower}"
        )
        
        # High quality
        test_files[f"hq_{format_lower}"] = self.save_audio_file(
            self.generate_valid_audio(format=format, sample_rate=48000, duration=2),
            f"high_quality.{format_lower}"
        )
        
        # With metadata
        metadata = {
            'title': f'Format Test {format.upper()}',
            'artist': 'Test Suite',
            'album': 'Format Testing',
            'year': '2024'
        }
        test_files[f"metadata_{format_lower}"] = self.save_audio_file(
            self.generate_valid_audio(format=format, duration=3, metadata=metadata),
            f"with_metadata.{format_lower}"
        )
        
        # Corrupted
        test_files[f"corrupted_{format_lower}"] = self.save_audio_file(
            self.generate_corrupted_audio(format=format),
            f"corrupted.{format_lower}"
        )
        
        return test_files
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB."""
        try:
            size_bytes = Path(file_path).stat().st_size
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
    
    def cleanup_test_files(self, file_paths: List[str]):
        """Clean up generated test files."""
        for file_path in file_paths:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass  # Ignore cleanup errors
    
    def cleanup_all_test_files(self):
        """Clean up all files in the temp directory."""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors
    
    def validate_generated_file(self, file_path: str, expected_format: str = None) -> Dict[str, Any]:
        """Validate a generated audio file and return information about it."""
        validation_result = {
            'exists': False,
            'size_bytes': 0,
            'size_mb': 0.0,
            'format_detected': None,
            'is_valid': False,
            'error': None
        }
        
        try:
            path = Path(file_path)
            if not path.exists():
                validation_result['error'] = 'File does not exist'
                return validation_result
            
            validation_result['exists'] = True
            validation_result['size_bytes'] = path.stat().st_size
            validation_result['size_mb'] = validation_result['size_bytes'] / (1024 * 1024)
            
            # Read first few bytes to detect format
            with open(path, 'rb') as f:
                header = f.read(12)
            
            # Detect format based on header
            if header.startswith(b'RIFF') and b'WAVE' in header:
                validation_result['format_detected'] = 'wav'
                validation_result['is_valid'] = len(header) >= 12
            elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                validation_result['format_detected'] = 'mp3'
                validation_result['is_valid'] = True
            elif header.startswith(b'fLaC'):
                validation_result['format_detected'] = 'flac'
                validation_result['is_valid'] = True
            elif header.startswith(b'OggS'):
                validation_result['format_detected'] = 'ogg'
                validation_result['is_valid'] = True
            elif b'ftyp' in header:
                validation_result['format_detected'] = 'm4a'
                validation_result['is_valid'] = True
            elif header.startswith(b'\xff\xf1'):
                validation_result['format_detected'] = 'aac'
                validation_result['is_valid'] = True
            else:
                validation_result['format_detected'] = 'unknown'
                validation_result['is_valid'] = False
            
            # Check if detected format matches expected
            if expected_format and validation_result['format_detected'] != expected_format.lower():
                validation_result['error'] = f"Expected {expected_format}, detected {validation_result['format_detected']}"
                validation_result['is_valid'] = False
                
        except Exception as e:
            validation_result['error'] = str(e)
        
        return validation_result