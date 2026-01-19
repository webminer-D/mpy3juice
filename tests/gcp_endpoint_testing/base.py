"""
Base test classes and utilities for GCP endpoint testing
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

import httpx
import pytest

from config import test_config


@dataclass
class ValidationResult:
    """Result of endpoint validation"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


@dataclass
class CORSResult:
    """Result of CORS validation"""
    endpoint: str
    has_cors_headers: bool
    allows_origin: bool
    allows_credentials: bool
    allows_methods: List[str]
    error_message: Optional[str] = None


@dataclass
class RateLimitResult:
    """Result of rate limiting validation"""
    endpoint: str
    max_concurrent: int
    requests_sent: int
    requests_succeeded: int
    requests_rate_limited: int
    error_message: Optional[str] = None


class BaseEndpointTest:
    """Base class for endpoint testing with common utilities"""
    
    def __init__(self):
        self.config = test_config
        self.client = None
    
    async def setup_client(self):
        """Set up HTTP client for testing"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout_seconds),
            verify=False  # Skip SSL verification for testing
        )
    
    async def teardown_client(self):
        """Clean up HTTP client"""
        if self.client:
            await self.client.aclose()
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> ValidationResult:
        """
        Make HTTP request and return validation result
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request
            
        Returns:
            ValidationResult with response details
        """
        if not self.client:
            await self.setup_client()
        
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = await self.client.request(method, url, **kwargs)
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Try to parse JSON response
            response_data = None
            try:
                response_data = response.json()
            except:
                pass
            
            return ValidationResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                success=200 <= response.status_code < 300,
                response_data=response_data
            )
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return ValidationResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def test_cors_headers(self, endpoint: str) -> CORSResult:
        """
        Test CORS headers for an endpoint
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            CORSResult with CORS validation details
        """
        if not self.client:
            await self.setup_client()
        
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            # Test preflight OPTIONS request
            response = await self.client.options(url)
            
            headers = response.headers
            
            return CORSResult(
                endpoint=endpoint,
                has_cors_headers='access-control-allow-origin' in headers,
                allows_origin=headers.get('access-control-allow-origin') == '*',
                allows_credentials=headers.get('access-control-allow-credentials') == 'true',
                allows_methods=headers.get('access-control-allow-methods', '').split(', ')
            )
            
        except Exception as e:
            return CORSResult(
                endpoint=endpoint,
                has_cors_headers=False,
                allows_origin=False,
                allows_credentials=False,
                allows_methods=[],
                error_message=str(e)
            )
    
    async def test_rate_limiting(self, endpoint: str, max_concurrent: int = 15) -> RateLimitResult:
        """
        Test rate limiting by sending concurrent requests
        
        Args:
            endpoint: API endpoint path
            max_concurrent: Number of concurrent requests to send
            
        Returns:
            RateLimitResult with rate limiting validation details
        """
        if not self.client:
            await self.setup_client()
        
        url = f"{self.config.base_url}{endpoint}"
        
        async def make_single_request():
            try:
                response = await self.client.get(url)
                return response.status_code
            except Exception:
                return 0
        
        try:
            # Send concurrent requests
            tasks = [make_single_request() for _ in range(max_concurrent)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            requests_sent = len(results)
            requests_succeeded = sum(1 for r in results if isinstance(r, int) and 200 <= r < 300)
            requests_rate_limited = sum(1 for r in results if isinstance(r, int) and r == 429)
            
            return RateLimitResult(
                endpoint=endpoint,
                max_concurrent=max_concurrent,
                requests_sent=requests_sent,
                requests_succeeded=requests_succeeded,
                requests_rate_limited=requests_rate_limited
            )
            
        except Exception as e:
            return RateLimitResult(
                endpoint=endpoint,
                max_concurrent=max_concurrent,
                requests_sent=0,
                requests_succeeded=0,
                requests_rate_limited=0,
                error_message=str(e)
            )


class PropertyTestBase:
    """Base class for property-based tests using Hypothesis"""
    
    def __init__(self):
        self.config = test_config
        self.iterations = self.config.property_test_iterations
    
    def log_property_test(self, property_name: str, feature: str = "gcp-endpoint-testing"):
        """Log property test execution with standard format"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] **Feature: {feature}, Property: {property_name}**")


@pytest.fixture
async def endpoint_client():
    """Pytest fixture for HTTP client"""
    test = BaseEndpointTest()
    await test.setup_client()
    yield test.client
    await test.teardown_client()


@pytest.fixture
def base_test():
    """Pytest fixture for base test instance"""
    return BaseEndpointTest()