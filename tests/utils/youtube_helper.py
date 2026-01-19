"""
YouTube test helper utilities for testing YouTube-related functionality.
Provides valid and invalid URLs for comprehensive testing.
"""

import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs


class YouTubeTestHelper:
    """Provides utilities for testing YouTube-related functionality."""
    
    def __init__(self):
        # Curated test URLs that should be stable for testing
        # Note: These are example URLs - in real testing, you'd want to use
        # URLs that are known to be stable and available
        self._valid_video_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - classic stable video
            "https://youtu.be/dQw4w9WgXcQ",  # Short format
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Another stable video
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",  # Mobile format
        ]
        
        self._valid_playlist_urls = [
            "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMt9H_i1_2pONgQnDn",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy6nuLMt9H_i1_2pONgQnDn",
        ]
        
        self._invalid_urls = [
            "https://www.youtube.com/watch?v=INVALID_VIDEO_ID",
            "https://youtu.be/INVALID123",
            "https://www.youtube.com/watch?v=",  # Empty video ID
            "not_a_url_at_all",
            "https://www.google.com",  # Valid URL but not YouTube
            "https://www.youtube.com/watch",  # Missing video ID
            "https://www.youtube.com/playlist?list=INVALID_PLAYLIST",
        ]
    
    def get_valid_test_urls(self) -> List[str]:
        """Get list of valid YouTube URLs for testing."""
        return self._valid_video_urls.copy()
    
    def get_invalid_test_urls(self) -> List[str]:
        """Get list of invalid YouTube URLs for testing."""
        return self._invalid_urls.copy()
    
    def get_playlist_test_urls(self) -> List[str]:
        """Get list of valid playlist URLs for testing."""
        return self._valid_playlist_urls.copy()
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        # Handle different YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from YouTube URL."""
        match = re.search(r'list=([^&\n?#]+)', url)
        return match.group(1) if match else ""
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL format."""
        youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com', 'www.youtube.com']
        
        try:
            parsed = urlparse(url)
            if parsed.netloc not in youtube_domains:
                return False
            
            # Check for video ID
            video_id = self.extract_video_id(url)
            return len(video_id) > 0
            
        except Exception:
            return False
    
    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a YouTube playlist URL."""
        return 'list=' in url and self.is_valid_youtube_url(url)
    
    def validate_youtube_response(self, response: dict) -> bool:
        """Validate structure of YouTube API response."""
        if not isinstance(response, dict):
            return False
        
        # Check for required fields in video info response
        required_fields = ['title']  # Minimal required field
        
        return all(field in response for field in required_fields)
    
    def create_mixed_url_list(self, valid_count: int = 3, invalid_count: int = 2) -> List[str]:
        """Create a mixed list of valid and invalid URLs for bulk testing."""
        urls = []
        
        # Add valid URLs
        valid_urls = self.get_valid_test_urls()
        for i in range(min(valid_count, len(valid_urls))):
            urls.append(valid_urls[i])
        
        # Add invalid URLs
        invalid_urls = self.get_invalid_test_urls()
        for i in range(min(invalid_count, len(invalid_urls))):
            urls.append(invalid_urls[i])
        
        return urls
    
    def generate_test_search_queries(self) -> List[str]:
        """Generate test search queries for YouTube search testing."""
        return [
            "test music",
            "python tutorial",
            "funny cats",
            "news",
            "music video",
            "",  # Empty query for error testing
            "a" * 1000,  # Very long query
            "special!@#$%^&*()characters",  # Special characters
        ]
    
    def create_bulk_test_data(self) -> Dict[str, Any]:
        """Create comprehensive test data for bulk operations."""
        return {
            "valid_urls": self.get_valid_test_urls()[:3],  # Limit for testing
            "invalid_urls": self.get_invalid_test_urls()[:3],
            "mixed_urls": self.create_mixed_url_list(),
            "playlist_urls": self.get_playlist_test_urls()[:2],
            "search_queries": self.generate_test_search_queries()
        }