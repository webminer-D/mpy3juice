"""
Temporary file cleanup utilities
Ensures resources are cleaned up after processing
Requirements: 10.5, 11.4
"""

import tempfile
import shutil
import logging
import atexit
import threading
from pathlib import Path
from typing import Set, Optional
from contextlib import contextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CleanupManager:
    """
    Manages temporary file cleanup
    Tracks temporary directories and ensures cleanup on both success and failure
    Requirements: 10.5, 11.4
    """
    
    def __init__(self):
        """Initialize cleanup manager"""
        self._temp_dirs: Set[Path] = set()
        self._lock = threading.Lock()
        
        # Register cleanup on program exit
        atexit.register(self.cleanup_all)
    
    def create_temp_dir(self, prefix: str = "audio_toolkit_") -> Path:
        """
        Create a temporary directory and track it for cleanup
        
        Args:
            prefix: Prefix for temporary directory name
            
        Returns:
            Path to temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        
        with self._lock:
            self._temp_dirs.add(temp_dir)
        
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir
    
    def cleanup_dir(self, temp_dir: Path) -> bool:
        """
        Clean up a specific temporary directory
        
        Args:
            temp_dir: Path to temporary directory
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            
            with self._lock:
                self._temp_dirs.discard(temp_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean up temporary directory {temp_dir}: {e}")
            return False
    
    def cleanup_all(self):
        """
        Clean up all tracked temporary directories
        Called on program exit or manually
        """
        with self._lock:
            temp_dirs_copy = self._temp_dirs.copy()
        
        if temp_dirs_copy:
            logger.info(f"Cleaning up {len(temp_dirs_copy)} temporary directories")
            
            for temp_dir in temp_dirs_copy:
                self.cleanup_dir(temp_dir)
    
    @contextmanager
    def temp_directory(self, prefix: str = "audio_toolkit_"):
        """
        Context manager for temporary directory
        Ensures cleanup on both success and failure
        
        Args:
            prefix: Prefix for temporary directory name
            
        Yields:
            Path to temporary directory
            
        Example:
            with cleanup_manager.temp_directory() as temp_dir:
                # Use temp_dir
                pass
            # temp_dir is automatically cleaned up
        """
        temp_dir = self.create_temp_dir(prefix)
        
        try:
            yield temp_dir
        finally:
            # Clean up regardless of success or failure (Requirement 10.5, 11.4)
            self.cleanup_dir(temp_dir)


# Global cleanup manager instance
cleanup_manager = CleanupManager()


@contextmanager
def temporary_directory(prefix: str = "audio_toolkit_"):
    """
    Convenience function for temporary directory context manager
    
    Args:
        prefix: Prefix for temporary directory name
        
    Yields:
        Path to temporary directory
        
    Example:
        with temporary_directory() as temp_dir:
            # Use temp_dir
            pass
        # temp_dir is automatically cleaned up
    """
    with cleanup_manager.temp_directory(prefix) as temp_dir:
        yield temp_dir


def cleanup_old_temp_files(max_age_hours: int = 1):
    """
    Clean up old temporary files that may have been left behind
    Useful for periodic cleanup tasks
    
    Args:
        max_age_hours: Maximum age of temporary files in hours
    """
    temp_root = Path(tempfile.gettempdir())
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    cleaned_count = 0
    
    try:
        # Find all audio_toolkit_* directories in temp
        for temp_dir in temp_root.glob("audio_toolkit_*"):
            if not temp_dir.is_dir():
                continue
            
            # Check directory age
            try:
                dir_mtime = datetime.fromtimestamp(temp_dir.stat().st_mtime)
                
                if dir_mtime < cutoff_time:
                    shutil.rmtree(temp_dir)
                    cleaned_count += 1
                    logger.debug(f"Cleaned up old temporary directory: {temp_dir}")
            
            except Exception as e:
                logger.warning(f"Failed to clean up old directory {temp_dir}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old temporary directories")
    
    except Exception as e:
        logger.error(f"Error during old temp file cleanup: {e}")
