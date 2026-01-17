"""
Input validation framework for audio processing
Validates file types, sizes, formats, and parameters
"""

import re
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Validates user inputs and uploaded files
    Requirements: 6.2, 11.1, 11.2, 11.5
    """
    
    # Supported formats
    AUDIO_FORMATS = ["mp3", "wav", "flac", "aac", "ogg", "m4a"]
    VIDEO_FORMATS = ["mp4", "avi", "mkv", "mov", "webm"]
    
    # File size limit (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
    
    # Audio file signatures (magic numbers)
    AUDIO_SIGNATURES = {
        "mp3": [b"\xFF\xFB", b"\xFF\xF3", b"\xFF\xF2", b"\xFF\xFA", b"ID3"],
        "wav": [b"RIFF"],
        "flac": [b"fLaC"],
        "aac": [b"\xFF\xF1", b"\xFF\xF9"],
        "ogg": [b"OggS"],
        "m4a": [b"ftyp"],
    }
    
    # Video file signatures
    VIDEO_SIGNATURES = {
        "mp4": [b"ftyp", b"moov"],
        "avi": [b"RIFF"],
        "mkv": [b"\x1A\x45\xDF\xA3"],
        "mov": [b"ftyp", b"moov"],
        "webm": [b"\x1A\x45\xDF\xA3"],
    }
    
    @classmethod
    async def validate_audio_file(cls, file: UploadFile) -> bool:
        """
        Validate audio file type and size
        Requirements: 6.2, 11.1
        
        Args:
            file: Uploaded file to validate
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If validation fails
        """
        # Check file extension
        filename = file.filename or ""
        logger.debug(f"Validating audio file: {filename}")
        
        ext = Path(filename).suffix.lower().lstrip(".")
        logger.debug(f"File extension: {ext}")
        
        if ext not in cls.AUDIO_FORMATS:
            logger.error(f"Unsupported format: {ext}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {ext}. Supported formats: {', '.join(cls.AUDIO_FORMATS)}"
            )
        
        # Read first chunk to check file signature
        logger.debug(f"Reading file signature for {filename}")
        try:
            original_position = file.file.tell() if hasattr(file.file, 'tell') else 0
            logger.debug(f"Original file position: {original_position}")
            
            content = await file.read(8192)
            logger.debug(f"Read {len(content)} bytes for signature validation")
            
            # Reset file pointer to original position
            if hasattr(file.file, 'seek'):
                file.file.seek(original_position)
                logger.debug("Reset file position using file.seek()")
            else:
                await file.seek(0)
                logger.debug("Reset file position using await file.seek(0)")
                
        except Exception as e:
            logger.error(f"Error reading file signature: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Error reading file: {str(e)}"
            )
        
        # Validate file signature
        logger.debug(f"Checking signature for format: {ext}")
        if not cls._check_audio_signature(content, ext):
            logger.error(f"File signature validation failed for {filename}")
            raise HTTPException(
                status_code=400,
                detail=f"File does not match declared format: {ext}"
            )
        
        logger.info(f"Audio file validated: {filename} ({ext})")
        return True
    
    @classmethod
    async def validate_video_file(cls, file: UploadFile) -> bool:
        """
        Validate video file type and size
        Requirements: 5.2, 11.1
        
        Args:
            file: Uploaded file to validate
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If validation fails
        """
        # Check file extension
        filename = file.filename or ""
        ext = Path(filename).suffix.lower().lstrip(".")
        
        if ext not in cls.VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported video format: {ext}. Supported formats: {', '.join(cls.VIDEO_FORMATS)}"
            )
        
        # Read first chunk to check file signature
        original_position = file.file.tell() if hasattr(file.file, 'tell') else 0
        content = await file.read(8192)
        
        # Reset file pointer to original position
        if hasattr(file.file, 'seek'):
            file.file.seek(original_position)
        else:
            await file.seek(0)
        
        # Validate file signature
        if not cls._check_video_signature(content, ext):
            raise HTTPException(
                status_code=400,
                detail=f"File does not match declared format: {ext}"
            )
        
        logger.info(f"Video file validated: {filename} ({ext})")
        return True
    
    @classmethod
    def _check_audio_signature(cls, content: bytes, ext: str) -> bool:
        """Check if file content matches audio format signature"""
        logger.debug(f"Checking audio signature for format: {ext}")
        
        if ext not in cls.AUDIO_SIGNATURES:
            logger.error(f"No signatures defined for format: {ext}")
            return False
        
        # Special handling for MP3 files
        if ext == "mp3":
            return cls._check_mp3_signature(content)
        
        signatures = cls.AUDIO_SIGNATURES[ext]
        logger.debug(f"Checking against {len(signatures)} signatures for {ext}")
        
        for i, sig in enumerate(signatures):
            if sig in content[:512]:  # Check first 512 bytes
                logger.debug(f"Signature {i+1} matched for {ext}: {sig}")
                return True
            else:
                logger.debug(f"Signature {i+1} not found for {ext}: {sig}")
        
        logger.error(f"No matching signatures found for {ext}")
        logger.debug(f"File content preview (first 32 bytes): {content[:32]}")
        logger.debug(f"File content hex: {content[:32].hex()}")
        return False
    
    @classmethod
    def _check_mp3_signature(cls, content: bytes) -> bool:
        """Special MP3 signature checking with more comprehensive detection"""
        logger.debug("Performing comprehensive MP3 signature check")
        
        # Check for ID3 tag at the beginning
        if content.startswith(b"ID3"):
            logger.debug("Found ID3 tag at beginning")
            return True
        
        # Check for MP3 frame sync patterns
        # MP3 frames start with 11 bits set to 1 (0xFFE or 0xFFF)
        for i in range(min(512, len(content) - 1)):
            if i < len(content) - 1:
                # Check for frame sync pattern
                if content[i] == 0xFF and (content[i + 1] & 0xE0) == 0xE0:
                    logger.debug(f"Found MP3 frame sync at position {i}: {content[i:i+2].hex()}")
                    return True
        
        # Check for common MP3 signatures
        mp3_signatures = [b"\xFF\xFB", b"\xFF\xF3", b"\xFF\xF2", b"\xFF\xFA"]
        for sig in mp3_signatures:
            if sig in content[:512]:
                logger.debug(f"Found MP3 signature: {sig.hex()}")
                return True
        
        logger.error("No MP3 signatures found")
        logger.debug(f"File content preview (first 32 bytes): {content[:32]}")
        logger.debug(f"File content hex: {content[:32].hex()}")
        return False
    
    @classmethod
    def _check_video_signature(cls, content: bytes, ext: str) -> bool:
        """Check if file content matches video format signature"""
        if ext not in cls.VIDEO_SIGNATURES:
            return False
        
        signatures = cls.VIDEO_SIGNATURES[ext]
        for sig in signatures:
            if sig in content[:512]:  # Check first 512 bytes
                return True
        return False
    
    @classmethod
    def validate_format(cls, format_str: str, format_type: str = "audio") -> bool:
        """
        Validate audio or video format string
        Requirements: 1.2, 5.2
        
        Args:
            format_str: Format string to validate
            format_type: "audio" or "video"
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If format is invalid
        """
        valid_formats = cls.AUDIO_FORMATS if format_type == "audio" else cls.VIDEO_FORMATS
        
        if format_str not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {format_type} format: {format_str}"
            )
        
        return True
    
    @classmethod
    def validate_time_range(
        cls,
        start_time: float,
        end_time: float,
        duration: Optional[float] = None
    ) -> bool:
        """
        Validate trim time range
        Requirements: 2.2, 2.5
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            duration: Optional audio duration for validation
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If time range is invalid
        """
        # Validate non-negative times
        if start_time < 0:
            raise HTTPException(
                status_code=400,
                detail="Start time must be non-negative"
            )
        
        if end_time < 0:
            raise HTTPException(
                status_code=400,
                detail="End time must be non-negative"
            )
        
        # Validate start < end
        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="End time must be greater than start time"
            )
        
        # Validate against duration if provided
        if duration is not None and start_time > duration:
            raise HTTPException(
                status_code=400,
                detail=f"Start time exceeds audio duration ({duration}s)"
            )
        
        logger.info(f"Time range validated: {start_time}s - {end_time}s")
        return True
    
    @classmethod
    def parse_timestamp(cls, timestamp: str) -> float:
        """
        Parse timestamp in MM:SS or seconds format
        Requirements: 2.2
        
        Args:
            timestamp: Timestamp string (e.g., "1:30" or "90")
            
        Returns:
            Time in seconds
            
        Raises:
            HTTPException: If timestamp format is invalid
        """
        # Try parsing as float (seconds)
        try:
            return float(timestamp)
        except ValueError:
            pass
        
        # Try parsing as MM:SS
        match = re.match(r"^(\d+):(\d{2})$", timestamp)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds
        
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timestamp format: {timestamp}. Use seconds (e.g., '90') or MM:SS (e.g., '1:30')"
        )
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks
        Requirements: 11.5
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name
        
        # Remove or replace dangerous characters
        # Keep alphanumeric, dots, dashes, underscores, spaces
        sanitized = re.sub(r"[^\w\s\-\.]", "_", filename)
        
        # Remove all whitespace characters (including tabs, newlines, etc.)
        # Replace with single space, then strip
        sanitized = re.sub(r"\s+", " ", sanitized)
        
        # Remove leading/trailing dots, spaces, and all whitespace
        sanitized = sanitized.strip(". \t\n\r\f\v")
        
        # Remove any remaining '..' patterns (path traversal attempts)
        while ".." in sanitized:
            sanitized = sanitized.replace("..", ".")
        
        # Remove leading dots again after '..' removal
        sanitized = sanitized.lstrip(".")
        
        # Ensure filename is not empty
        if not sanitized or sanitized.isspace():
            sanitized = "file"
        
        logger.debug(f"Sanitized filename: {filename} -> {sanitized}")
        return sanitized
    
    @classmethod
    def validate_file_count(cls, files: List[UploadFile], min_count: int = 2, max_count: int = 10) -> bool:
        """
        Validate number of files for merge operation
        Requirements: 3.2
        
        Args:
            files: List of uploaded files
            min_count: Minimum number of files
            max_count: Maximum number of files
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If file count is invalid
        """
        count = len(files)
        
        if count < min_count:
            raise HTTPException(
                status_code=400,
                detail=f"At least {min_count} files required for merging"
            )
        
        if count > max_count:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {max_count} files allowed for merging"
            )
        
        logger.info(f"File count validated: {count} files")
        return True
