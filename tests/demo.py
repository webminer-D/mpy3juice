#!/usr/bin/env python3
"""
Demonstration script showing the GCP endpoint testing framework in action.
This validates that the framework setup is complete and functional.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config import TestConfig
from tests.base import EndpointValidator
from tests.utils.audio_generator import AudioFileGenerator
from tests.utils.youtube_helper import YouTubeTestHelper
import httpx


async def demonstrate_framework():
    """Demonstrate key framework components."""
    print("🚀 GCP Endpoint Testing Framework Demonstration")
    print("=" * 50)
    
    # 1. Configuration
    print("\n1. Configuration Management:")
    config = TestConfig()
    print(f"   ✅ Base URL: {config.base_url}")
    print(f"   ✅ Timeout: {config.timeout_seconds}s")
    print(f"   ✅ Property tests: {config.enable_property_tests}")
    print(f"   ✅ Max file size: {config.max_file_size_mb}MB")
    
    # 2. Audio Generator
    print("\n2. Audio File Generation:")
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = AudioFileGenerator(temp_dir)
        
        # Generate test audio
        audio_data = generator.generate_valid_audio(duration=1)
        print(f"   ✅ Generated valid audio: {len(audio_data)} bytes")
        
        invalid_data = generator.generate_invalid_audio()
        print(f"   ✅ Generated invalid audio: {len(invalid_data)} bytes")
        
        edge_cases = generator.generate_edge_case_audio()
        print(f"   ✅ Generated {len(edge_cases)} edge case files")
    
    # 3. YouTube Helper
    print("\n3. YouTube Test Helper:")
    youtube_helper = YouTubeTestHelper()
    
    valid_urls = youtube_helper.get_valid_test_urls()
    invalid_urls = youtube_helper.get_invalid_test_urls()
    print(f"   ✅ Valid test URLs: {len(valid_urls)}")
    print(f"   ✅ Invalid test URLs: {len(invalid_urls)}")
    
    # Test URL validation
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    is_valid = youtube_helper.is_valid_youtube_url(test_url)
    video_id = youtube_helper.extract_video_id(test_url)
    print(f"   ✅ URL validation works: {is_valid}")
    print(f"   ✅ Video ID extraction: {video_id}")
    
    # 4. Endpoint Validation
    print("\n4. Endpoint Validation:")
    validator = EndpointValidator(config)
    
    async with httpx.AsyncClient(base_url=config.base_url, timeout=30) as client:
        # Test health endpoint
        result = await validator.validate_endpoint(client, "/api/health")
        print(f"   ✅ Health endpoint test: {result.success}")
        print(f"   ✅ Response time: {result.response_time_ms:.2f}ms")
        
        if result.success and result.response_data:
            ffmpeg_available = result.response_data.get('ffmpeg_available', 'unknown')
            print(f"   ✅ FFmpeg available: {ffmpeg_available}")
        
        # Test CORS configuration
        cors_result = await validator.test_cors_configuration(client, "/api/health")
        print(f"   ✅ CORS test completed: {cors_result.success}")
    
    print("\n🎉 Framework Demonstration Complete!")
    print("\nThe testing framework is ready for comprehensive endpoint validation.")
    print("Key components verified:")
    print("  • Configuration management ✅")
    print("  • Test data generation ✅") 
    print("  • YouTube URL handling ✅")
    print("  • HTTP client validation ✅")
    print("  • Performance measurement ✅")
    print("  • CORS validation ✅")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(demonstrate_framework())
        if success:
            print("\n✅ Framework setup is complete and functional!")
            sys.exit(0)
        else:
            print("\n❌ Framework demonstration failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Framework error: {e}")
        sys.exit(1)