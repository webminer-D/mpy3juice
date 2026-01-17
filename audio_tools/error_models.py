"""
Error response models and error handling utilities
Provides standardized error responses with user-friendly messages
Requirements: 12.1, 9.5
"""

from pydantic import BaseModel
from typing import Optional, Dict
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for audio toolkit operations"""
    
    # Validation errors (400)
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    INVALID_TIME_RANGE = "INVALID_TIME_RANGE"
    INVALID_COMPRESSION_LEVEL = "INVALID_COMPRESSION_LEVEL"
    CORRUPTED_FILE = "CORRUPTED_FILE"
    NO_AUDIO_TRACK = "NO_AUDIO_TRACK"
    INVALID_FILE_COUNT = "INVALID_FILE_COUNT"
    MALFORMED_REQUEST = "MALFORMED_REQUEST"
    
    # Processing errors (500)
    PROCESSING_FAILED = "PROCESSING_FAILED"
    FFMPEG_ERROR = "FFMPEG_ERROR"
    INSUFFICIENT_MEMORY = "INSUFFICIENT_MEMORY"
    
    # Resource errors (413, 429, 504)
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    
    # Not found errors (404)
    NOT_FOUND = "NOT_FOUND"


class ErrorResponse(BaseModel):
    """
    Standardized error response model
    Requirements: 12.1, 9.5
    
    Attributes:
        error: Short error description
        details: Detailed technical information (optional)
        suggestion: User-friendly suggestion for resolution (optional)
        code: Error code for programmatic handling
    """
    error: str
    details: Optional[str] = None
    suggestion: Optional[str] = None
    code: ErrorCode


# Error code to HTTP status code mapping
ERROR_STATUS_MAP: Dict[ErrorCode, int] = {
    # Validation errors (400)
    ErrorCode.UNSUPPORTED_FORMAT: 400,
    ErrorCode.INVALID_TIME_RANGE: 400,
    ErrorCode.INVALID_COMPRESSION_LEVEL: 400,
    ErrorCode.CORRUPTED_FILE: 400,
    ErrorCode.NO_AUDIO_TRACK: 400,
    ErrorCode.INVALID_FILE_COUNT: 400,
    ErrorCode.MALFORMED_REQUEST: 400,
    
    # Resource errors
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.RATE_LIMIT: 429,
    ErrorCode.TIMEOUT: 504,
    
    # Processing errors (500)
    ErrorCode.PROCESSING_FAILED: 500,
    ErrorCode.FFMPEG_ERROR: 500,
    ErrorCode.INSUFFICIENT_MEMORY: 500,
    
    # Not found errors (404)
    ErrorCode.NOT_FOUND: 404,
}


# User-friendly error messages and suggestions
ERROR_MESSAGES: Dict[ErrorCode, Dict[str, str]] = {
    ErrorCode.FILE_TOO_LARGE: {
        "error": "File too large",
        "suggestion": "File exceeds 100MB limit. Please use a smaller file or compress it first."
    },
    ErrorCode.UNSUPPORTED_FORMAT: {
        "error": "Unsupported format",
        "suggestion": "Format not supported. Please use MP3, WAV, FLAC, AAC, OGG, or M4A for audio, or MP4, AVI, MKV, MOV, WEBM for video."
    },
    ErrorCode.INVALID_TIME_RANGE: {
        "error": "Invalid time range",
        "suggestion": "End time must be greater than start time. Please check your timestamps."
    },
    ErrorCode.INVALID_COMPRESSION_LEVEL: {
        "error": "Invalid compression level",
        "suggestion": "Please select a valid compression level: low (320kbps), medium (192kbps), or high (128kbps)."
    },
    ErrorCode.CORRUPTED_FILE: {
        "error": "File appears to be corrupted",
        "suggestion": "File appears to be corrupted or incomplete. Please try a different file."
    },
    ErrorCode.NO_AUDIO_TRACK: {
        "error": "No audio track found",
        "suggestion": "Video file contains no audio track to extract. Please use a video with audio."
    },
    ErrorCode.INVALID_FILE_COUNT: {
        "error": "Invalid number of files",
        "suggestion": "Please provide between 2 and 10 files for merging."
    },
    ErrorCode.MALFORMED_REQUEST: {
        "error": "Malformed request",
        "suggestion": "Request parameters are invalid. Please check your input and try again."
    },
    ErrorCode.PROCESSING_FAILED: {
        "error": "Processing failed",
        "suggestion": "Processing failed. Please try again or use a different file."
    },
    ErrorCode.FFMPEG_ERROR: {
        "error": "Audio processing error",
        "suggestion": "An error occurred during audio processing. Please try again with a different file."
    },
    ErrorCode.INSUFFICIENT_MEMORY: {
        "error": "Insufficient memory",
        "suggestion": "File is too large to process. Please try a smaller file."
    },
    ErrorCode.TIMEOUT: {
        "error": "Processing timeout",
        "suggestion": "Processing took too long. Please try a smaller file or simpler operation."
    },
    ErrorCode.RATE_LIMIT: {
        "error": "Too many requests",
        "suggestion": "Too many requests. Please wait a moment and try again."
    },
    ErrorCode.NOT_FOUND: {
        "error": "Not found",
        "suggestion": "The requested resource was not found."
    },
}


def create_error_response(
    code: ErrorCode,
    details: Optional[str] = None,
    custom_suggestion: Optional[str] = None
) -> ErrorResponse:
    """
    Create a standardized error response
    
    Args:
        code: Error code
        details: Optional detailed technical information
        custom_suggestion: Optional custom suggestion (overrides default)
        
    Returns:
        ErrorResponse object
    """
    message_info = ERROR_MESSAGES.get(code, {
        "error": "An error occurred",
        "suggestion": "Please try again."
    })
    
    return ErrorResponse(
        error=message_info["error"],
        details=details,
        suggestion=custom_suggestion or message_info.get("suggestion"),
        code=code
    )


def get_http_status(code: ErrorCode) -> int:
    """
    Get HTTP status code for error code
    
    Args:
        code: Error code
        
    Returns:
        HTTP status code (default: 500)
    """
    return ERROR_STATUS_MAP.get(code, 500)
