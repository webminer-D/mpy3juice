# GCP Endpoint Testing Framework

This directory contains a comprehensive testing framework for validating all API endpoints in the MPY3JUICE backend deployed to Google Cloud Platform via CloudFlare tunnel.

## Framework Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── config.py                   # Test configuration management
├── base.py                     # Base test classes and utilities
├── controller.py               # Test orchestration and result aggregation
├── demo.py                     # Framework demonstration script
├── test_runner.py              # Basic test runner
├── README.md                   # This documentation
│
├── utils/                      # Test utilities
│   ├── __init__.py
│   ├── audio_generator.py      # Audio file generation for testing
│   └── youtube_helper.py       # YouTube URL testing utilities
│
├── unit_tests/                 # Unit tests for individual components
│   ├── __init__.py
│   ├── test_framework.py       # Framework component tests
│   └── test_health_check.py    # Health endpoint tests
│
├── integration_tests/          # End-to-end functionality tests
│   └── __init__.py
│
├── property_tests/             # Property-based tests using Hypothesis
│   └── __init__.py
│
├── performance_tests/          # Performance and load tests
│   └── __init__.py
│
└── security_tests/             # Security and CORS validation tests
    └── __init__.py
```

## Configuration

The framework uses environment variables for configuration:

- `GCP_TEST_URL`: Base URL for the GCP deployment (default: CloudFlare tunnel URL)
- `TEST_TIMEOUT`: HTTP request timeout in seconds (default: 30)
- `MAX_CONCURRENT`: Maximum concurrent requests (default: 5)
- `ENABLE_PBT`: Enable property-based tests (default: true)
- `PBT_ITERATIONS`: Property-based test iterations (default: 100)
- `RATE_LIMIT_MAX`: Rate limiting threshold (default: 10)
- `MAX_FILE_SIZE_MB`: Maximum file size for uploads (default: 100)

## Dependencies

The framework requires the following Python packages:

```
pytest==7.4.3          # Test framework
pytest-asyncio==0.21.1 # Async test support
hypothesis==6.88.1     # Property-based testing
httpx==0.25.2          # HTTP client for API testing
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run framework demonstration:**
   ```bash
   python tests/demo.py
   ```

3. **Run basic connectivity tests:**
   ```bash
   python tests/test_runner.py
   ```

4. **Run framework unit tests:**
   ```bash
   pytest tests/unit_tests/test_framework.py -v
   ```

## Key Components

### TestConfig
Manages configuration for GCP deployment URL, timeouts, and test parameters. Supports environment variable overrides and validation.

### EndpointValidator
Provides comprehensive endpoint validation including:
- HTTP status code validation
- Response time measurement
- CORS header validation
- Rate limiting testing
- Timeout behavior testing

### AudioFileGenerator
Creates test audio files for comprehensive testing:
- Valid audio in multiple formats (WAV, MP3, etc.)
- Invalid/corrupted audio files
- Large files for size limit testing
- Edge cases (zero duration, mono/stereo, etc.)

### YouTubeTestHelper
Provides utilities for YouTube-related testing:
- Valid and invalid YouTube URLs
- Video ID extraction
- Playlist URL handling
- Bulk operation test data

### TestController
Orchestrates test execution across different categories:
- Health check validation
- Security and CORS testing
- Performance validation
- Result aggregation and reporting

## Test Categories

### Unit Tests
- Framework component validation
- Configuration testing
- Utility function testing

### Integration Tests
- End-to-end API functionality
- Frontend-backend communication
- File upload/download workflows

### Property-Based Tests
- Universal properties using Hypothesis
- Comprehensive input coverage
- Automatic test case generation

### Performance Tests
- Response time validation
- Throughput measurement
- Timeout enforcement

### Security Tests
- CORS configuration validation
- Rate limiting enforcement
- Input validation testing

## Usage Examples

### Basic Endpoint Testing
```python
from tests.config import TestConfig
from tests.base import EndpointValidator
import httpx

config = TestConfig()
validator = EndpointValidator(config)

async with httpx.AsyncClient(base_url=config.base_url) as client:
    result = await validator.validate_endpoint(client, "/api/health")
    print(f"Health check: {result.success}")
```

### Audio File Generation
```python
from tests.utils.audio_generator import AudioFileGenerator
import tempfile

with tempfile.TemporaryDirectory() as temp_dir:
    generator = AudioFileGenerator(temp_dir)
    audio_data = generator.generate_valid_audio(format='wav', duration=5)
    test_files = generator.create_test_audio_set()
```

### YouTube URL Testing
```python
from tests.utils.youtube_helper import YouTubeTestHelper

helper = YouTubeTestHelper()
valid_urls = helper.get_valid_test_urls()
is_valid = helper.is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ")
video_id = helper.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
```

## Test Execution

### Run All Framework Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
pytest tests/unit_tests/ -v           # Unit tests only
pytest tests/integration_tests/ -v    # Integration tests only
pytest tests/property_tests/ -v       # Property-based tests only
pytest tests/performance_tests/ -v    # Performance tests only
pytest tests/security_tests/ -v       # Security tests only
```

### Run with Markers
```bash
pytest -m "property" -v               # Property-based tests
pytest -m "integration" -v            # Integration tests
pytest -m "performance" -v            # Performance tests
pytest -m "security" -v               # Security tests
```

## Framework Validation Results

The framework has been validated against the GCP deployment:

✅ **Configuration Management**: Environment-based configuration working  
✅ **Test Data Generation**: Audio and URL generation functional  
✅ **HTTP Client Validation**: Successfully connecting to GCP deployment  
✅ **Performance Measurement**: Response time tracking operational  
✅ **CORS Validation**: CORS header detection working  
✅ **Health Endpoint**: Successfully validated health check endpoint  
✅ **FFmpeg Detection**: Confirmed FFmpeg availability in deployment  

## Next Steps

This framework provides the foundation for implementing the remaining tasks in the GCP endpoint testing specification:

1. **Audio Processing Tests** (Tasks 3-6)
2. **YouTube Integration Tests** (Task 9)
3. **Error Handling Tests** (Task 11)
4. **Performance Testing** (Task 12)
5. **Integration Testing** (Task 14)

Each subsequent task will build upon this framework foundation to create comprehensive endpoint validation.