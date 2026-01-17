"""
API Router for audio processing tools
Provides endpoints for format conversion, trimming, merging, compression, and extraction
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Literal
import logging
import io

from .error_models import ErrorResponse, ErrorCode, create_error_response, get_http_status

logger = logging.getLogger(__name__)

# Create router for audio tools
router = APIRouter(prefix="/api", tags=["audio-tools"])


def create_http_exception(code: ErrorCode, details: str = None) -> HTTPException:
    """
    Create HTTPException with standardized error response
    
    Args:
        code: Error code
        details: Optional detailed error information
        
    Returns:
        HTTPException with error response
    """
    error_response = create_error_response(code, details)
    return HTTPException(
        status_code=get_http_status(code),
        detail=error_response.model_dump()
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns status and FFmpeg availability within 100ms
    Requirements: 10.6
    """
    import time
    from .ffmpeg_wrapper import FFmpegWrapper
    
    start_time = time.time()
    
    try:
        ffmpeg = FFmpegWrapper()
        ffmpeg_available = ffmpeg.check_availability()
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        status_value = "healthy" if ffmpeg_available else "unhealthy"
        
        logger.debug(f"Health check completed in {response_time_ms:.2f}ms")
        
        return {
            "status": status_value,
            "ffmpeg_available": ffmpeg_available,
            "version": "1.0.0",
            "response_time_ms": round(response_time_ms, 2)
        }
    except Exception as e:
        # Calculate response time even on error
        response_time_ms = (time.time() - start_time) * 1000
        
        logger.error(f"Health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "ffmpeg_available": False,
            "version": "1.0.0",
            "response_time_ms": round(response_time_ms, 2),
            "error": str(e)
        }


@router.post("/convert")
async def convert_audio(
    file: UploadFile = File(...),
    target_format: Literal["mp3", "wav", "flac", "aac", "ogg", "m4a"] = Form(...)
):
    """
    Convert audio file to target format
    Preserves metadata and quality
    Requirements: 1.1, 1.2, 1.4, 9.1
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Convert request: {file.filename} -> {target_format}")
    
    try:
        # Validate audio file
        await InputValidator.validate_audio_file(file)
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Convert format
        ffmpeg = FFmpegWrapper()
        converted_data = ffmpeg.convert_format(
            input_data=file_data,
            input_format=input_format,
            output_format=target_format,
            preserve_metadata=True
        )
        
        # Generate output filename
        original_name = Path(file.filename or "audio").stem
        sanitized_name = InputValidator.sanitize_filename(original_name)
        output_filename = f"{sanitized_name}.{target_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(target_format, "audio/mpeg")
        
        logger.info(f"Conversion successful: {output_filename}")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(converted_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )


@router.post("/trim")
async def trim_audio(
    file: UploadFile = File(...),
    start_time: float = Form(...),
    end_time: float = Form(...)
):
    """
    Trim audio file to specified time range
    Times in seconds
    Requirements: 2.1, 2.2, 2.6, 9.1
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Trim request: {file.filename} from {start_time}s to {end_time}s")
    
    try:
        # Validate audio file
        await InputValidator.validate_audio_file(file)
        
        # Validate time range
        InputValidator.validate_time_range(start_time, end_time)
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Trim audio
        ffmpeg = FFmpegWrapper()
        trimmed_data = ffmpeg.trim_audio(
            input_data=file_data,
            input_format=input_format,
            start_time=start_time,
            end_time=end_time
        )
        
        # Generate output filename
        original_name = Path(file.filename or "audio").stem
        sanitized_name = InputValidator.sanitize_filename(original_name)
        output_filename = f"{sanitized_name}_trimmed.{input_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(input_format, "audio/mpeg")
        
        logger.info(f"Trimming successful: {output_filename}")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(trimmed_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trimming error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Trimming failed: {str(e)}"
        )


