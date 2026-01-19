#!/usr/bin/env python3
"""
Debug script for GCP trimming issue
Tests the trim functionality with detailed logging
"""

import requests
import logging
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_trim_endpoint(base_url, audio_file_path):
    """Test the trim endpoint with a local audio file"""
    
    logger.info(f"Testing trim endpoint at: {base_url}")
    logger.info(f"Using audio file: {audio_file_path}")
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found: {audio_file_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(audio_file_path)
    logger.info(f"File size: {file_size} bytes")
    
    try:
        # Prepare the request
        url = f"{base_url}/api/trim"
        
        with open(audio_file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(audio_file_path), f, 'audio/mpeg')
            }
            data = {
                'start_time': '0.5',
                'end_time': '1.5'
            }
            
            logger.info(f"Sending POST request to: {url}")
            logger.info(f"Parameters: start_time=0.5, end_time=1.5")
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                logger.info(f"SUCCESS: Received {len(response.content)} bytes")
                
                # Save the output file
                output_path = "debug_trimmed_output.mp3"
                with open(output_path, 'wb') as out_f:
                    out_f.write(response.content)
                logger.info(f"Saved output to: {output_path}")
                return True
            else:
                logger.error(f"FAILED: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False

def test_health_endpoint(base_url):
    """Test the health endpoint"""
    
    try:
        url = f"{base_url}/api/health"
        logger.info(f"Testing health endpoint: {url}")
        
        response = requests.get(url, timeout=10)
        logger.info(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"Health data: {health_data}")
            return health_data.get('ffmpeg_available', False)
        else:
            logger.error(f"Health check failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Health check exception: {str(e)}")
        return False

def main():
    """Main debug function"""
    
    if len(sys.argv) < 2:
        print("Usage: python debug_trim_issue.py <base_url> [audio_file_path]")
        print("Example: python debug_trim_issue.py https://your-gcp-url.com")
        print("Example: python debug_trim_issue.py https://your-gcp-url.com test_audio.mp3")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    audio_file_path = sys.argv[2] if len(sys.argv) > 2 else "test_audio.mp3"
    
    logger.info("="*50)
    logger.info("GCP Trim Issue Debug Script")
    logger.info("="*50)
    
    # Test health endpoint first
    logger.info("Step 1: Testing health endpoint...")
    ffmpeg_available = test_health_endpoint(base_url)
    
    if not ffmpeg_available:
        logger.error("FFmpeg not available on server - this is likely the issue!")
        sys.exit(1)
    
    logger.info("✓ FFmpeg is available on server")
    
    # Test trim endpoint
    logger.info("Step 2: Testing trim endpoint...")
    success = test_trim_endpoint(base_url, audio_file_path)
    
    if success:
        logger.info("✓ Trim endpoint test PASSED")
    else:
        logger.error("✗ Trim endpoint test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()