# Audio Toolkit Infrastructure

This directory contains the core infrastructure for the audio processing toolkit.

## Components

### 1. Router (`router.py`)
- API router with `/api` prefix
- Endpoints for all audio processing tools:
  - `GET /api/health` - Health check and FFmpeg availability
  - `POST /api/convert` - Audio format conversion
  - `POST /api/trim` - Audio trimming
  - `POST /api/merge` - Audio file merging
  - `POST /api/compress` - Audio compression
  - `POST /api/extract` - Audio extraction from video

### 2. Input Validator (`validators.py`)
- File type validation (audio and video formats)
- File size validation (100MB limit)
- File signature verification (magic numbers)
- Filename sanitization (path traversal prevention)
- Time range validation for trimming
- Timestamp parsing (MM:SS and seconds formats)
- File count validation for merging

### 3. FFmpeg Wrapper (`ffmpeg_wrapper.py`)
- Base class for FFmpeg operations
- Subprocess management with error handling
- Timeout enforcement (5 minutes default)
- Logging of all operations
- Method stubs for:
  - Format conversion
  - Audio trimming
  - Audio merging
  - Audio compression
  - Audio extraction from video

## Requirements Addressed

- **9.1**: RESTful API endpoints for each audio processing tool
- **9.2**: FastAPI framework for request handling and routing
- **9.5**: Proper error handling and HTTP status codes
- **11.3**: CORS policies configured in main application
- **9.4**: FFmpeg wrapper for audio/video processing
- **9.6**: Logging for all processing operations
- **12.3**: FFmpeg error capture and logging
- **6.2**: File size validation (100MB limit)
- **11.1**: File type validation with signature checking
- **11.2**: Rejection of suspicious or malformed files
- **11.5**: Filename sanitization to prevent path traversal

## Testing

Run the infrastructure test:
```bash
python mpy3juice/test_infrastructure.py
```

This verifies:
- Router configuration and endpoint registration
- Validator setup and functionality
- FFmpeg wrapper initialization
- CORS middleware configuration
- Router integration into main app

## Next Steps

The infrastructure is now ready for implementation of specific audio processing features in subsequent tasks:
- Task 2: Input validation and security
- Task 3: FFmpeg wrapper and core processing
- Task 5: Audio trimming functionality
- Task 6: Audio merging functionality
- Task 7: Audio compression functionality
- Task 9: Video audio extraction functionality