@router.post("/merge")
async def merge_audio(
    files: List[UploadFile] = File(...),
    output_format: Literal["mp3", "wav", "flac", "aac", "ogg", "m4a"] = Form(...)
):
    """
    Merge multiple audio files into one
    Handles format conversion and resampling
    Requirements: 3.1, 3.2, 3.5, 9.1
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Merge request: {len(files)} files -> {output_format}")
    
    try:
        # Validate file count (2-10 files)
        if len(files) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 files required for merging"
            )
        
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 files allowed for merging"
            )
        
        # Validate all files and read their data
        input_files_data = []
        input_formats = []
        
        logger.info(f"Processing {len(files)} files for merge")
        
        for i, file in enumerate(files):
            logger.info(f"Processing file {i+1}: {file.filename}")
            
            try:
                # Validate audio file
                await InputValidator.validate_audio_file(file)
                logger.info(f"File {i+1} validation successful")
                
                # Get input format from filename
                input_format = Path(file.filename or "").suffix.lower().lstrip(".")
                logger.debug(f"File {i+1} format: {input_format}")
                
                # Read file data
                logger.debug(f"Reading file {i+1} data...")
                file_data = await file.read()
                logger.info(f"File {i+1} read: {len(file_data)} bytes")
                
                # Check file size
                if len(file_data) > InputValidator.MAX_FILE_SIZE:
                    logger.error(f"File {i+1} exceeds size limit: {len(file_data)} bytes > {InputValidator.MAX_FILE_SIZE}")
                    raise HTTPException(
                        status_code=413,
                        detail=f"File {i+1} exceeds 100MB limit"
                    )
                
                input_files_data.append(file_data)
                input_formats.append(input_format)
                
                logger.info(f"File {i+1} processed successfully: {file.filename} ({input_format}, {len(file_data)} bytes)")
                
            except HTTPException as e:
                logger.error(f"File {i+1} validation failed: {e.detail}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error processing file {i+1}: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing file {i+1}: {str(e)}"
                )
        
        # Merge audio files
        ffmpeg = FFmpegWrapper()
        merged_data = ffmpeg.merge_audio(
            input_files=input_files_data,
            input_formats=input_formats,
            output_format=output_format
        )
        
        # Generate output filename
        output_filename = f"merged_audio.{output_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(output_format, "audio/mpeg")
        
        logger.info(f"Merge successful: {output_filename} ({len(merged_data)} bytes)")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(merged_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Merge failed: {str(e)}"
        )


@router.post("/compress")
async def compress_audio(
    file: UploadFile = File(...),
    level: Literal["low", "medium", "high"] = Form(...)
):
    """
    Compress audio file to reduce size
    Levels: low (320kbps), medium (192kbps), high (128kbps)
    Requirements: 4.1, 4.2, 4.4, 4.5, 9.1
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Compress request: {file.filename} at {level} compression")
    
    try:
        # Validate audio file
        await InputValidator.validate_audio_file(file)
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        original_size = len(file_data)
        
        # Check file size
        if original_size > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Map compression levels to bitrates (Requirement 4.2)
        bitrate_map = {
            "low": "320k",
            "medium": "192k",
            "high": "128k"
        }
        bitrate = bitrate_map[level]
        
        # Calculate estimated file size reduction (Requirement 4.4)
        # Rough estimation: bitrate * duration
        # For estimation purposes, we'll probe the duration
        try:
            probe_command = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                "-i", "pipe:0"
            ]
            
            import subprocess
            probe_result = subprocess.run(
                probe_command,
                input=file_data,
                capture_output=True,
                timeout=10
            )
            
            duration = None
            if probe_result.returncode == 0:
                try:
                    duration = float(probe_result.stdout.decode().strip())
                    logger.debug(f"Audio duration: {duration} seconds")
                except (ValueError, AttributeError):
                    logger.warning("Could not determine duration for size estimation")
            
            # Estimate compressed size if we have duration
            if duration:
                # Bitrate in kbps, duration in seconds
                target_bitrate_kbps = int(bitrate.rstrip('k'))
                estimated_size = int((target_bitrate_kbps * 1000 / 8) * duration)
                reduction_percent = int((1 - estimated_size / original_size) * 100) if estimated_size < original_size else 0
                logger.info(f"Estimated size reduction: {reduction_percent}% (from {original_size} to ~{estimated_size} bytes)")
        except Exception as e:
            logger.warning(f"Size estimation failed: {e}")
        
        # Compress audio
        ffmpeg = FFmpegWrapper()
        compressed_data = ffmpeg.compress_audio(
            input_data=file_data,
            input_format=input_format,
            bitrate=bitrate
        )
        
        compressed_size = len(compressed_data)
        actual_reduction_percent = int((1 - compressed_size / original_size) * 100) if compressed_size < original_size else 0
        
        logger.info(f"Compression complete: {original_size} -> {compressed_size} bytes ({actual_reduction_percent}% reduction)")
        
        # Generate output filename
        original_name = Path(file.filename or "audio").stem
        sanitized_name = InputValidator.sanitize_filename(original_name)
        
        # Determine output format (may change if WAV/FLAC was converted to MP3)
        output_format = input_format
        if input_format in ["wav", "flac"]:
            output_format = "mp3"  # These formats are converted to MP3 for compression
        
        output_filename = f"{sanitized_name}_compressed.{output_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(output_format, "audio/mpeg")
        
        logger.info(f"Compression successful: {output_filename}")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(compressed_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compression error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Compression failed: {str(e)}"
        )


