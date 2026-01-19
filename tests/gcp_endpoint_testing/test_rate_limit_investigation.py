"""
Investigation of rate limiting behavior
"""

import pytest
import httpx
import asyncio

from .config import test_config


@pytest.mark.asyncio
async def test_rate_limit_investigation():
    """Investigate rate limiting behavior"""
    
    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        base_url = test_config.base_url
        
        print(f"\n🔍 Investigating rate limiting on {base_url}")
        
        # Test single request to search endpoint
        print("\n1. Testing single GET /api/search?q=test")
        try:
            response = await client.get(f"{base_url}/api/search?q=test&max_results=5")
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text[:200]}")
            else:
                print("   ✅ Search endpoint working")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test health endpoint for comparison
        print("\n2. Testing single GET /api/health")
        try:
            response = await client.get(f"{base_url}/api/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test concurrent requests to health endpoint (should not be rate limited)
        print("\n3. Testing 5 concurrent requests to /api/health")
        async def make_health_request():
            try:
                response = await client.get(f"{base_url}/api/health")
                return response.status_code
            except Exception as e:
                return f"Error: {e}"
        
        tasks = [make_health_request() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r == 200)
        print(f"   Results: {results}")
        print(f"   Successful: {success_count}/5")
        
        # Test concurrent requests to search endpoint
        print("\n4. Testing 5 concurrent requests to /api/search")
        async def make_search_request():
            try:
                response = await client.get(f"{base_url}/api/search?q=test&max_results=5")
                return response.status_code
            except Exception as e:
                return f"Error: {e}"
        
        tasks = [make_search_request() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r == 200)
        rate_limited_count = sum(1 for r in results if r == 429)
        print(f"   Results: {results}")
        print(f"   Successful: {success_count}/5")
        print(f"   Rate limited: {rate_limited_count}/5")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])