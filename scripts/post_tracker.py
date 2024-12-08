import json
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime
import hashlib
from utils.logger import get_logger

class PostTracker:
    """Enhanced tracking system for published blog posts"""
    
    def __init__(self, tracking_file: str = "published_posts.json"):
        self.tracking_file = Path(tracking_file)
        self.logger = get_logger(__name__)
        self.published_posts: Dict[str, Dict] = {}
        self._load_tracking_data()
    
    def _load_tracking_data(self):
        """Load existing tracking data"""
        if self.tracking_file.exists():
            try:
                with self.tracking_file.open('r') as f:
                    self.published_posts = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading tracking data: {e}")
                self.published_posts = {}
    
    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            # Create directory if it doesn't exist
            self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self.tracking_file.open('w') as f:
                json.dump(self.published_posts, f, indent=2)
                
            self.logger.debug(f"Saved tracking data: {self.published_posts}")
        except Exception as e:
            self.logger.error(f"Error saving tracking data: {e}")
    
    def get_unpublished_files(self, all_files: Set[str]) -> Set[str]:
        """Get list of files that haven't been published yet"""
        unpublished = set()
        for file_path in all_files:
            if not self.is_published(file_path):
                self.logger.info(f"Found unpublished file: {file_path}")
                unpublished.add(file_path)
            else:
                self.logger.info(f"Skipping already published file: {file_path}")
        return unpublished
    
    def is_published(self, file_path: str) -> bool:
        """Check if a post has already been published successfully"""
        if file_path in self.published_posts:
            post_data = self.published_posts[file_path]
            # Consider it published if it was published to at least one platform
            return bool(post_data.get('medium_url') or post_data.get('devto_url'))
        return False
    
    def mark_as_published(self, file_path: str, content_hash: str,
                         medium_url: Optional[str] = None,
                         devto_url: Optional[str] = None):
        """Mark a post as published with platform-specific URLs"""
        self.published_posts[file_path] = {
            'content_hash': content_hash,
            'published_at': datetime.now().isoformat(),
            'medium_url': medium_url,
            'devto_url': devto_url,
            'last_updated': datetime.now().isoformat()
        }
        self._save_tracking_data()
        self.logger.info(f"Marked {file_path} as published. Medium: {medium_url}, Dev.to: {devto_url}")