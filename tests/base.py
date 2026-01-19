"""
Base test classes and utilities for common testing patterns.
Provides shared functionality for endpoint validation and test execution.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
import httpx
import pytest

from tests.config import TestConfig


@dataclass
class ValidationResult:
    """Result of endpoint validation."""
    success: bool
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class CORSResult:
    """Result of CORS validation."""
    success: bool
    has_cors_headers: bool = False
    allowed_origins: Optional[str] = None
    allowed_methods: Optional[str] = None
    allowed_headers: Optional[str] = None
    allows_credentials: bool = False
    error_message: Optional[str] = None


@dataclass
class RateLimitResult:
    """Result of rate limiting validation."""
    success: bool
    limit_enforced: bool = False
    requests_sent: int = 0
    successful_requests: int = 0
    rate_limited_requests: int = 0
    error_message: Optional[str] = None


@dataclass
class TimeoutResult:
    """Result of timeout behavior validation."""
    success: bool
    timeout_enforced: bool = False
    actual_timeout_seconds: Optional[float] = None
    expected_timeout_seconds: float = 300.0
    error_message: Optional[str] = None


class BaseTestCase(ABC):
    """Base class for all test cases with common functionality."""
    
    def __init__(self, config: TestConfig):
        self.config = config
    
    async def measure_response_time(self, client: httpx.AsyncClient, method: str, 
                                  url: str, **kwargs) -> float:
        """Measure response time for an HTTP request."""
        start_time = time.time()
        try:
            response = await client.request(method, url, **kwargs)
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception:
            end_time = time.time()
            return (end_time - start_time) * 1000
    
    async def validate_cors_headers(self, response: httpx.Response) -> CORSResult:
        """Validate CORS headers in response."""
        headers = response.headers
        
        cors_headers = {
            'access-control-allow-origin': headers.get('access-control-allow-origin'),
            'access-control-allow-methods': headers.get('access-control-allow-methods'),
            'access-control-allow-headers': headers.get('access-control-allow-headers'),
            'access-control-allow-credentials': headers.get('access-control-allow-credentials')
        }
        
        has_cors = any(value is not None for value in cors_headers.values())
        
        return CORSResult(
            success=has_cors,
            has_cors_headers=has_cors,
            allowed_origins=cors_headers['access-control-allow-origin'],
            allowed_methods=cors_headers['access-control-allow-methods'],
            allowed_headers=cors_headers['access-control-allow-headers'],
            allows_credentials=cors_headers['access-control-allow-credentials'] == 'true'
        )
    
    async def test_rate_limiting(self, client: httpx.AsyncClient, 
                               endpoint: str) -> RateLimitResult:
        """Test rate limiting enforcement on an endpoint."""
        concurrent_requests = self.config.rate_limit_max_requests + 5
        
        async def make_request():
            try:
                response = await client.get(endpoint)
                return response.status_code
            except Exception as e:
                return str(e)
        
        # Send concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_requests = sum(1 for r in results if isinstance(r, int) and r < 400)
        rate_limited_requests = sum(1 for r in results if isinstance(r, int) and r == 429)
        
        limit_enforced = rate_limited_requests > 0
        
        return RateLimitResult(
            success=True,
            limit_enforced=limit_enforced,
            requests_sent=concurrent_requests,
            successful_requests=successful_requests,
            rate_limited_requests=rate_limited_requests
        )


class EndpointValidator(BaseTestCase):
    """Validates individual API endpoints with comprehensive test scenarios."""
    
    def __init__(self, config: TestConfig):
        super().__init__(config)
    
    async def validate_endpoint(self, client: httpx.AsyncClient, 
                              endpoint: str, method: str = "GET",
                              expected_status: int = 200,
                              **kwargs) -> ValidationResult:
        """Validate an endpoint with comprehensive checks."""
        try:
            start_time = time.time()
            response = await client.request(method, endpoint, **kwargs)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except Exception:
                response_data = {"raw_content": response.text[:500]}  # Truncate for safety
            
            success = response.status_code == expected_status
            
            return ValidationResult(
                success=success,
                status_code=response.status_code,
                response_data=response_data,
                response_time_ms=response_time_ms,
                headers=dict(response.headers),
                error_message=None if success else f"Expected {expected_status}, got {response.status_code}"
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                error_message=str(e)
            )
    
    async def test_cors_configuration(self, client: httpx.AsyncClient, 
                                    endpoint: str) -> CORSResult:
        """Test CORS configuration for an endpoint."""
        try:
            # Test preflight request
            preflight_response = await client.options(endpoint)
            cors_result = await self.validate_cors_headers(preflight_response)
            
            if not cors_result.success:
                # Try regular request to check CORS headers
                regular_response = await client.get(endpoint)
                cors_result = await self.validate_cors_headers(regular_response)
            
            return cors_result
            
        except Exception as e:
            return CORSResult(
                success=False,
                error_message=str(e)
            )
    
    async def test_timeout_behavior(self, client: httpx.AsyncClient, 
                                  endpoint: str) -> TimeoutResult:
        """Test timeout behavior for an endpoint."""
        # This is a placeholder - actual timeout testing would require
        # endpoints that can be made to run longer than the timeout
        try:
            start_time = time.time()
            response = await client.get(endpoint, timeout=1.0)  # Short timeout for testing
            end_time = time.time()
            
            actual_time = end_time - start_time
            
            return TimeoutResult(
                success=True,
                timeout_enforced=False,  # No timeout occurred
                actual_timeout_seconds=actual_time
            )
            
        except httpx.TimeoutException:
            end_time = time.time()
            actual_time = end_time - start_time
            
            return TimeoutResult(
                success=True,
                timeout_enforced=True,
                actual_timeout_seconds=actual_time
            )
        except Exception as e:
            return TimeoutResult(
                success=False,
                error_message=str(e)
            )


class PropertyTestBase(BaseTestCase):
    """Base class for property-based tests using Hypothesis."""
    
    def __init__(self, config: TestConfig):
        super().__init__(config)
        self.iterations = config.property_test_iterations if config.enable_property_tests else 10
    
    @abstractmethod
    def property_name(self) -> str:
        """Return the name of the property being tested."""
        pass
    
    @abstractmethod
    def requirements_validated(self) -> List[str]:
        """Return list of requirements this property validates."""
        pass
    
    def format_property_test_name(self) -> str:
        """Format property test name according to specification."""
        return f"Feature: gcp-endpoint-testing, Property {self.property_name()}"