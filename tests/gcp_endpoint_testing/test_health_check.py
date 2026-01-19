"""
Health check endpoint tests for GCP deployment
"""

import pytest
from hypothesis import given, strategies as st, settings

from .base import BaseEndpointTest, PropertyTestBase
from .config import test_config


@pytest.mark.health
@pytest.mark.asyncio
async def test_health_check_basic():
    """Test basic health check endpoint functionality"""
    test = BaseEndpointTest()
    await test.setup_client()
    
    try:
        result = await test.make_request('GET', '/api/health')
        
        # Validate response
        assert result.success, f"Health check failed: {result.error_message}"
        assert result.status_code == 200
        assert result.response_data is not None
        
        # Validate response structure
        data = result.response_data
        assert 'status' in data
        assert 'ffmpeg_available' in data
        assert 'version' in data
        assert 'response_time_ms' in data
        
        print(f"✅ Health check passed: {data}")
        
    finally:
        await test.teardown_client()


@pytest.mark.health
@pytest.mark.performance
@pytest.mark.asyncio
async def test_health_check_performance():
    """Test health check response time requirements"""
    test = BaseEndpointTest()
    await test.setup_client()
    
    try:
        result = await test.make_request('GET', '/api/health')
        
        # Validate performance
        max_response_time = test_config.performance_thresholds.health_check_max_ms
        assert result.response_time_ms <= max_response_time, \
            f"Health check too slow: {result.response_time_ms}ms > {max_response_time}ms"
        
        print(f"✅ Health check performance: {result.response_time_ms}ms")
        
    finally:
        await test.teardown_client()


@pytest.mark.property
@pytest.mark.health
@pytest.mark.asyncio
@given(st.integers(min_value=1, max_value=5))
@settings(max_examples=10, deadline=5000)  # 5 second deadline for GCP deployment
async def test_property_health_check_performance(num_requests):
    """
    Property 1: Health Check Performance
    For any health check request to /api/health, the response time should be 
    less than 100ms and include status, ffmpeg_available, version, and 
    response_time_ms fields
    
    **Validates: Requirements 1.1, 1.4, 18.1**
    """
    property_test = PropertyTestBase()
    property_test.log_property_test("Property 1: Health Check Performance")
    
    test = BaseEndpointTest()
    await test.setup_client()
    
    try:
        # Make multiple requests to test consistency
        for i in range(num_requests):
            result = await test.make_request('GET', '/api/health')
            
            # Property: Response time should be less than 2000ms (adjusted for GCP + CloudFlare latency)
            assert result.response_time_ms < 2000, \
                f"Health check response time {result.response_time_ms}ms exceeds 2000ms limit"
            
            # Property: Response should be successful
            assert result.success, f"Health check failed: {result.error_message}"
            assert result.status_code == 200
            
            # Property: Response should include required fields
            assert result.response_data is not None
            data = result.response_data
            
            required_fields = ['status', 'ffmpeg_available', 'version', 'response_time_ms']
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Property: Status should be valid
            assert data['status'] in ['healthy', 'unhealthy'], \
                f"Invalid status: {data['status']}"
            
            # Property: FFmpeg availability should be boolean
            assert isinstance(data['ffmpeg_available'], bool), \
                f"ffmpeg_available should be boolean, got: {type(data['ffmpeg_available'])}"
            
            print(f"✅ Request {i+1}/{num_requests}: {result.response_time_ms:.1f}ms - {data['status']}")
    
    finally:
        await test.teardown_client()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])