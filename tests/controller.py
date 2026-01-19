"""
Test controller for orchestrating comprehensive endpoint testing.
Manages test execution, coordinates different test types, and aggregates results.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import httpx

from tests.config import TestConfig
from tests.base import EndpointValidator, ValidationResult, CORSResult, RateLimitResult


@dataclass
class TestResults:
    """Aggregated results from all test executions."""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    execution_time: float = 0.0
    health_results: Optional[Dict[str, Any]] = None
    audio_results: Optional[Dict[str, Any]] = None
    youtube_results: Optional[Dict[str, Any]] = None
    security_results: Optional[Dict[str, Any]] = None
    performance_results: Optional[Dict[str, Any]] = None
    property_results: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class HealthTestResults:
    """Results from health check endpoint testing."""
    endpoint_available: bool = False
    response_time_ms: float = 0.0
    status_code: Optional[int] = None
    ffmpeg_available: Optional[bool] = None
    version_info: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class AudioTestResults:
    """Results from audio processing endpoint testing."""
    conversion_tests: Dict[str, bool] = field(default_factory=dict)
    trimming_tests: Dict[str, bool] = field(default_factory=dict)
    merging_tests: Dict[str, bool] = field(default_factory=dict)
    compression_tests: Dict[str, bool] = field(default_factory=dict)
    extraction_tests: Dict[str, bool] = field(default_factory=dict)
    splitting_tests: Dict[str, bool] = field(default_factory=dict)
    volume_tests: Dict[str, bool] = field(default_factory=dict)
    speed_tests: Dict[str, bool] = field(default_factory=dict)


@dataclass
class YouTubeTestResults:
    """Results from YouTube integration testing."""
    download_tests: Dict[str, bool] = field(default_factory=dict)
    search_tests: Dict[str, bool] = field(default_factory=dict)
    bulk_tests: Dict[str, bool] = field(default_factory=dict)
    playlist_tests: Dict[str, bool] = field(default_factory=dict)


@dataclass
class SecurityTestResults:
    """Results from security and CORS testing."""
    cors_tests: Dict[str, CORSResult] = field(default_factory=dict)
    rate_limit_tests: Dict[str, RateLimitResult] = field(default_factory=dict)
    input_validation_tests: Dict[str, bool] = field(default_factory=dict)


@dataclass
class PerformanceTestResults:
    """Results from performance testing."""
    response_times: Dict[str, float] = field(default_factory=dict)
    throughput_tests: Dict[str, float] = field(default_factory=dict)
    timeout_tests: Dict[str, bool] = field(default_factory=dict)


class TestController:
    """Central orchestrator for managing test execution and result aggregation."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.validator = EndpointValidator(config)
        self.results = TestResults()
    
    async def run_all_tests(self) -> TestResults:
        """Run comprehensive test suite across all categories."""
        start_time = time.time()
        
        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds
        ) as client:
            
            # Run test categories in sequence
            self.results.health_results = await self.run_health_tests(client)
            self.results.security_results = await self.run_security_tests(client)
            self.results.performance_results = await self.run_performance_tests(client)
            
            # Audio and YouTube tests would be implemented in subsequent tasks
            # Placeholder for now
            self.results.audio_results = {"status": "not_implemented"}
            self.results.youtube_results = {"status": "not_implemented"}
            self.results.property_results = {"status": "not_implemented"}
        
        end_time = time.time()
        self.results.execution_time = end_time - start_time
        
        # Calculate summary statistics
        self._calculate_summary_stats()
        
        return self.results
    
    async def run_health_tests(self, client: httpx.AsyncClient) -> HealthTestResults:
        """Run health check endpoint validation."""
        health_results = HealthTestResults()
        
        try:
            # Test health endpoint
            result = await self.validator.validate_endpoint(
                client, "/api/health", expected_status=200
            )
            
            health_results.endpoint_available = result.success
            health_results.status_code = result.status_code
            health_results.response_time_ms = result.response_time_ms
            
            if result.success and result.response_data:
                health_results.ffmpeg_available = result.response_data.get('ffmpeg_available')
                health_results.version_info = result.response_data.get('version')
            else:
                health_results.error_message = result.error_message
                
        except Exception as e:
            health_results.error_message = str(e)
            self.results.errors.append(f"Health test error: {e}")
        
        return health_results
    
    async def run_security_tests(self, client: httpx.AsyncClient) -> SecurityTestResults:
        """Run security and CORS validation tests."""
        security_results = SecurityTestResults()
        
        # Test endpoints for CORS configuration
        test_endpoints = [
            "/api/health",
            "/api/convert",
            "/api/trim",
            "/api/merge",
            "/download-audio/",
            "/api/search"
        ]
        
        for endpoint in test_endpoints:
            try:
                # Test CORS headers
                cors_result = await self.validator.test_cors_configuration(client, endpoint)
                security_results.cors_tests[endpoint] = cors_result
                
                # Test rate limiting (skip health endpoint as per requirements)
                if endpoint != "/api/health":
                    rate_limit_result = await self.validator.test_rate_limiting(client, endpoint)
                    security_results.rate_limit_tests[endpoint] = rate_limit_result
                
            except Exception as e:
                self.results.errors.append(f"Security test error for {endpoint}: {e}")
        
        return security_results
    
    async def run_performance_tests(self, client: httpx.AsyncClient) -> PerformanceTestResults:
        """Run performance validation tests."""
        performance_results = PerformanceTestResults()
        
        # Test response times for key endpoints
        test_endpoints = {
            "/api/health": self.config.performance_thresholds.health_check_max_ms,
            "/api/search": self.config.performance_thresholds.search_max_seconds * 1000,
        }
        
        for endpoint, threshold_ms in test_endpoints.items():
            try:
                response_time = await self.validator.measure_response_time(
                    client, "GET", endpoint
                )
                performance_results.response_times[endpoint] = response_time
                
                # Check if within threshold
                within_threshold = response_time <= threshold_ms
                performance_results.timeout_tests[endpoint] = within_threshold
                
            except Exception as e:
                self.results.errors.append(f"Performance test error for {endpoint}: {e}")
        
        return performance_results
    
    def _calculate_summary_stats(self):
        """Calculate summary statistics from all test results."""
        # This is a simplified calculation - would be expanded as tests are implemented
        total_tests = 0
        passed_tests = 0
        
        # Count health tests
        if self.results.health_results:
            total_tests += 1
            if self.results.health_results.endpoint_available:
                passed_tests += 1
        
        # Count security tests
        if self.results.security_results:
            cors_tests = len(self.results.security_results.cors_tests)
            rate_limit_tests = len(self.results.security_results.rate_limit_tests)
            total_tests += cors_tests + rate_limit_tests
            
            passed_cors = sum(1 for result in self.results.security_results.cors_tests.values() 
                            if result.success)
            passed_rate_limit = sum(1 for result in self.results.security_results.rate_limit_tests.values() 
                                  if result.success)
            passed_tests += passed_cors + passed_rate_limit
        
        # Count performance tests
        if self.results.performance_results:
            perf_tests = len(self.results.performance_results.response_times)
            total_tests += perf_tests
            passed_perf = sum(1 for passed in self.results.performance_results.timeout_tests.values() 
                            if passed)
            passed_tests += passed_perf
        
        self.results.total_tests = total_tests
        self.results.passed_tests = passed_tests
        self.results.failed_tests = total_tests - passed_tests
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=== GCP Endpoint Testing Report ===")
        report.append(f"Total Tests: {self.results.total_tests}")
        report.append(f"Passed: {self.results.passed_tests}")
        report.append(f"Failed: {self.results.failed_tests}")
        report.append(f"Execution Time: {self.results.execution_time:.2f}s")
        report.append("")
        
        # Health test results
        if self.results.health_results:
            report.append("--- Health Check Results ---")
            health = self.results.health_results
            report.append(f"Endpoint Available: {health.endpoint_available}")
            report.append(f"Response Time: {health.response_time_ms:.2f}ms")
            report.append(f"FFmpeg Available: {health.ffmpeg_available}")
            if health.error_message:
                report.append(f"Error: {health.error_message}")
            report.append("")
        
        # Security test results
        if self.results.security_results:
            report.append("--- Security Test Results ---")
            security = self.results.security_results
            
            report.append("CORS Tests:")
            for endpoint, result in security.cors_tests.items():
                status = "PASS" if result.success else "FAIL"
                report.append(f"  {endpoint}: {status}")
            
            report.append("Rate Limiting Tests:")
            for endpoint, result in security.rate_limit_tests.items():
                status = "PASS" if result.success else "FAIL"
                report.append(f"  {endpoint}: {status}")
            report.append("")
        
        # Performance test results
        if self.results.performance_results:
            report.append("--- Performance Test Results ---")
            perf = self.results.performance_results
            
            for endpoint, response_time in perf.response_times.items():
                within_threshold = perf.timeout_tests.get(endpoint, False)
                status = "PASS" if within_threshold else "FAIL"
                report.append(f"  {endpoint}: {response_time:.2f}ms ({status})")
            report.append("")
        
        # Errors
        if self.results.errors:
            report.append("--- Errors ---")
            for error in self.results.errors:
                report.append(f"  {error}")
        
        return "\n".join(report)