@router.post("/extract")
async def extract_audio(
    file: UploadFile = File(...),
    output_format: Literal["mp3", "wav", "flac", "aac", "ogg", "m4a"] = Form(...)
):
    """
    Extract audio track from video file
    Supports MP4, AVI, MKV, MOV, WEBM
    Requirements: 5.1, 5.2, 5.3, 9.1
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Extract request: {file.filename} -> {output_format}")
    
    try:
        # Validate video file
        await InputValidator.validate_video_file(file)
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Extract audio from video
        ffmpeg = FFmpegWrapper()
        try:
            extracted_data = ffmpeg.extract_audio(
                input_data=file_data,
                input_format=input_format,
                output_format=output_format
            )
        except RuntimeError as e:
            error_msg = str(e)
            # Handle specific error for videos with no audio track (Requirement 5.6)
            if "no audio track" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Video file contains no audio track to extract"
                )
            # Re-raise other runtime errors as 500
            raise HTTPException(
                status_code=500,
                detail=f"Audio extraction failed: {error_msg}"
            )
        
        # Generate output filename
        original_name = Path(file.filename or "video").stem
        sanitized_name = InputValidator.sanitize_filename(original_name)
        output_filename = f"{sanitized_name}_audio.{output_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(output_format, "audio/mpeg")
        
        logger.info(f"Extraction successful: {output_filename} ({len(extracted_data)} bytes)")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(extracted_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/split-audio")
async def split_audio(
    file: UploadFile = File(...),
    split_mode: Literal["time", "segments"] = Form(...),
    interval_duration: int = Form(None),
    segments: str = Form(None)
):
    """
    Split audio file into multiple segments
    Modes: time (equal intervals), segments (custom time ranges)
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import json
    import tempfile
    import os
    
    logger.info(f"Split request: {file.filename} mode={split_mode}")
    
    try:
        # Validate audio file
        await InputValidator.validate_audio_file(file)
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Parse segments for custom mode
        segment_list = []
        if split_mode == "segments":
            if not segments:
                raise HTTPException(
                    status_code=400,
                    detail="Segments data required for custom split mode"
                )
            try:
                segment_list = json.loads(segments)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid segments JSON format"
                )
        
        # Split audio
        ffmpeg = FFmpegWrapper()
        
        if split_mode == "time":
            if not interval_duration:
                raise HTTPException(
                    status_code=400,
                    detail="Interval duration required for time split mode"
                )
            split_files = ffmpeg.split_audio_by_time(
                input_data=file_data,
                input_format=input_format,
                interval_seconds=interval_duration
            )
        else:  # segments mode
            split_files = ffmpeg.split_audio_by_segments(
                input_data=file_data,
                input_format=input_format,
                segments=segment_list
            )
        
        # Create ZIP file with all segments
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, file_data in enumerate(split_files):
                segment_filename = f"segment_{i+1}.{input_format}"
                zip_file.writestr(segment_filename, file_data)
        
        zip_buffer.seek(0)
        
        logger.info(f"Split successful: {len(split_files)} segments created")
        
        # Return ZIP file as download
        return StreamingResponse(
            BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=split_audio_segments.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Split error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Split failed: {str(e)}"
        )


