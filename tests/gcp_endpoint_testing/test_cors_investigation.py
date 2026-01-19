"""
Investigation of CORS behavior in GCP deployment
"""

import pytest
import httpx

from .config import test_config


@pytest.mark.asyncio
async def test_cors_headers_investigation():
    """Investigate CORS headers on different request types"""
    
    async with httpx.AsyncClient(verify=False) as client:
        base_url = test_config.base_url
        
        print(f"\n🔍 Investigating CORS headers on {base_url}")
        
        # Test GET request to health endpoint
        print("\n1. Testing GET /api/health")
        try:
            response = await client.get(f"{base_url}/api/health")
            print(f"   Status: {response.status_code}")
            print("   CORS Headers:")
            for header, value in response.headers.items():
                if 'access-control' in header.lower() or 'cors' in header.lower():
                    print(f"     {header}: {value}")
            
            # Check for any CORS-related headers
            cors_headers = {k: v for k, v in response.headers.items() 
                          if 'access-control' in k.lower()}
            if not cors_headers:
                print("     ❌ No CORS headers found in GET response")
            else:
                print(f"     ✅ Found CORS headers: {cors_headers}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test OPTIONS request to health endpoint
        print("\n2. Testing OPTIONS /api/health")
        try:
            response = await client.options(f"{base_url}/api/health")
            print(f"   Status: {response.status_code}")
            print("   CORS Headers:")
            for header, value in response.headers.items():
                if 'access-control' in header.lower() or 'cors' in header.lower():
                    print(f"     {header}: {value}")
            
            # Check for any CORS-related headers
            cors_headers = {k: v for k, v in response.headers.items() 
                          if 'access-control' in k.lower()}
            if not cors_headers:
                print("     ❌ No CORS headers found in OPTIONS response")
            else:
                print(f"     ✅ Found CORS headers: {cors_headers}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test with Origin header (simulate browser request)
        print("\n3. Testing GET /api/health with Origin header")
        try:
            headers = {
                'Origin': 'https://mpyjuice-ui.vercel.app',
                'User-Agent': 'Mozilla/5.0 (compatible; test-client)'
            }
            response = await client.get(f"{base_url}/api/health", headers=headers)
            print(f"   Status: {response.status_code}")
            print("   CORS Headers:")
            for header, value in response.headers.items():
                if 'access-control' in header.lower() or 'cors' in header.lower():
                    print(f"     {header}: {value}")
            
            # Check for any CORS-related headers
            cors_headers = {k: v for k, v in response.headers.items() 
                          if 'access-control' in k.lower()}
            if not cors_headers:
                print("     ❌ No CORS headers found with Origin header")
            else:
                print(f"     ✅ Found CORS headers: {cors_headers}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test preflight request (OPTIONS with CORS headers)
        print("\n4. Testing preflight OPTIONS /api/health")
        try:
            headers = {
                'Origin': 'https://mpyjuice-ui.vercel.app',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = await client.options(f"{base_url}/api/health", headers=headers)
            print(f"   Status: {response.status_code}")
            print("   All Headers:")
            for header, value in response.headers.items():
                print(f"     {header}: {value}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])