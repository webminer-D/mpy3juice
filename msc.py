import subprocess
import json
import io
import time
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import audio tools router and error models
from audio_tools.router import router as audio_router
from audio_tools.error_models import ErrorResponse, ErrorCode, create_error_response, get_http_status

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
# Requirements: 10.5, 11.4
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    Handles cleanup of old temporary files on startup
    """
    # Startup: Clean up old temporary files
    from audio_tools.cleanup import cleanup_old_temp_files
    
    logger.info("Running startup cleanup of old temporary files")
    cleanup_old_temp_files(max_age_hours=1)
    logger.info("Startup cleanup complete")
    
    yield
    
    # Shutdown: Could add cleanup here if needed
    logger.info("Application shutting down")


app = FastAPI(
    title="Audio Toolkit API",
    description="Comprehensive audio processing toolkit with format conversion, trimming, merging, compression, and extraction",
    version="1.0.0",
    lifespan=lifespan
)


# Timeout middleware
# Requirements: 10.2 - Set 5-minute timeout for processing operations
class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeout
    Prevents long-running operations from blocking resources
    """
    
    def __init__(self, app, timeout_seconds: int = 300):
        """
        Initialize timeout middleware
        
        Args:
            app: FastAPI application
            timeout_seconds: Timeout in seconds (default: 300 = 5 minutes)
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with timeout enforcement
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response or timeout error
        """
        try:
            # Apply timeout to request processing
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {self.timeout_seconds}s: {request.method} {request.url}")
            
            error_response = create_error_response(
                code=ErrorCode.TIMEOUT,
                details=f"Request exceeded {self.timeout_seconds} second timeout"
            )
            
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content=error_response.model_dump()
            )


