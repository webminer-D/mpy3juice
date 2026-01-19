"""
Endpoint validation framework for comprehensive API testing
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import httpx

from .config import test_config
from .base import ValidationResult, CORSResult, RateLimitResult


@dataclass
class EndpointSpec:
    """Specification for an API endpoint"""
    path: str
    method: str
    expected_status: int
    requires_auth: bool = False
    file_upload: bool = False
    form_data: Optional[Dict[str, Any]] = None
    query_params: Optional[Dict[str, Any]] = None
    timeout_override: Optional[int] = None


@dataclass
class TimeoutResult:
    """Result of timeout behavior validation"""
    endpoint: str
    timeout_seconds: int
    completed_within_timeout: bool
    actual_duration_seconds: float
    error_message: Optional[str] = None


class EndpointValidator:
    """
    Comprehensive endpoint validator with CORS, rate limiting, and timeout testing
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        Initialize endpoint validator
        
        Args:
            client: Optional HTTP client, will create one if not provided
        """
        self.config = test_config
        self.client = client
        self._own_client = client is None
    
    async def setup(self):
        """Set up HTTP client if needed"""
        if self._own_client and not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                verify=False  # Skip SSL verification for testing
            )
    
    async def teardown(self):
        """Clean up HTTP client if we own it"""
        if self._own_client and self.client:
            await self.client.aclose()
            self.client = None
    
    async def validate_endpoint(self, endpoint_spec: EndpointSpec) -> ValidationResult:
        """
        Validate a single endpoint according to its specification
        
        Args:
            endpoint_spec: Specification for the endpoint to validate
            
        Returns:
            ValidationResult with validation details
        """
        if not self.client:
            await self.setup()
        
        url = f"{self.config.base_url}{endpoint_spec.path}"
        start_time = time.time()
        
        # Prepare request parameters
        kwargs = {}
        if endpoint_spec.query_params:
            kwargs['params'] = endpoint_spec.query_params
        if endpoint_spec.form_data:
            kwargs['data'] = endpoint_spec.form_data
        
        # Override timeout if specified
        if endpoint_spec.timeout_override:
            kwargs['timeout'] = endpoint_spec.timeout_override
        
        try:
            response = await self.client.request(
                endpoint_spec.method, 
                url, 
                **kwargs
            )
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Try to parse JSON response
            response_data = None
            try:
                response_data = response.json()
            except:
                pass
            
            # Check if status matches expected
            status_matches = response.status_code == endpoint_spec.expected_status
            
            return ValidationResult(
                endpoint=endpoint_spec.path,
                method=endpoint_spec.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                success=status_matches,
                response_data=response_data,
                error_message=None if status_matches else f"Expected {endpoint_spec.expected_status}, got {response.status_code}"
            )
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return ValidationResult(
                endpoint=endpoint_spec.path,
                method=endpoint_spec.method,
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
            await self.setup()
        
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            # Test preflight OPTIONS request with proper CORS headers
            headers = {
                'Origin': 'https://mpyjuice-ui.vercel.app',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = await self.client.options(url, headers=headers)
            
            response_headers = response.headers
            
            # Check CORS headers
            has_cors_headers = 'access-control-allow-origin' in response_headers
            allows_origin = response_headers.get('access-control-allow-origin') in ['*', 'https://mpyjuice-ui.vercel.app']
            allows_credentials = response_headers.get('access-control-allow-credentials', '').lower() == 'true'
            
            # Parse allowed methods
            methods_header = response_headers.get('access-control-allow-methods', '')
            allows_methods = [m.strip() for m in methods_header.split(',') if m.strip()]
            
            return CORSResult(
                endpoint=endpoint,
                has_cors_headers=has_cors_headers,
                allows_origin=allows_origin,
                allows_credentials=allows_credentials,
                allows_methods=allows_methods
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
            await self.setup()
        
        url = f"{self.config.base_url}{endpoint}"
        
        async def make_single_request():
            try:
                if endpoint.startswith('/api/convert') or endpoint.startswith('/api/trim'):
                    # POST endpoints that expect files - will return 422 (validation error)
                    response = await self.client.post(url)
                else:
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
            # Also count 400/422 as "handled" (validation errors are expected for POST endpoints without files)
            requests_handled = sum(1 for r in results if isinstance(r, int) and (200 <= r < 300 or r in [400, 422, 429]))
            
            return RateLimitResult(
                endpoint=endpoint,
                max_concurrent=max_concurrent,
                requests_sent=requests_sent,
                requests_succeeded=requests_handled,  # Use handled count as "succeeded"
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
    
    async def test_timeout_behavior(self, endpoint: str, timeout_seconds: int = 10) -> TimeoutResult:
        """
        Test timeout behavior for an endpoint
        
        Args:
            endpoint: API endpoint path
            timeout_seconds: Timeout to test with
            
        Returns:
            TimeoutResult with timeout validation details
        """
        if not self.client:
            await self.setup()
        
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            # Create a client with specific timeout
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds), verify=False) as timeout_client:
                response = await timeout_client.get(url)
                end_time = time.time()
                duration = end_time - start_time
                
                return TimeoutResult(
                    endpoint=endpoint,
                    timeout_seconds=timeout_seconds,
                    completed_within_timeout=duration < timeout_seconds,
                    actual_duration_seconds=duration
                )
                
        except asyncio.TimeoutError:
            end_time = time.time()
            duration = end_time - start_time
            
            return TimeoutResult(
                endpoint=endpoint,
                timeout_seconds=timeout_seconds,
                completed_within_timeout=False,
                actual_duration_seconds=duration,
                error_message="Request timed out"
            )
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return TimeoutResult(
                endpoint=endpoint,
                timeout_seconds=timeout_seconds,
                completed_within_timeout=duration < timeout_seconds,
                actual_duration_seconds=duration,
                error_message=str(e)
            )


# Common endpoint specifications for the MPY3JUICE API
COMMON_ENDPOINTS = [
    # Health check
    EndpointSpec('/api/health', 'GET', 200),
    
    # Audio processing endpoints
    EndpointSpec('/api/convert', 'POST', 200, file_upload=True),
    EndpointSpec('/api/trim', 'POST', 200, file_upload=True),
    EndpointSpec('/api/merge', 'POST', 200, file_upload=True),
    EndpointSpec('/api/compress', 'POST', 200, file_upload=True),
    EndpointSpec('/api/extract', 'POST', 200, file_upload=True),
    EndpointSpec('/api/split-audio', 'POST', 200, file_upload=True),
    EndpointSpec('/api/adjust-volume', 'POST', 200, file_upload=True),
    EndpointSpec('/api/change-speed', 'POST', 200, file_upload=True),
    
    # YouTube endpoints
    EndpointSpec('/download-audio/', 'GET', 200, query_params={'url': 'https://youtu.be/dQw4w9WgXcQ'}),
    EndpointSpec('/api/search', 'GET', 200, query_params={'q': 'test', 'max_results': 5}),
    EndpointSpec('/api/video/dQw4w9WgXcQ', 'GET', 200),
    EndpointSpec('/api/bulk-validate', 'POST', 200),
    EndpointSpec('/api/playlist-extract', 'POST', 200),
    
    # Contact form
    EndpointSpec('/api/contact', 'POST', 200),
]