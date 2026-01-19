"""
Test configuration management for GCP deployment URL and test parameters.
Handles environment-specific settings and test thresholds.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PerformanceThresholds:
    """Performance thresholds for endpoint validation."""
    health_check_max_ms: int = 100
    file_upload_max_seconds: int = 30
    processing_max_seconds: int = 300
    download_max_seconds: int = 60
    search_max_seconds: int = 10


@dataclass
class TestConfig:
    """Configuration for GCP endpoint testing."""
    
    # GCP deployment URL - can be overridden via environment variable
    base_url: str = field(default_factory=lambda: os.getenv(
        "GCP_TEST_URL", 
        "https://command-arthur-hockey-calculations.trycloudflare.com"
    ))
    
    # HTTP client configuration
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TEST_TIMEOUT", "30")))
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT", "5")))
    
    # Test data configuration
    test_data_path: str = field(default_factory=lambda: os.getenv("TEST_DATA_PATH", "test_data/"))
    
    # Property-based testing configuration
    enable_property_tests: bool = field(default_factory=lambda: os.getenv("ENABLE_PBT", "true").lower() == "true")
    property_test_iterations: int = field(default_factory=lambda: int(os.getenv("PBT_ITERATIONS", "100")))
    
    # Performance thresholds
    performance_thresholds: PerformanceThresholds = field(default_factory=PerformanceThresholds)
    
    # Rate limiting configuration
    rate_limit_max_requests: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_MAX", "10")))
    
    # File size limits (in bytes)
    max_file_size_mb: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "100")))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Calculate max_file_size_bytes after initialization
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
        
        # Bulk operation limits
        self.max_merge_files = int(os.getenv("MAX_MERGE_FILES", "10"))
        self.max_bulk_urls = int(os.getenv("MAX_BULK_URLS", "50"))
        
        if not self.base_url:
            raise ValueError("Base URL must be provided")
        
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Base URL must include protocol (http:// or https://)")
        
        # Ensure base URL doesn't end with slash
        self.base_url = self.base_url.rstrip("/")
    
    @property
    def health_endpoint(self) -> str:
        """Get health check endpoint URL."""
        return f"{self.base_url}/api/health"
    
    @property
    def api_base(self) -> str:
        """Get API base URL."""
        return f"{self.base_url}/api"