# Rate limiting middleware
# Requirements: 10.4, 11.6 - Limit concurrent requests to prevent resource exhaustion
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit concurrent requests
    Prevents resource exhaustion from too many simultaneous operations
    """
    
    def __init__(self, app, max_concurrent: int = 10):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            max_concurrent: Maximum concurrent requests (default: 10)
        """
        super().__init__(app)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = 0
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response or rate limit error
        """
        # Skip rate limiting for health check endpoint
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Try to acquire semaphore (non-blocking)
        acquired = self.semaphore.locked() == False
        
        if not acquired and self.active_requests >= self.max_concurrent:
            # Too many concurrent requests
            logger.warning(
                f"Rate limit exceeded: {self.active_requests}/{self.max_concurrent} "
                f"concurrent requests for {request.method} {request.url}"
            )
            
            error_response = create_error_response(
                code=ErrorCode.RATE_LIMIT,
                details=f"Too many concurrent requests ({self.max_concurrent} limit)"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response.model_dump()
            )
        
        # Acquire semaphore and process request
        async with self.semaphore:
            async with self.lock:
                self.active_requests += 1
            
            try:
                logger.debug(f"Processing request ({self.active_requests}/{self.max_concurrent} active)")
                response = await call_next(request)
                return response
            finally:
                async with self.lock:
                    self.active_requests -= 1


# Add timeout middleware (5 minutes for processing operations)
app.add_middleware(TimeoutMiddleware, timeout_seconds=300)

# Add rate limiting middleware (10 concurrent requests)
app.add_middleware(RateLimitMiddleware, max_concurrent=10)

# CORS middleware configuration
# Requirements: 9.5, 11.3
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.mp3juices.sbs",
        "https://mp3juices.sbs", 
        "http://localhost:5179",
        "http://localhost:3000",
        "http://127.0.0.1:5179",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Add Vite dev server default port
        "http://127.0.0.1:5173"   # Add Vite dev server default port
    ],  # Specific origins instead of wildcard when using credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["*"],  # Allow all headers
)

# Include audio tools router
app.include_router(audio_router)


# Simple session endpoint to prevent 404 errors
@app.get("/api/session")
async def get_session():
    """
    Simple session endpoint
    Returns basic session info without authentication
    """
    return {
        "authenticated": False,
        "message": "Session authentication not implemented yet"
    }


# Global exception handlers
# Requirements: 12.6 - Catch unexpected exceptions and return appropriate error responses

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors (malformed requests)
    Requirements: 12.6
    """
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    
    error_response = create_error_response(
        code=ErrorCode.MALFORMED_REQUEST,
        details=str(exc.errors())
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unexpected errors
    Ensures service doesn't crash on unhandled exceptions
    Requirements: 12.6
    """
    from datetime import datetime
    
    timestamp = datetime.now().isoformat()
    logger.error(
        f"[{timestamp}] Unhandled exception on {request.method} {request.url}: "
        f"{type(exc).__name__}: {str(exc)}",
        exc_info=True  # Include stack trace in logs
    )
    
    # Create generic error response
    error_response = create_error_response(
        code=ErrorCode.PROCESSING_FAILED,
        details=f"{type(exc).__name__}: {str(exc)}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


# Get the absolute path to the ffmpeg.exe in the same directory as this script
current_dir = Path(__file__).parent
ffmpeg_path = "ffmpeg"

# Custom User-Agent string to mimic a browser request
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

@app.get("/download-audio/")
async def download_audio(url: str):
    mainstart = time.time()
    logger.info(f"Downloading audio from: {url}")

    try:
        # Step 1: Use yt-dlp to get video info and check audio format
        info_command = [
            "yt-dlp", "-j", "--skip-download", "--no-check-certificate", "--geo-bypass",
            "--user-agent", USER_AGENT, url  # Output metadata in JSON format, no SSL check, bypass region block
        ]
        logger.debug(f"Running command: {' '.join(info_command)}")
        result = subprocess.run(info_command, capture_output=True, text=True, check=True)

        # Parse the JSON output safely
        metadata = json.loads(result.stdout)  # Parse JSON string to Python dictionary

        ext = metadata.get("ext", "")  # Get the file extension (audio/video format)
        title = metadata.get("title", "audio_file")  # Extract the video title or set a default
        logger.info(f"File extension: {ext}")
        logger.info(f"Title: {title}")

        # Step 2: Handle audio download and conversion
        if ext == "mp3":
            # Directly download the MP3 file if it is already in MP3 format
            yt_dlp_command = [
                "yt-dlp",
                "--format", "bestaudio/best",  # Best available audio
                "--output", "-",  # Output to stdout (in memory)
                "--no-check-certificate",  # Disable certificate check
                "--geo-bypass",  # Bypass geo-blocks
                "--user-agent", USER_AGENT,  # Use the browser-like User-Agent
                url
            ]
            logger.info("Downloading MP3")
            result = subprocess.run(yt_dlp_command, capture_output=True, check=True)

            # Return the result as a streaming response with a dynamic filename
            logger.debug("Returning MP3 file as response.")
            return StreamingResponse(io.BytesIO(result.stdout), media_type="audio/mpeg",
                                     headers={"Content-Disposition": f"attachment; filename={title}.mp3"})

        elif ext in ["webm", "m4a", "flac", "ogg"]:
            # Handle known audio formats that yt-dlp can extract
            yt_dlp_command = [
                "yt-dlp",
                "--extract-audio",  # Extract audio only
                "--audio-format", "best",  # Let yt-dlp decide the best format
                "--output", "-",  # Output to stdout (in memory)
                "--no-check-certificate",  # Disable certificate check
                "--geo-bypass",  # Bypass geo-blocks
                "--user-agent", USER_AGENT,  # Use the browser-like User-Agent
                url
            ]
            logger.info(f"Downloading audio in format: {ext}")
            start_time = time.time()
            result = subprocess.run(yt_dlp_command, capture_output=True, check=True)
            end_time = time.time()

            elapsed_time = end_time - start_time
            logger.info(f"Download ran for {elapsed_time} seconds.")

            # Convert to MP3 if the format isn't MP3
            if ext != "mp3":
                ffmpeg_command = [
                    str(ffmpeg_path), '-i', 'pipe:0',  # Read from stdin
                    '-c:a', 'libmp3lame', '-b:a', '192k',  # Encode with MP3 codec, 192kbps
                    '-f', 'mp3', 'pipe:1'  # Write to stdout
                ]
                logger.info("Converting to MP3")
                start_time = time.time()
                try:
                    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as e:
                    logger.error("Error starting ffmpeg process")
                    raise e

                try:
                    mp3_data, stderr = ffmpeg_process.communicate(input=result.stdout)
                    if stderr:
                        logger.error(f"FFmpeg stderr: {stderr.decode()}")
                except Exception as e:
                    logger.error("Error during ffmpeg communicate")
                    raise e

                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.info(f"Conversion ran for {elapsed_time} seconds.")

                mainend = time.time()
                main_elapsed_time = mainend - mainstart
                logger.info(f"Total time: {main_elapsed_time} seconds.")

                # Return the MP3 data as a streaming response with a dynamic filename
                logger.debug(f"Returning converted MP3 as response.")
                return StreamingResponse(io.BytesIO(mp3_data), media_type="audio/mpeg",
                                         headers={"Content-Disposition": f"attachment; filename={title}.mp3"})

        else:
            error_message = f"Unsupported audio format: {ext}"
            logger.error(error_message)
            return {"error": error_message}

    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp subprocess error: {e.stderr}")
        return {"error": f"An error occurred: {e.stderr}"}
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {"error": str(e)}
