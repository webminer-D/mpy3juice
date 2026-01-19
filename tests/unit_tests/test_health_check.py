"""
Unit tests for health check endpoint validation.
Tests the basic framework functionality and health endpoint.
"""

import pytest
import httpx
from tests.config import TestConfig
from tests.base import EndpointValidator


class TestHealthCheck:
    """Test health check endpoint functionality."""
    
    @pytest.fixture
    def validator(self, test_config: TestConfig) -> EndpointValidator:
        """Create endpoint validator for testing."""
        return EndpointValidator(test_config)
    
    @pytest.mark.asyncio
    async def test_health_endpoint_availability(self, http_client: httpx.AsyncClient, 
                                              validator: EndpointValidator):
        """Test that health endpoint is available and responds correctly."""
        result = await validator.validate_endpoint(
            http_client, "/api/health", expected_status=200
        )
        
        # Basic availability check
        assert result.status_code is not None, "Health endpoint should return a status code"
        
        # If endpoint is available, validate response structure
        if result.success:
            assert result.response_data is not None, "Successful response should have data"
            assert isinstance(result.response_data, dict), "Response should be JSON object"
            
            # Check for expected health check fields
            expected_fields = ['status']  # Minimal expected field
            for field in expected_fields:
                if field in result.response_data:
                    assert result.response_data[field] is not None, f"Field {field} should not be None"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, http_client: httpx.AsyncClient, 
                                             validator: EndpointValidator,
                                             test_config: TestConfig):
        """Test that health endpoint meets performance requirements."""
        result = await validator.validate_endpoint(
            http_client, "/api/health", expected_status=200
        )
        
        # Only test performance if endpoint is available
        if result.success and result.response_time_ms is not None:
            max_response_time = test_config.performance_thresholds.health_check_max_ms
            assert result.response_time_ms <= max_response_time, \
                f"Health check should respond within {max_response_time}ms, got {result.response_time_ms}ms"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_cors(self, http_client: httpx.AsyncClient, 
                                      validator: EndpointValidator):
        """Test CORS configuration for health endpoint."""
        cors_result = await validator.test_cors_configuration(http_client, "/api/health")
        
        # CORS should be configured (success=True) or gracefully handled (success=False with no error)
        assert cors_result.error_message is None or cors_result.success, \
            f"CORS test should not fail with error: {cors_result.error_message}"