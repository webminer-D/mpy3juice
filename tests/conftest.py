"""
Pytest configuration and shared fixtures for GCP endpoint testing.
Provides common test setup, configuration, and utilities.
"""

import pytest
import asyncio
import httpx
from typing import AsyncGenerator, Dict, Any
from pathlib import Path
import tempfile
import os

from tests.config import TestConfig
from tests.utils.audio_generator import AudioFileGenerator
from tests.utils.youtube_helper import YouTubeTestHelper


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Load test configuration from environment or defaults."""
    return TestConfig()


@pytest.fixture
async def http_client(test_config: TestConfig) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create HTTP client for API testing."""
    async with httpx.AsyncClient(
        base_url=test_config.base_url,
        timeout=test_config.timeout_seconds,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="session")
def temp_dir() -> str:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="session")
def audio_generator(temp_dir: str) -> AudioFileGenerator:
    """Create audio file generator for test data."""
    return AudioFileGenerator(temp_dir)


@pytest.fixture(scope="session")
def youtube_helper() -> YouTubeTestHelper:
    """Create YouTube test helper for URL testing."""
    return YouTubeTestHelper()


@pytest.fixture
async def clean_temp_files(temp_dir: str):
    """Clean up temporary files after each test."""
    yield
    # Clean up any files created during the test
    for file_path in Path(temp_dir).glob("*"):
        if file_path.is_file():
            try:
                file_path.unlink()
            except OSError:
                pass  # File might be in use, ignore


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "property: mark test as a property-based test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "property_tests" in str(item.fspath):
            item.add_marker(pytest.mark.property)
        elif "integration_tests" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance_tests" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security_tests" in str(item.fspath):
            item.add_marker(pytest.mark.security)