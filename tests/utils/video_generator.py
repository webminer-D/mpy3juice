"""
Video file generator for creating test data.
Generates valid, invalid, and edge case video files for comprehensive testing.
"""

import io
import os
import struct
import random
import json
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime


class VideoFileGenerator:
    """Creates test video files in various formats, sizes, and characteristics."""
    
    SUPPORTED_FORMATS = ['mp4', 'avi', 'mkv', 'mov', 'webm']
    
    # File size limits for testing (in MB)
    MAX_FILE_SIZE_MB = 100
    LARGE_FILE_SIZE_MB = 95  # Just under limit
    OVERSIZED_FILE_SIZE_MB = 105  # Over limit
    
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Default metadata for test files
        self.default_metadata = {
            'title': 'Test Video File',
            'artist': 'Test Creator',
            'album': 'Test Collection',
            'year': '2024',
            'genre': 'Test',
            'comment': 'Generated for testing purposes'
        }
    
    def generate_valid_video(self, format: str = 'mp4', duration: int = 5, 
                           width: int = 640, height: int = 480,
                           has_audio: bool = True, fps: int = 30,
                           metadata: Optional[Dict[str, str]] = None) -> bytes:
        """Generate a valid video file in the specified format with optional audio track."""
        if format.lower() not in [f.lower() for f in self.SUPPORTED_FORMATS]:
            raise ValueError(f"Unsupported format: {format}")
        
        # Use default metadata if none provided
        if metadata is None:
            metadata = self.default_metadata.copy()
        
        # Generate video data based on format
        format_lower = format.lower()
        
        if format_lower == 'mp4':
            return self._generate_mp4_video(duration, width, height, has_audio, fps, metadata)
        elif format_lower == 'avi':
            return self._generate_avi_video(duration, width, height, has_audio, fps, metadata)
        elif format_lower == 'mkv':
            return self._generate_mkv_video(duration, width, height, has_audio, fps, metadata)
        elif format_lower == 'mov':
            return self._generate_mov_video(duration, width, height, has_audio, fps, metadata)
        elif format_lower == 'webm':
            return self._generate_webm_video(duration, width, height, has_audio, fps, metadata)
        else:
            return self._generate_generic_video(format, duration, width, height, has_audio, fps, metadata)
    
    def _generate_mp4_video(self, duration: int, width: int, height: int, 
                          has_audio: bool, fps: int, metadata: Dict[str, str]) -> bytes:
        """Generate MP4 video data with proper headers."""
        # Simplified MP4 structure for testing
        
        # File type box (ftyp)
        ftyp_data = b'mp41\x00\x00\x00\x00mp41isom'
        ftyp_size = len(ftyp_data) + 8
        ftyp_box = struct.pack('>I', ftyp_size) + b'ftyp' + ftyp_data
        
        # Simplified movie header (mvhd)
        mvhd_data = b'\x00' * 100  # Simplified header data
        mvhd_size = len(mvhd_data) + 8
        mvhd_box = struct.pack('>I', mvhd_size) + b'mvhd' + mvhd_data
        
        # Video track data (simplified)
        video_track_data = b'\x00' * 200  # Simplified track data
        if has_audio:
            video_track_data += b'\x00' * 100  # Add audio track data
        
        # Movie box (moov)
        moov_content = mvhd_box + video_track_data
        moov_size = len(moov_content) + 8
        moov_box = struct.pack('>I', moov_size) + b'moov' + moov_content
        
        # Media data box (mdat) - contains actual video/audio data
        frame_count = duration * fps
        frame_size = max(100, width * height // 1000)  # Simplified frame size
        
        # Generate dummy video frames
        video_data = b''
        for frame in range(min(frame_count, 30)):  # Limit frames for testing
            frame_data = bytes([
                (frame + i) % 256 for i in range(frame_size)
            ])
            video_data += frame_data
        
        # Add audio data if needed
        audio_data = b''
        if has_audio:
            # Generate simple audio data
            sample_count = duration * 1000  # 1000 samples per second for testing
            for i in range(sample_count):
                t = i / 1000.0
                sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * t))
                audio_data += struct.pack('<h', sample)
        
        mdat_content = video_data + audio_data
        mdat_size = len(mdat_content) + 8
        mdat_box = struct.pack('>I', mdat_size) + b'mdat' + mdat_content
        
        # Combine all boxes
        return ftyp_box + moov_box + mdat_box
    
    def _create_video_track_data(self, width: int, height: int, fps: int, duration: int) -> bytes:
        """Create video track data for MP4."""
        # Simplified video track - just return placeholder data
        return b'\x00' * 100
    
    def _create_audio_track_data(self, duration: int) -> bytes:
        """Create audio track data for MP4."""
        # Simplified audio track - just return placeholder data
        return b'\x00' * 50
    
    def _generate_avi_video(self, duration: int, width: int, height: int, 
                          has_audio: bool, fps: int, metadata: Dict[str, str]) -> bytes:
        """Generate AVI video data."""
        # Simplified AVI structure
        riff_header = b'RIFF'
        
        # Create basic AVI content
        avi_content = b'AVI LIST' + b'\x00' * 100  # Simplified header
        
        # Add video data
        video_data = bytes([i % 256 for i in range(duration * 100)])  # Simple video data
        
        # Add audio data if needed
        audio_data = b''
        if has_audio:
            audio_data = bytes([i % 128 for i in range(duration * 50)])  # Simple audio data
        
        content = b'AVI ' + avi_content + video_data + audio_data
        file_size = len(content)
        
        return riff_header + struct.pack('<I', file_size) + content

    
    def _generate_mkv_video(self, duration: int, width: int, height: int, 
                          has_audio: bool, fps: int, metadata: Dict[str, str]) -> bytes:
        """Generate MKV (Matroska) video data."""
        # Simplified Matroska structure
        ebml_header = (
            b'\x1a\x45\xdf\xa3'  # EBML signature
            b'\x9f'  # Size
            b'\x42\x86\x81\x01'  # EBMLVersion = 1
            b'\x42\xf7\x81\x01'  # EBMLReadVersion = 1
            b'\x42\xf2\x81\x04'  # EBMLMaxIDLength = 4
            b'\x42\xf3\x81\x08'  # EBMLMaxSizeLength = 8
            b'\x42\x82\x88matroska'  # DocType = "matroska"
            b'\x42\x87\x81\x02'  # DocTypeVersion = 2
            b'\x42\x85\x81\x02'  # DocTypeReadVersion = 2
        )
        
        # Simplified segment
        segment_header = b'\x18\x53\x80\x67\x8f'  # Segment with size
        segment_content = b'\x00' * 200  # Simplified content
        
        # Add video data
        video_data = bytes([i % 256 for i in range(duration * 100)])
        
        # Add audio data if needed
        audio_data = b''
        if has_audio:
            audio_data = bytes([i % 128 for i in range(duration * 50)])
        
        return ebml_header + segment_header + segment_content + video_data + audio_data

    
    def _generate_mov_video(self, duration: int, width: int, height: int, 
                          has_audio: bool, fps: int, metadata: Dict[str, str]) -> bytes:
        """Generate MOV (QuickTime) video data."""
        # Simplified MOV structure
        ftyp_data = b'qt  \x00\x00\x00\x00qt  '
        ftyp_size = len(ftyp_data) + 8
        ftyp_atom = struct.pack('>I', ftyp_size) + b'ftyp' + ftyp_data
        
        # Simplified movie atom
        moov_content = b'\x00' * 200  # Simplified movie data
        moov_size = len(moov_content) + 8
        moov_atom = struct.pack('>I', moov_size) + b'moov' + moov_content
        
        # Media data
        video_data = bytes([i % 256 for i in range(duration * 100)])
        audio_data = b''
        if has_audio:
            audio_data = bytes([i % 128 for i in range(duration * 50)])
        
        mdat_content = video_data + audio_data
        mdat_size = len(mdat_content) + 8
        mdat_atom = struct.pack('>I', mdat_size) + b'mdat' + mdat_content
        
        return ftyp_atom + moov_atom + mdat_atom

    
    def _generate_webm_video(self, duration: int, width: int, height: int, 
                           has_audio: bool, fps: int, metadata: Dict[str, str]) -> bytes:
        """Generate WebM video data."""
        # Simplified WebM structure
        ebml_header = (
            b'\x1a\x45\xdf\xa3'  # EBML signature
            b'\x9f'  # Size
            b'\x42\x86\x81\x01'  # EBMLVersion = 1
            b'\x42\xf7\x81\x01'  # EBMLReadVersion = 1
            b'\x42\xf2\x81\x04'  # EBMLMaxIDLength = 4
            b'\x42\xf3\x81\x08'  # EBMLMaxSizeLength = 8
            b'\x42\x82\x84webm'  # DocType = "webm"
            b'\x42\x87\x81\x02'  # DocTypeVersion = 2
            b'\x42\x85\x81\x02'  # DocTypeReadVersion = 2
        )
        
        # Simplified segment
        segment_header = b'\x18\x53\x80\x67\x8f'  # Segment with size
        segment_content = b'\x00' * 200  # Simplified content
        
        # Add video data
        video_data = bytes([i % 256 for i in range(duration * 100)])
        
        # Add audio data if needed
        audio_data = b''
        if has_audio:
            audio_data = bytes([i % 128 for i in range(duration * 50)])
        
        return ebml_header + segment_header + segment_content + video_data + audio_data

    
    def _generate_generic_video(self, format: str, duration: int, width: int, height: int, 
                              has_audio: bool, fps: int, metadata: Dict[str, str]) -> bytes:
        """Generate generic video file for unsupported formats."""
        # Create a basic file with format-specific header
        header = f"VIDEO_{format.upper()}_FILE".encode('utf-8')
        
        # Add basic video properties
        properties = json.dumps({
            'format': format,
            'duration': duration,
            'width': width,
            'height': height,
            'has_audio': has_audio,
            'fps': fps,
            'metadata': metadata
        }).encode('utf-8')
        
        # Generate some dummy video data
        frame_count = duration * fps
        video_data = bytes([i % 256 for i in range(min(frame_count * 100, 10000))])
        
        return header + b'\n' + properties + b'\n' + video_data
    
    def generate_video_without_audio(self, format: str = 'mp4', duration: int = 5, 
                                   width: int = 640, height: int = 480, fps: int = 30) -> bytes:
        """Generate video file without audio track."""
        return self.generate_valid_video(format, duration, width, height, has_audio=False, fps=fps)
    
    def generate_video_with_audio(self, format: str = 'mp4', duration: int = 5, 
                                width: int = 640, height: int = 480, fps: int = 30) -> bytes:
        """Generate video file with audio track."""
        return self.generate_valid_video(format, duration, width, height, has_audio=True, fps=fps)
    
    def generate_invalid_video(self) -> bytes:
        """Generate invalid/corrupted video data."""
        return b'INVALID_VIDEO_DATA' + bytes([random.randint(0, 255) for _ in range(1000)])
    
    def generate_empty_video(self) -> bytes:
        """Generate empty video file."""
        return b''
    
    def generate_corrupted_video(self, format: str = 'mp4') -> bytes:
        """Generate corrupted video file with valid header but corrupted data."""
        valid_video = self.generate_valid_video(format=format, duration=2)
        
        # Corrupt the middle portion of the file
        video_bytes = bytearray(valid_video)
        start_corrupt = len(video_bytes) // 3
        end_corrupt = 2 * len(video_bytes) // 3
        
        for i in range(start_corrupt, min(end_corrupt, len(video_bytes))):
            video_bytes[i] = random.randint(0, 255)
        
        return bytes(video_bytes)
    
    def generate_oversized_video(self) -> bytes:
        """Generate video file exceeding the 100MB limit."""
        # Create a large video by increasing duration
        # Approximate: 1 minute of simple video ≈ 10-20MB
        duration_minutes = self.OVERSIZED_FILE_SIZE_MB // 15 + 1
        duration_seconds = duration_minutes * 60
        
        return self.generate_valid_video(duration=duration_seconds)
    
    def generate_large_video_near_limit(self) -> bytes:
        """Generate large video file just under the 100MB limit."""
        duration_minutes = self.LARGE_FILE_SIZE_MB // 15
        duration_seconds = max(60, duration_minutes * 60)  # At least 1 minute
        
        return self.generate_valid_video(duration=duration_seconds)
    
    def generate_edge_case_videos(self) -> List[Tuple[str, bytes]]:
        """Generate edge case video files for testing."""
        edge_cases = []
        
        # Zero duration video (minimal file)
        try:
            zero_duration = self.generate_valid_video(duration=0)
            edge_cases.append(("zero_duration", zero_duration))
        except Exception:
            # Create minimal valid video file
            minimal_video = self._create_minimal_video()
            edge_cases.append(("minimal_duration", minimal_video))
        
        # Very short video (1 second)
        short_video = self.generate_valid_video(duration=1)
        edge_cases.append(("short_video", short_video))
        
        # Small resolution video
        small_video = self.generate_valid_video(width=160, height=120, duration=2)
        edge_cases.append(("small_resolution", small_video))
        
        # Large resolution video
        large_video = self.generate_valid_video(width=1920, height=1080, duration=1)
        edge_cases.append(("large_resolution", large_video))
        
        # High FPS video
        high_fps_video = self.generate_valid_video(fps=60, duration=2)
        edge_cases.append(("high_fps", high_fps_video))
        
        # Low FPS video
        low_fps_video = self.generate_valid_video(fps=15, duration=2)
        edge_cases.append(("low_fps", low_fps_video))
        
        # Empty file
        edge_cases.append(("empty_file", self.generate_empty_video()))
        
        # Video without audio
        no_audio_video = self.generate_video_without_audio(duration=3)
        edge_cases.append(("no_audio", no_audio_video))
        
        return edge_cases
    
    def _create_minimal_video(self) -> bytes:
        """Create minimal valid video file."""
        # Create a very basic MP4 with minimal content
        ftyp = b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41'
        moov = b'\x00\x00\x00\x08moov'
        mdat = b'\x00\x00\x00\x08mdat'
        return ftyp + moov + mdat
    
    def save_video_file(self, video_data: bytes, filename: str) -> str:
        """Save video data to a file and return the file path."""
        file_path = self.temp_dir / filename
        with open(file_path, 'wb') as f:
            f.write(video_data)
        return str(file_path)
    
    def create_test_video_set(self) -> Dict[str, str]:
        """Create a comprehensive set of test video files and return their paths."""
        test_files = {}
        
        # Valid video files in all supported formats
        for format in self.SUPPORTED_FORMATS:
            # Video with audio
            video_with_audio = self.generate_video_with_audio(format=format, duration=3)
            filename_with_audio = f"test_video_with_audio.{format}"
            file_path_with_audio = self.save_video_file(video_with_audio, filename_with_audio)
            test_files[f"valid_with_audio_{format}"] = file_path_with_audio
            
            # Video without audio
            video_without_audio = self.generate_video_without_audio(format=format, duration=3)
            filename_without_audio = f"test_video_without_audio.{format}"
            file_path_without_audio = self.save_video_file(video_without_audio, filename_without_audio)
            test_files[f"valid_without_audio_{format}"] = file_path_without_audio
        
        # Invalid video file
        invalid_data = self.generate_invalid_video()
        invalid_path = self.save_video_file(invalid_data, "invalid_video.bin")
        test_files["invalid"] = invalid_path
        
        # Empty video file
        empty_data = self.generate_empty_video()
        empty_path = self.save_video_file(empty_data, "empty_video.mp4")
        test_files["empty"] = empty_path
        
        # Corrupted video files for each format
        for format in ['mp4', 'avi', 'mkv']:
            corrupted_data = self.generate_corrupted_video(format=format)
            corrupted_path = self.save_video_file(corrupted_data, f"corrupted_video.{format}")
            test_files[f"corrupted_{format}"] = corrupted_path
        
        # Large video file (near limit) - create smaller version for testing
        large_data = self.generate_valid_video(duration=30)  # 30 seconds instead of very large
        large_path = self.save_video_file(large_data, "large_video_near_limit.mp4")
        test_files["large_near_limit"] = large_path
        
        # Oversized video file - create moderate size for testing
        oversized_data = self.generate_valid_video(duration=60)  # 1 minute for testing
        oversized_path = self.save_video_file(oversized_data, "oversized_video.mp4")
        test_files["oversized"] = oversized_path
        
        # Edge case files
        edge_cases = self.generate_edge_case_videos()
        for case_name, case_data in edge_cases:
            case_path = self.save_video_file(case_data, f"{case_name}.mp4")
            test_files[case_name] = case_path
        
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
        """Validate a generated video file and return information about it."""
        validation_result = {
            'exists': False,
            'size_bytes': 0,
            'size_mb': 0.0,
            'format_detected': None,
            'has_audio_track': None,
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
                header = f.read(32)
            
            # Detect format based on header
            if b'ftyp' in header and (b'mp41' in header or b'isom' in header):
                validation_result['format_detected'] = 'mp4'
                validation_result['is_valid'] = True
            elif header.startswith(b'RIFF') and b'AVI ' in header:
                validation_result['format_detected'] = 'avi'
                validation_result['is_valid'] = True
            elif header.startswith(b'\x1a\x45\xdf\xa3'):  # EBML signature
                if b'matroska' in header or b'webm' in header:
                    validation_result['format_detected'] = 'mkv' if b'matroska' in header else 'webm'
                    validation_result['is_valid'] = True
            elif b'ftyp' in header and b'qt  ' in header:
                validation_result['format_detected'] = 'mov'
                validation_result['is_valid'] = True
            else:
                validation_result['format_detected'] = 'unknown'
                validation_result['is_valid'] = False
            
            # Try to detect audio track (simplified check)
            with open(path, 'rb') as f:
                content = f.read(min(1024, validation_result['size_bytes']))
                # Look for audio-related signatures
                has_audio_indicators = [
                    b'soun',  # QuickTime/MP4 audio track
                    b'auds',  # AVI audio stream
                    b'A_VORBIS', b'A_AAC',  # Matroska/WebM audio codecs
                    b'\x01wb',  # AVI audio chunk
                ]
                validation_result['has_audio_track'] = any(indicator in content for indicator in has_audio_indicators)
            
            # Check if detected format matches expected
            if expected_format and validation_result['format_detected'] != expected_format.lower():
                validation_result['error'] = f"Expected {expected_format}, detected {validation_result['format_detected']}"
                validation_result['is_valid'] = False
                
        except Exception as e:
            validation_result['error'] = str(e)
        
        return validation_result