"""
Debug rate limiting behavior
"""

import pytest
import httpx
import asyncio

from .config import test_config


@pytest.mark.asyncio
async def test_rate_limit_debug():
    """Debug rate limiting behavior"""
    
    async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
        base_url = test_config.base_url
        
        print(f"\n🔍 Debugging rate limiting on {base_url}")
        
        # Test concurrent requests to health endpoint
        print("\n1. Testing 5 concurrent requests to /api/health")
        async def make_health_request():
            try:
                response = await client.get(f"{base_url}/api/health")
                return response.status_code
            except Exception as e:
                return f"Error: {str(e)[:50]}"
        
        tasks = [make_health_request() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"   Results: {results}")
        
        success_count = sum(1 for r in results if r == 200)
        error_count = sum(1 for r in results if isinstance(r, str))
        other_count = sum(1 for r in results if isinstance(r, int) and r != 200)
        
        print(f"   Success (200): {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Other status: {other_count}")
        
        # Test concurrent requests to convert endpoint
        print("\n2. Testing 5 concurrent POST requests to /api/convert")
        async def make_convert_request():
            try:
                response = await client.post(f"{base_url}/api/convert")
                return response.status_code
            except Exception as e:
                return f"Error: {str(e)[:50]}"
        
        tasks = [make_convert_request() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"   Results: {results}")
        
        success_count = sum(1 for r in results if isinstance(r, int) and 200 <= r < 300)
        validation_errors = sum(1 for r in results if isinstance(r, int) and r in [400, 422])
        rate_limited = sum(1 for r in results if isinstance(r, int) and r == 429)
        error_count = sum(1 for r in results if isinstance(r, str))
        
        print(f"   Success (2xx): {success_count}")
        print(f"   Validation errors (400/422): {validation_errors}")
        print(f"   Rate limited (429): {rate_limited}")
        print(f"   Network errors: {error_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])