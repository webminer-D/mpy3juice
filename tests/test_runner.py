#!/usr/bin/env python3
"""
Test runner for GCP endpoint testing framework.
Demonstrates basic usage of the testing framework components.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config import TestConfig
from tests.controller import TestController


async def main():
    """Run basic framework validation tests."""
    print("=== GCP Endpoint Testing Framework ===")
    print("Initializing test configuration...")
    
    try:
        # Initialize configuration
        config = TestConfig()
        print(f"Base URL: {config.base_url}")
        print(f"Timeout: {config.timeout_seconds}s")
        print(f"Property tests enabled: {config.enable_property_tests}")
        print()
        
        # Initialize test controller
        print("Initializing test controller...")
        controller = TestController(config)
        
        # Run basic connectivity tests
        print("Running basic connectivity tests...")
        results = await controller.run_all_tests()
        
        # Generate and display report
        print("\n" + controller.generate_report())
        
        # Return exit code based on results
        if results.failed_tests > 0:
            print(f"\n❌ {results.failed_tests} tests failed")
            return 1
        else:
            print(f"\n✅ All {results.passed_tests} tests passed")
            return 0
            
    except Exception as e:
        print(f"❌ Framework initialization failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)