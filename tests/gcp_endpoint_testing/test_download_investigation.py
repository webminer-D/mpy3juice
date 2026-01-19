"""
Investigation of download-audio endpoint behavior
"""

import pytest
import httpx

from .config import test_config


@pytest.mark.asyncio
async def test_download_audio_investigation():
    """Investigate download-audio endpoint behavior"""
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        base_url = test_config.base_url
        
        print(f"\n🔍 Investigating download-audio endpoint on {base_url}")
        
        # Test single request to download-audio endpoint
        print("\n1. Testing single GET /download-audio/?url=https://youtu.be/dQw4w9WgXcQ")
        try:
            response = await client.get(f"{base_url}/download-audio/?url=https://youtu.be/dQw4w9WgXcQ")
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            if response.status_code != 200:
                print(f"   Response: {response.text[:500]}")
            else:
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {response.headers.get('content-length', 'unknown')}")
                print("   ✅ Download endpoint working")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test with a shorter timeout to see if it's a timeout issue
        print("\n2. Testing with 5 second timeout")
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as short_client:
                response = await short_client.get(f"{base_url}/download-audio/?url=https://youtu.be/dQw4w9WgXcQ")
                print(f"   Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error (expected timeout): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])