@router.post("/adjust-volume")
async def adjust_volume(
    file: UploadFile = File(...),
    adjustment_mode: Literal["percentage", "decibels", "normalize"] = Form(...),
    volume_percentage: int = Form(None),
    decibel_change: float = Form(None),
    normalize_target: float = Form(None)
):
    """
    Adjust audio volume levels
    Modes: percentage (0-500%), decibels (-30 to +30), normalize (target dB)
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Volume adjust request: {file.filename} mode={adjustment_mode}")
    
    try:
        # Validate audio file
        await InputValidator.validate_audio_file(file)
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Validate adjustment parameters
        if adjustment_mode == "percentage":
            if volume_percentage is None:
                raise HTTPException(
                    status_code=400,
                    detail="Volume percentage required for percentage mode"
                )
            if not (0 <= volume_percentage <= 500):
                raise HTTPException(
                    status_code=400,
                    detail="Volume percentage must be between 0 and 500"
                )
        elif adjustment_mode == "decibels":
            if decibel_change is None:
                raise HTTPException(
                    status_code=400,
                    detail="Decibel change required for decibels mode"
                )
            if not (-30 <= decibel_change <= 30):
                raise HTTPException(
                    status_code=400,
                    detail="Decibel change must be between -30 and +30"
                )
        elif adjustment_mode == "normalize":
            if normalize_target is None:
                raise HTTPException(
                    status_code=400,
                    detail="Normalize target required for normalize mode"
                )
            if not (-20 <= normalize_target <= 0):
                raise HTTPException(
                    status_code=400,
                    detail="Normalize target must be between -20 and 0 dB"
                )
        
        # Adjust volume
        ffmpeg = FFmpegWrapper()
        adjusted_data = ffmpeg.adjust_volume(
            input_data=file_data,
            input_format=input_format,
            adjustment_mode=adjustment_mode,
            volume_percentage=volume_percentage,
            decibel_change=decibel_change,
            normalize_target=normalize_target
        )
        
        # Generate output filename
        original_name = Path(file.filename or "audio").stem
        sanitized_name = InputValidator.sanitize_filename(original_name)
        output_filename = f"{sanitized_name}_volume_adjusted.{input_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(input_format, "audio/mpeg")
        
        logger.info(f"Volume adjustment successful: {output_filename}")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(adjusted_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Volume adjustment error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Volume adjustment failed: {str(e)}"
        )


@router.post("/change-speed")
async def change_speed(
    file: UploadFile = File(...),
    speed: float = Form(...),
    preserve_pitch: bool = Form(True)
):
    """
    Change audio playback speed
    Speed: 0.25x to 4.0x
    Preserve pitch: maintain original pitch while changing speed
    """
    from .ffmpeg_wrapper import FFmpegWrapper
    from .validators import InputValidator
    from pathlib import Path
    import io
    
    logger.info(f"Speed change request: {file.filename} speed={speed}x pitch_preserve={preserve_pitch}")
    
    try:
        # Validate audio file
        await InputValidator.validate_audio_file(file)
        
        # Validate speed parameter
        if not (0.25 <= speed <= 4.0):
            raise HTTPException(
                status_code=400,
                detail="Speed must be between 0.25x and 4.0x"
            )
        
        # Get input format from filename
        input_format = Path(file.filename or "").suffix.lower().lstrip(".")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > InputValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        
        # Change speed
        ffmpeg = FFmpegWrapper()
        speed_changed_data = ffmpeg.change_speed(
            input_data=file_data,
            input_format=input_format,
            speed=speed,
            preserve_pitch=preserve_pitch
        )
        
        # Generate output filename
        original_name = Path(file.filename or "audio").stem
        sanitized_name = InputValidator.sanitize_filename(original_name)
        speed_suffix = f"{speed:.2f}x".replace(".", "_")
        output_filename = f"{sanitized_name}_speed_{speed_suffix}.{input_format}"
        
        # Determine MIME type
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_types.get(input_format, "audio/mpeg")
        
        logger.info(f"Speed change successful: {output_filename}")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(speed_changed_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speed change error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Speed change failed: {str(e)}"
        )
