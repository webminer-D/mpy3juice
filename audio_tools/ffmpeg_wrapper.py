"""
FFmpeg wrapper for audio and video processing
Handles subprocess execution, error handling, and logging
"""

import subprocess
import logging
import shutil
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegWrapper:
    """
    Wrapper for FFmpeg command execution
    Handles subprocess management and error handling
    Requirements: 9.4, 9.6, 12.3
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize FFmpeg wrapper
        
        Args:
            ffmpeg_path: Path to ffmpeg executable (default: "ffmpeg" from PATH)
        """
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available"""
        if not shutil.which(self.ffmpeg_path):
            logger.error(f"FFmpeg not found at: {self.ffmpeg_path}")
            raise RuntimeError(f"FFmpeg not found. Please install FFmpeg and ensure it's in PATH.")
        
        logger.info(f"FFmpeg found at: {self.ffmpeg_path}")
    
    def check_availability(self) -> bool:
        """
        Check if FFmpeg is available
        Requirements: 10.6
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"FFmpeg availability check failed: {e}")
            return False
    
    def _execute_command(
        self,
        command: List[str],
        input_data: Optional[bytes] = None,
        timeout: int = 300,
        operation: str = "processing",
        filename: Optional[str] = None
    ) -> bytes:
        """
        Execute FFmpeg command with error handling and detailed logging
        Requirements: 9.4, 9.6, 12.3
        
        Args:
            command: FFmpeg command as list of strings
            input_data: Optional input data to pipe to stdin
            timeout: Command timeout in seconds (default: 5 minutes)
            operation: Description of operation for logging (e.g., "conversion", "trimming")
            filename: Optional filename for logging context
            
        Returns:
            Output data from stdout
            
        Raises:
            RuntimeError: If FFmpeg execution fails
        """
        from datetime import datetime
        
        # Log operation start with timestamp and file information
        timestamp = datetime.now().isoformat()
        file_info = f" (file: {filename})" if filename else ""
        input_size = len(input_data) if input_data else 0
        
        logger.info(
            f"[{timestamp}] Starting FFmpeg {operation}{file_info} "
            f"(input size: {input_size} bytes)"
        )
        logger.debug(f"FFmpeg command: {' '.join(command)}")
        
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=input_data, timeout=timeout)
            
            # Capture and log stderr output (Requirements: 12.3, 9.6)
            stderr_text = stderr.decode('utf-8', errors='ignore')
            
            if process.returncode != 0:
                # Log detailed error information with timestamp and file context
                end_timestamp = datetime.now().isoformat()
                logger.error(
                    f"[{end_timestamp}] FFmpeg {operation} failed{file_info} "
                    f"(return code: {process.returncode})"
                )
                logger.error(f"FFmpeg stderr output:\n{stderr_text}")
                
                # Extract meaningful error message from stderr
                error_lines = [line for line in stderr_text.split('\n') if line.strip()]
                meaningful_error = error_lines[-1] if error_lines else "Unknown error"
                
                raise RuntimeError(
                    f"FFmpeg {operation} failed: {meaningful_error}"
                )
            
            # Log stderr even on success (FFmpeg outputs progress info to stderr)
            if stderr_text:
                logger.debug(f"FFmpeg stderr output:\n{stderr_text}")
            
            # Log successful completion with timestamp and output size
            end_timestamp = datetime.now().isoformat()
            output_size = len(stdout)
            logger.info(
                f"[{end_timestamp}] FFmpeg {operation} completed successfully{file_info} "
                f"(output size: {output_size} bytes)"
            )
            
            return stdout
            
        except subprocess.TimeoutExpired:
            process.kill()
            end_timestamp = datetime.now().isoformat()
            logger.error(
                f"[{end_timestamp}] FFmpeg {operation} timed out{file_info} "
                f"(timeout: {timeout}s)"
            )
            raise RuntimeError(f"Processing timed out after {timeout} seconds")
        
        except RuntimeError:
            # Re-raise RuntimeError (already logged above)
            raise
        
        except Exception as e:
            end_timestamp = datetime.now().isoformat()
            logger.error(
                f"[{end_timestamp}] FFmpeg {operation} execution error{file_info}: {str(e)}"
            )
            raise RuntimeError(f"FFmpeg execution failed: {str(e)}")
    
    def convert_format(
        self,
        input_data: bytes,
        input_format: str,
        output_format: str,
        preserve_metadata: bool = True
    ) -> bytes:
        """
        Convert audio between formats
        Requirements: 1.1, 1.2, 1.4
        
        Args:
            input_data: Input audio data
            input_format: Input format (e.g., "mp3", "wav")
            output_format: Output format (e.g., "mp3", "wav")
            preserve_metadata: Whether to preserve metadata
            
        Returns:
            Converted audio data
        """
        # Map user-friendly format names to FFmpeg format names
        # Some formats need special handling for piped output
        ffmpeg_format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "flac": "flac",
            "aac": "adts",  # AAC uses ADTS container for streaming
            "ogg": "ogg",
            "m4a": "mp4",  # M4A uses MP4 container with special flags for streaming
        }
        
        ffmpeg_output_format = ffmpeg_format_map.get(output_format, output_format)
        
        # Build FFmpeg command for format conversion
        command = [
            self.ffmpeg_path,
            "-i", "pipe:0",  # Read from stdin
        ]
        
        # Preserve metadata if requested (copy all metadata streams)
        if preserve_metadata:
            command.extend([
                "-map_metadata", "0",  # Copy global metadata
                "-id3v2_version", "3",  # Use ID3v2.3 for MP3 compatibility
            ])
        
        # Format-specific codec and quality settings
        # Maintain high quality during conversion
        codec_settings = self._get_codec_settings(output_format)
        command.extend(codec_settings)
        
        # Special handling for M4A/MP4 to support piped output
        if output_format == "m4a":
            command.extend([
                "-movflags", "frag_keyframe+empty_moov",  # Enable fragmented MP4 for streaming
            ])
        
        # Output format
        command.extend([
            "-f", ffmpeg_output_format,  # Output format (FFmpeg name)
            "pipe:1"  # Write to stdout
        ])
        
        logger.info(f"Converting {input_format} to {output_format} (FFmpeg format: {ffmpeg_output_format}, preserve_metadata={preserve_metadata})")
        return self._execute_command(
            command, 
            input_data, 
            operation="format conversion",
            filename=f"input.{input_format}"
        )
    
    def _get_codec_settings(self, output_format: str) -> List[str]:
        """
        Get codec settings for output format to maintain quality
        Requirements: 1.3
        
        Args:
            output_format: Output format
            
        Returns:
            List of FFmpeg arguments for codec settings
        """
        # Format-specific codec settings to preserve quality
        codec_map = {
            "mp3": ["-codec:a", "libmp3lame", "-q:a", "0"],  # VBR highest quality
            "wav": ["-codec:a", "pcm_s16le"],  # 16-bit PCM
            "flac": ["-codec:a", "flac", "-compression_level", "5"],  # FLAC compression
            "aac": ["-codec:a", "aac", "-b:a", "256k"],  # AAC 256kbps
            "ogg": ["-codec:a", "libvorbis", "-q:a", "8"],  # Vorbis quality 8
            "m4a": ["-codec:a", "aac", "-b:a", "256k"],  # M4A with AAC
        }
        
        settings = codec_map.get(output_format, [])
        logger.debug(f"Codec settings for {output_format}: {settings}")
        return settings
    
    def trim_audio(
        self,
        input_data: bytes,
        input_format: str,
        start_time: float,
        end_time: float
    ) -> bytes:
        """
        Trim audio to time range
        Requirements: 2.1, 2.3, 2.4
        
        Args:
            input_data: Input audio data
            input_format: Input format
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Trimmed audio data
            
        Note:
            If end_time exceeds the audio duration, FFmpeg will automatically
            trim to the end of the file (Requirement 2.4)
        """
        duration = end_time - start_time
        
        # Map user-friendly format names to FFmpeg format names for piped I/O
        ffmpeg_format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "flac": "flac",
            "aac": "adts",  # AAC uses ADTS container for streaming
            "ogg": "ogg",
            "m4a": "mp4",  # M4A uses MP4 container
        }
        
        ffmpeg_output_format = ffmpeg_format_map.get(input_format, input_format)
        
        command = [
            self.ffmpeg_path,
            "-i", "pipe:0",  # Read from stdin
            "-ss", str(start_time),  # Start time
            "-t", str(duration),  # Duration
            "-c", "copy",  # Copy codec (no re-encoding, maintains quality)
            "-f", ffmpeg_output_format,  # Output format
        ]
        
        # Special handling for M4A/MP4 to support piped output
        if input_format == "m4a":
            command.extend([
                "-movflags", "frag_keyframe+empty_moov",  # Enable fragmented MP4 for streaming
            ])
        
        command.append("pipe:1")  # Write to stdout
        
        logger.info(f"Trimming audio from {start_time}s to {end_time}s (duration: {duration}s)")
        return self._execute_command(
            command, 
            input_data,
            operation="audio trimming",
            filename=f"input.{input_format}"
        )
    
    def merge_audio(
        self,
        input_files: List[bytes],
        input_formats: List[str],
        output_format: str
    ) -> bytes:
        """
        Merge multiple audio files
        Requirements: 3.1, 3.3, 3.4
        
        Args:
            input_files: List of input audio data
            input_formats: List of input formats
            output_format: Output format
            
        Returns:
            Merged audio data
            
        Note:
            - Handles format conversion for mixed formats (Requirement 3.3)
            - Implements sample rate unification to highest sample rate (Requirement 3.4)
            - Preserves order of input files (Requirement 3.1)
        """
        import os
        from .cleanup import temporary_directory
        
        logger.info(f"Merging {len(input_files)} audio files to {output_format}")
        
        if len(input_files) != len(input_formats):
            raise ValueError("Number of input files must match number of input formats")
        
        if len(input_files) < 2:
            raise ValueError("At least 2 files required for merging")
        
        # Map user-friendly format names to FFmpeg format names for output
        ffmpeg_format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "flac": "flac",
            "aac": "adts",
            "ogg": "ogg",
            "m4a": "mp4",
        }
        
        ffmpeg_output_format = ffmpeg_format_map.get(output_format, output_format)
        
        # Use cleanup manager for automatic cleanup (Requirements: 10.5, 11.4)
        with temporary_directory(prefix="audio_merge_") as temp_dir:
            try:
                # Step 1: Probe all input files to get their sample rates
                # This is needed for sample rate unification (Requirement 3.4)
                sample_rates = []
                
                for i, (file_data, file_format) in enumerate(zip(input_files, input_formats)):
                    probe_command = [
                        "ffprobe",
                        "-v", "error",
                        "-select_streams", "a:0",
                        "-show_entries", "stream=sample_rate",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        "-i", "pipe:0"
                    ]
                    
                    probe_result = subprocess.run(
                        probe_command,
                        input=file_data,
                        capture_output=True,
                        timeout=10
                    )
                    
                    if probe_result.returncode == 0:
                        try:
                            sample_rate = int(probe_result.stdout.decode().strip())
                            sample_rates.append(sample_rate)
                            logger.debug(f"File {i} ({file_format}): sample rate = {sample_rate} Hz")
                        except (ValueError, AttributeError):
                            # Default to 44100 if we can't determine sample rate
                            sample_rates.append(44100)
                            logger.warning(f"Could not determine sample rate for file {i}, using default 44100 Hz")
                    else:
                        # Default to 44100 if probe fails
                        sample_rates.append(44100)
                        logger.warning(f"Probe failed for file {i}, using default sample rate 44100 Hz")
                
                # Determine the maximum sample rate for unification (Requirement 3.4)
                max_sample_rate = max(sample_rates) if sample_rates else 44100
                logger.info(f"Unified sample rate: {max_sample_rate} Hz")
                
                # Step 2: Create temporary files for intermediate processing
                # FFmpeg's concat demuxer requires files on disk
                temp_files = []
                concat_list_path = os.path.join(temp_dir, "concat_list.txt")
                
                # Step 3: Convert all files to a common intermediate format with unified sample rate
                # This handles both format conversion (Requirement 3.3) and sample rate unification (Requirement 3.4)
                for i, (file_data, file_format) in enumerate(zip(input_files, input_formats)):
                    # Create temporary file for this input
                    temp_file_path = os.path.join(temp_dir, f"input_{i}.wav")
                    temp_files.append(temp_file_path)
                    
                    # Convert to WAV with unified sample rate as intermediate format
                    # WAV is lossless and works well as intermediate format
                    convert_command = [
                        self.ffmpeg_path,
                        "-i", "pipe:0",  # Read from stdin
                        "-ar", str(max_sample_rate),  # Resample to unified sample rate
                        "-ac", "2",  # Stereo (or mono if source is mono, FFmpeg handles this)
                        "-f", "wav",  # Output as WAV
                        temp_file_path
                    ]
                    
                    logger.debug(f"Converting file {i} to intermediate format with sample rate {max_sample_rate} Hz")
                    
                    process = subprocess.Popen(
                        convert_command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    stdout, stderr = process.communicate(input=file_data, timeout=300)
                    
                    if process.returncode != 0:
                        error_msg = stderr.decode('utf-8', errors='ignore')
                        logger.error(f"Failed to convert file {i}: {error_msg}")
                        raise RuntimeError(f"Failed to convert file {i} for merging: {error_msg}")
                
                # Step 4: Create concat list file for FFmpeg
                # Format: file 'path' (one per line)
                with open(concat_list_path, 'w') as f:
                    for temp_file in temp_files:
                        # Use absolute paths and escape single quotes
                        abs_path = os.path.abspath(temp_file)
                        f.write(f"file '{abs_path}'\n")
                
                logger.debug(f"Created concat list with {len(temp_files)} files")
                
                # Step 5: Concatenate all files using FFmpeg's concat demuxer
                # This preserves the order of files (Requirement 3.1)
                concat_command = [
                    self.ffmpeg_path,
                    "-f", "concat",  # Use concat demuxer
                    "-safe", "0",  # Allow absolute paths
                    "-i", concat_list_path,  # Input is the concat list
                ]
                
                # For WAV output, we can use codec copy for efficiency
                # For other formats, we need to re-encode
                if output_format == "wav":
                    concat_command.extend([
                        "-c", "copy",  # Copy codec (no re-encoding for concat)
                        "-f", "wav",  # Output as WAV
                        "pipe:1"  # Write to stdout
                    ])
                else:
                    # Re-encode to ensure proper format
                    # Add codec settings for output format
                    codec_settings = self._get_codec_settings(output_format)
                    concat_command.extend(codec_settings)
                    
                    # Special handling for M4A/MP4 to support piped output
                    if output_format == "m4a":
                        concat_command.extend([
                            "-movflags", "frag_keyframe+empty_moov",
                        ])
                    
                    concat_command.extend([
                        "-f", ffmpeg_output_format,
                        "pipe:1"
                    ])
                
                logger.debug("Concatenating files")
                
                concat_result = subprocess.run(
                    concat_command,
                    capture_output=True,
                    timeout=300
                )
                
                if concat_result.returncode != 0:
                    error_msg = concat_result.stderr.decode('utf-8', errors='ignore')
                    logger.error(f"Concatenation failed: {error_msg}")
                    raise RuntimeError(f"Audio concatenation failed: {error_msg}")
                
                merged_output = concat_result.stdout
                
                logger.info(f"Merge complete (output format: {output_format})")
                return merged_output
                
            except subprocess.TimeoutExpired:
                logger.error("Merge operation timed out")
                raise RuntimeError("Audio merge operation timed out")
            except Exception as e:
                logger.error(f"Merge operation failed: {str(e)}")
                raise RuntimeError(f"Audio merge failed: {str(e)}")
        # Temporary directory is automatically cleaned up here (Requirements: 10.5, 11.4)
    
    def compress_audio(
        self,
        input_data: bytes,
        input_format: str,
        bitrate: str
    ) -> bytes:
        """
        Compress audio to target bitrate
        Requirements: 4.1, 4.2, 4.6
        
        Args:
            input_data: Input audio data
            input_format: Input format
            bitrate: Target bitrate (e.g., "320k", "192k", "128k")
            
        Returns:
            Compressed audio data
            
        Note:
            If the input file is already at or below the target bitrate,
            returns the original file without reprocessing (Requirement 4.6)
        """
        logger.info(f"Compressing audio to {bitrate}")
        
        # Step 1: Probe the input file to get its current bitrate
        # This is needed for bypass logic (Requirement 4.6)
        probe_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-i", "pipe:0"
        ]
        
        try:
            probe_result = subprocess.run(
                probe_command,
                input=input_data,
                capture_output=True,
                timeout=10
            )
            
            current_bitrate = None
            if probe_result.returncode == 0:
                try:
                    # Bitrate is in bits per second, convert to kbps
                    current_bitrate_bps = int(probe_result.stdout.decode().strip())
                    current_bitrate_kbps = current_bitrate_bps // 1000
                    current_bitrate = current_bitrate_kbps
                    logger.info(f"Current bitrate: {current_bitrate} kbps")
                except (ValueError, AttributeError):
                    logger.warning("Could not determine current bitrate, proceeding with compression")
            else:
                logger.warning("Bitrate probe failed, proceeding with compression")
            
            # Step 2: Check if bypass is needed (Requirement 4.6)
            # If current bitrate is at or below target, return original file
            if current_bitrate is not None:
                # Parse target bitrate (e.g., "320k" -> 320)
                target_bitrate_kbps = int(bitrate.rstrip('k'))
                
                if current_bitrate <= target_bitrate_kbps:
                    logger.info(f"Current bitrate ({current_bitrate} kbps) is at or below target ({target_bitrate_kbps} kbps), bypassing compression")
                    return input_data
        
        except Exception as e:
            logger.warning(f"Bitrate check failed: {e}, proceeding with compression")
        
        # Step 3: Build FFmpeg command for compression
        # Map user-friendly format names to FFmpeg format names
        ffmpeg_format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "flac": "flac",
            "aac": "adts",
            "ogg": "ogg",
            "m4a": "mp4",
        }
        
        ffmpeg_output_format = ffmpeg_format_map.get(input_format, input_format)
        
        command = [
            self.ffmpeg_path,
            "-i", "pipe:0",  # Read from stdin
        ]
        
        # Format-specific compression settings
        # Requirements: 4.1, 4.2 - maintain acceptable quality at target bitrate
        if input_format == "mp3":
            command.extend([
                "-codec:a", "libmp3lame",
                "-b:a", bitrate,  # Target bitrate
            ])
        elif input_format == "wav":
            # WAV is uncompressed, convert to MP3 for compression
            command.extend([
                "-codec:a", "libmp3lame",
                "-b:a", bitrate,
            ])
            ffmpeg_output_format = "mp3"
            logger.info("Converting WAV to MP3 for compression")
        elif input_format == "flac":
            # FLAC is lossless, convert to MP3 for compression
            command.extend([
                "-codec:a", "libmp3lame",
                "-b:a", bitrate,
            ])
            ffmpeg_output_format = "mp3"
            logger.info("Converting FLAC to MP3 for compression")
        elif input_format in ["aac", "m4a"]:
            command.extend([
                "-codec:a", "aac",
                "-b:a", bitrate,
            ])
        elif input_format == "ogg":
            # For OGG, use quality-based encoding that approximates the bitrate
            # Map bitrates to vorbis quality levels
            quality_map = {
                "320k": "8",  # ~320 kbps
                "192k": "6",  # ~192 kbps
                "128k": "4",  # ~128 kbps
            }
            quality = quality_map.get(bitrate, "6")
            command.extend([
                "-codec:a", "libvorbis",
                "-q:a", quality,
            ])
        else:
            # Default to MP3 compression for unknown formats
            command.extend([
                "-codec:a", "libmp3lame",
                "-b:a", bitrate,
            ])
            ffmpeg_output_format = "mp3"
            logger.info(f"Converting {input_format} to MP3 for compression")
        
        # Special handling for M4A/MP4 to support piped output
        if input_format == "m4a" or (input_format in ["wav", "flac"] and ffmpeg_output_format == "mp3"):
            if ffmpeg_output_format == "mp4":
                command.extend([
                    "-movflags", "frag_keyframe+empty_moov",
                ])
        
        # Output format
        command.extend([
            "-f", ffmpeg_output_format,
            "pipe:1"  # Write to stdout
        ])
        
        logger.info(f"Compressing {input_format} to {bitrate} (output format: {ffmpeg_output_format})")
        return self._execute_command(
            command,
            input_data,
            operation="audio compression",
            filename=f"input.{input_format}"
        )
    
    def extract_audio(
        self,
        input_data: bytes,
        input_format: str,
        output_format: str
    ) -> bytes:
        """
        Extract audio from video
        Requirements: 5.1, 5.2, 5.6
        
        Args:
            input_data: Input video data
            input_format: Input video format (mp4, avi, mkv, mov, webm)
            output_format: Output audio format (mp3, wav, flac, aac, ogg, m4a)
            
        Returns:
            Extracted audio data
            
        Raises:
            RuntimeError: If video has no audio track or extraction fails
        """
        logger.info(f"Extracting audio from {input_format} video to {output_format} audio")
        
        # Map user-friendly format names to FFmpeg format names for output
        ffmpeg_format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "flac": "flac",
            "aac": "adts",  # AAC uses ADTS container for streaming
            "ogg": "ogg",
            "m4a": "mp4",  # M4A uses MP4 container
        }
        
        ffmpeg_output_format = ffmpeg_format_map.get(output_format, output_format)
        
        # Step 1: Probe the video to check if it has an audio track
        # This handles Requirement 5.6 - detect videos with no audio track
        probe_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",  # Select first audio stream
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-i", "pipe:0"
        ]
        
        try:
            probe_result = subprocess.run(
                probe_command,
                input=input_data,
                capture_output=True,
                timeout=10
            )
            
            # Check if audio stream was found
            if probe_result.returncode != 0 or not probe_result.stdout.strip():
                logger.error(f"No audio track found in {input_format} video")
                raise RuntimeError("Video file contains no audio track to extract")
            
            # Verify the stream is actually audio
            stream_type = probe_result.stdout.decode().strip()
            if stream_type != "audio":
                logger.error(f"Expected audio stream but found: {stream_type}")
                raise RuntimeError("Video file contains no audio track to extract")
            
            logger.debug(f"Audio track detected in video")
            
        except subprocess.TimeoutExpired:
            logger.error("Audio track probe timed out")
            raise RuntimeError("Failed to probe video file for audio track")
        except RuntimeError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Audio track probe failed: {str(e)}")
            raise RuntimeError(f"Failed to check for audio track: {str(e)}")
        
        # Step 2: Build FFmpeg command to extract audio stream
        # Requirements: 5.1, 5.2 - extract audio from all supported video formats
        command = [
            self.ffmpeg_path,
            "-i", "pipe:0",  # Read video from stdin
            "-vn",  # Disable video (extract audio only)
            "-map", "0:a:0",  # Map first audio stream
        ]
        
        # Add codec settings for output format to preserve quality (Requirement 5.4)
        codec_settings = self._get_codec_settings(output_format)
        command.extend(codec_settings)
        
        # Special handling for M4A/MP4 to support piped output
        if output_format == "m4a":
            command.extend([
                "-movflags", "frag_keyframe+empty_moov",  # Enable fragmented MP4 for streaming
            ])
        
        # Output format
        command.extend([
            "-f", ffmpeg_output_format,  # Output format (FFmpeg name)
            "pipe:1"  # Write to stdout
        ])
        
        logger.info(f"Extracting audio from {input_format} to {output_format} (FFmpeg format: {ffmpeg_output_format})")
        
        try:
            return self._execute_command(
                command, 
                input_data,
                operation="audio extraction",
                filename=f"input.{input_format}"
            )
        except RuntimeError as e:
            # Enhance error message for audio extraction failures
            error_msg = str(e)
            if "no audio" in error_msg.lower() or "stream" in error_msg.lower():
                raise RuntimeError("Failed to extract audio: video may not contain a valid audio track")
            raise

    def split_audio_by_time(
        self,
        input_data: bytes,
        input_format: str,
        interval_seconds: int
    ) -> List[bytes]:
        """
        Split audio into equal time intervals
        
        Args:
            input_data: Input audio data
            input_format: Input audio format
            interval_seconds: Duration of each segment in seconds
            
        Returns:
            List of audio segment data
        """
        logger.info(f"Splitting {input_format} audio into {interval_seconds}s intervals")
        
        # First, get the total duration
        probe_command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-i", "pipe:0"
        ]
        
        try:
            probe_result = subprocess.run(
                probe_command,
                input=input_data,
                capture_output=True,
                timeout=10
            )
            
            if probe_result.returncode != 0:
                raise RuntimeError("Failed to probe audio duration")
            
            duration_str = probe_result.stdout.decode().strip()
            logger.info(f"Raw duration output: '{duration_str}'")
            
            # Handle 'N/A' or empty output
            if duration_str == 'N/A' or not duration_str:
                # Try alternative method using stream info
                alt_probe_command = [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    "-i", "pipe:0"
                ]
                
                alt_probe_result = subprocess.run(
                    alt_probe_command,
                    input=input_data,
                    capture_output=True,
                    timeout=10
                )
                
                if alt_probe_result.returncode == 0:
                    duration_str = alt_probe_result.stdout.decode().strip()
                    logger.info(f"Alternative duration output: '{duration_str}'")
                
                # If still N/A, try decoding method as last resort
                if duration_str == 'N/A' or not duration_str:
                    logger.info("Trying decode method to determine duration")
                    decode_probe_command = [
                        "ffprobe",
                        "-v", "error",
                        "-f", "null",
                        "-show_entries", "packet=pts_time",
                        "-select_streams", "a:0",
                        "-of", "csv=p=0",
                        "-i", "pipe:0"
                    ]
                    
                    decode_result = subprocess.run(
                        decode_probe_command,
                        input=input_data,
                        capture_output=True,
                        timeout=30  # Longer timeout for decode
                    )
                    
                    if decode_result.returncode == 0:
                        # Get the last timestamp
                        lines = decode_result.stdout.decode().strip().split('\n')
                        if lines and lines[-1]:
                            try:
                                duration = float(lines[-1])
                                logger.info(f"Duration from decode method: {duration} seconds")
                            except ValueError:
                                duration_str = 'N/A'
                    
                    if duration_str == 'N/A' or not duration_str:
                        # Final fallback: use ffmpeg to decode and count
                        logger.info("Using ffmpeg decode fallback for duration")
                        fallback_command = [
                            self.ffmpeg_path,
                            "-i", "pipe:0",
                            "-f", "null",
                            "-v", "error",
                            "-stats",
                            "-"
                        ]
                        
                        fallback_result = subprocess.run(
                            fallback_command,
                            input=input_data,
                            capture_output=True,
                            timeout=30
                        )
                        
                        # Parse duration from ffmpeg stats output
                        if fallback_result.returncode == 0:
                            stderr_output = fallback_result.stderr.decode('utf-8')
                            # Look for time= pattern in stderr
                            import re
                            time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', stderr_output)
                            if time_match:
                                hours, minutes, seconds = time_match.groups()
                                duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                                logger.info(f"Duration from ffmpeg stats: {duration} seconds")
                            else:
                                raise ValueError(f"Could not determine duration from any method")
                        else:
                            raise ValueError(f"All duration detection methods failed")
            else:
                duration = float(duration_str)
                
            logger.info(f"Final audio duration: {duration} seconds")
            
        except (ValueError, subprocess.TimeoutExpired) as e:
            logger.error(f"Duration probe failed: {e}")
            raise RuntimeError("Failed to determine audio duration")
        
        # Calculate number of segments
        num_segments = int(duration / interval_seconds) + (1 if duration % interval_seconds > 0 else 0)
        logger.info(f"Creating {num_segments} segments")
        
        segments = []
        for i in range(num_segments):
            start_time = i * interval_seconds
            end_time = min((i + 1) * interval_seconds, duration)
            
            # Map format for FFmpeg output compatibility
            output_format = input_format
            if input_format == "m4a":
                output_format = "mp4"  # FFmpeg uses mp4 for m4a output
            elif input_format == "mp4":
                output_format = "mp4"
            
            command = [
                self.ffmpeg_path,
                "-i", "pipe:0",
                "-ss", str(start_time),
                "-t", str(end_time - start_time),
                "-c", "copy",  # Copy without re-encoding for speed
                "-f", output_format,
                "pipe:1"
            ]
            
            try:
                segment_data = self._execute_command(
                    command,
                    input_data,
                    operation=f"split segment {i+1}",
                    filename=f"segment_{i+1}.{input_format}"
                )
                segments.append(segment_data)
                logger.debug(f"Segment {i+1} created: {len(segment_data)} bytes")
                
            except RuntimeError as e:
                logger.error(f"Failed to create segment {i+1}: {e}")
                raise RuntimeError(f"Failed to create segment {i+1}: {str(e)}")
        
        logger.info(f"Split complete: {len(segments)} segments created")
        return segments

    def split_audio_by_segments(
        self,
        input_data: bytes,
        input_format: str,
        segments: List[dict]
    ) -> List[bytes]:
        """
        Split audio into custom segments
        
        Args:
            input_data: Input audio data
            input_format: Input audio format
            segments: List of segment dicts with 'start', 'end', 'name' keys
            
        Returns:
            List of audio segment data
        """
        logger.info(f"Splitting {input_format} audio into {len(segments)} custom segments")
        
        segment_files = []
        for i, segment in enumerate(segments):
            start_time = segment['start']
            end_time = segment['end']
            duration = end_time - start_time
            
            if duration <= 0:
                logger.warning(f"Skipping invalid segment {i+1}: duration {duration}s")
                continue
            
            # Map format for FFmpeg output compatibility
            output_format = input_format
            if input_format == "m4a":
                output_format = "mp4"  # FFmpeg uses mp4 for m4a output
            elif input_format == "mp4":
                output_format = "mp4"
            
            command = [
                self.ffmpeg_path,
                "-i", "pipe:0",
                "-ss", str(start_time),
                "-t", str(duration),
                "-c", "copy",  # Copy without re-encoding for speed
                "-f", output_format,
                "pipe:1"
            ]
            
            try:
                segment_data = self._execute_command(
                    command,
                    input_data,
                    operation=f"split segment {segment.get('name', f'segment_{i+1}')}",
                    filename=f"{segment.get('name', f'segment_{i+1}')}.{input_format}"
                )
                segment_files.append(segment_data)
                logger.debug(f"Segment '{segment.get('name', f'segment_{i+1}')}' created: {len(segment_data)} bytes")
                
            except RuntimeError as e:
                logger.error(f"Failed to create segment '{segment.get('name', f'segment_{i+1}')}': {e}")
                raise RuntimeError(f"Failed to create segment '{segment.get('name', f'segment_{i+1}')}': {str(e)}")
        
        logger.info(f"Split complete: {len(segment_files)} segments created")
        return segment_files

    def adjust_volume(
        self,
        input_data: bytes,
        input_format: str,
        adjustment_mode: str,
        volume_percentage: int = None,
        decibel_change: float = None,
        normalize_target: float = None
    ) -> bytes:
        """
        Adjust audio volume levels
        
        Args:
            input_data: Input audio data
            input_format: Input audio format
            adjustment_mode: 'percentage', 'decibels', or 'normalize'
            volume_percentage: Volume percentage (0-500) for percentage mode
            decibel_change: Decibel change (-30 to +30) for decibels mode
            normalize_target: Target dB level (-20 to 0) for normalize mode
            
        Returns:
            Volume-adjusted audio data
        """
        logger.info(f"Adjusting volume: mode={adjustment_mode}")
        
        command = [
            self.ffmpeg_path,
            "-i", "pipe:0"
        ]
        
        if adjustment_mode == "percentage":
            # Convert percentage to volume filter value
            volume_factor = volume_percentage / 100.0
            command.extend(["-af", f"volume={volume_factor}"])
            logger.info(f"Volume adjustment: {volume_percentage}% (factor: {volume_factor})")
            
        elif adjustment_mode == "decibels":
            command.extend(["-af", f"volume={decibel_change}dB"])
            logger.info(f"Volume adjustment: {decibel_change:+.1f} dB")
            
        elif adjustment_mode == "normalize":
            # Use loudnorm filter for normalization
            command.extend(["-af", f"loudnorm=I={normalize_target}"])
            logger.info(f"Volume normalization: target {normalize_target} dB")
        
        command.extend([
            "-c:a", "libmp3lame" if input_format == "mp3" else "copy",
            "-f", input_format,
            "pipe:1"
        ])
        
        try:
            return self._execute_command(
                command,
                input_data,
                operation="volume adjustment",
                filename=f"input.{input_format}"
            )
        except RuntimeError as e:
            logger.error(f"Volume adjustment failed: {e}")
            raise RuntimeError(f"Volume adjustment failed: {str(e)}")

    def change_speed(
        self,
        input_data: bytes,
        input_format: str,
        speed: float,
        preserve_pitch: bool = True
    ) -> bytes:
        """
        Change audio playback speed
        
        Args:
            input_data: Input audio data
            input_format: Input audio format
            speed: Speed multiplier (0.25 to 4.0)
            preserve_pitch: Whether to preserve original pitch
            
        Returns:
            Speed-changed audio data
        """
        logger.info(f"Changing speed: {speed}x, preserve_pitch={preserve_pitch}")
        
        command = [
            self.ffmpeg_path,
            "-i", "pipe:0"
        ]
        
        if preserve_pitch:
            # Use atempo filter to change speed while preserving pitch
            # atempo has limits, so we may need to chain multiple filters
            if speed <= 0.5:
                # For very slow speeds, chain multiple atempo filters
                command.extend(["-af", f"atempo=0.5,atempo={speed/0.5}"])
            elif speed >= 2.0:
                # For very fast speeds, chain multiple atempo filters
                command.extend(["-af", f"atempo=2.0,atempo={speed/2.0}"])
            else:
                command.extend(["-af", f"atempo={speed}"])
        else:
            # Use asetrate to change speed without preserving pitch (chipmunk effect)
            # First get the original sample rate, then multiply by speed
            command.extend(["-af", f"asetrate=44100*{speed},aresample=44100"])
        
        command.extend([
            "-c:a", "libmp3lame" if input_format == "mp3" else "aac",
            "-f", input_format,
            "pipe:1"
        ])
        
        try:
            return self._execute_command(
                command,
                input_data,
                operation="speed change",
                filename=f"input.{input_format}"
            )
        except RuntimeError as e:
            logger.error(f"Speed change failed: {e}")
            raise RuntimeError(f"Speed change failed: {str(e)}")
