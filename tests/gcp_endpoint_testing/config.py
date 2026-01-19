"""
Test configuration for GCP endpoint testing
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PerformanceThresholds:
    """Performance thresholds for endpoint validation"""
    health_check_max_ms: int = 2000  # Increased for GCP deployment + CloudFlare tunnel latency
    file_upload_max_seconds: int = 30
    processing_max_seconds: int = 300
    download_max_seconds: int = 60
    search_max_seconds: int = 10


@dataclass
class TestConfig:
    """Configuration for GCP endpoint testing"""
    base_url: str
    performance_thresholds: PerformanceThresholds
    timeout_seconds: int = 30
    max_concurrent_requests: int = 5
    test_data_path: str = "test_data/"
    enable_property_tests: bool = True
    property_test_iterations: int = 100
    
    @classmethod
    def from_environment(cls) -> 'TestConfig':
        """Create configuration from environment variables"""
        base_url = os.getenv(
            'GCP_BACKEND_URL', 
            'https://command-arthur-hockey-calculations.trycloudflare.com'
        )
        
        return cls(
            base_url=base_url,
            performance_thresholds=PerformanceThresholds(
                health_check_max_ms=int(os.getenv('HEALTH_CHECK_MAX_MS', '2000')),
                file_upload_max_seconds=int(os.getenv('FILE_UPLOAD_MAX_SECONDS', '30')),
                processing_max_seconds=int(os.getenv('PROCESSING_MAX_SECONDS', '300')),
                download_max_seconds=int(os.getenv('DOWNLOAD_MAX_SECONDS', '60')),
                search_max_seconds=int(os.getenv('SEARCH_MAX_SECONDS', '10'))
            ),
            timeout_seconds=int(os.getenv('TEST_TIMEOUT', '30')),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT', '5')),
            test_data_path=os.getenv('TEST_DATA_PATH', 'test_data/'),
            enable_property_tests=os.getenv('ENABLE_PROPERTY_TESTS', 'true').lower() == 'true',
            property_test_iterations=int(os.getenv('PROPERTY_TEST_ITERATIONS', '100'))
        )


# Global test configuration instance
test_config = TestConfig.from_environment()