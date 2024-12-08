import json
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime
from utils.logger import get_logger

class PostTracker:
    """Tracks published blog posts to prevent duplicates"""
    
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
            with self.tracking_file.open('w') as f:
                json.dump(self.published_posts, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving tracking data: {e}")
    
    def is_published(self, file_path: str, content_hash: str) -> bool:
        """
        Check if a post has already been published
        
        Args:
            file_path: Path to the markdown file
            content_hash: Hash of the file content to detect changes
        """
        if file_path in self.published_posts:
            return self.published_posts[file_path]['content_hash'] == content_hash
        return False
    
    def mark_as_published(self, file_path: str, content_hash: str, 
                         medium_url: Optional[str] = None, 
                         devto_url: Optional[str] = None):
        """
        Mark a post as published
        
        Args:
            file_path: Path to the markdown file
            content_hash: Hash of the file content
            medium_url: URL of the Medium post
            devto_url: URL of the Dev.to post
        """
        self.published_posts[file_path] = {
            'content_hash': content_hash,
            'published_at': datetime.now().isoformat(),
            'medium_url': medium_url,
            'devto_url': devto_url
        }
        self._save_tracking_data()
    
    def get_unpublished_files(self, all_files: Set[str]) -> Set[str]:
        """Get list of files that haven't been published yet"""
        return all_files - set(self.published_posts.keys())
    
    def get_publication_status(self, file_path: str) -> Dict:
        """Get publication status for a file"""
        return self.published_posts.get(file_path, {})