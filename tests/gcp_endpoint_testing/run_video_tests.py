#!/usr/bin/env python3
"""
Run video extraction tests for GCP endpoint testing.
"""

import sys
import asyncio
from pathlib import Path

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from test_video_extraction import run_video_extraction_tests


async def main():
    """Run video extraction tests."""
    try:
        results = await run_video_extraction_tests()
        
        # Check if any tests failed
        failed_tests = [name for name, result in results.items() if not result.success]
        
        if failed_tests:
            print(f"\nFailed tests: {failed_tests}")
            return 1
        else:
            print(f"\nAll tests passed!")
            return 0
            
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)