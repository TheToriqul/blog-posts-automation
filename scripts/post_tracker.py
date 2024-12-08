import json
from pathlib import Path
from typing import Dict, Set, Optional, Tuple
from datetime import datetime
import hashlib
from utils.logger import get_logger

class PostTracker:
    """Enhanced tracking system with platform-specific handling"""
    
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
            self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
            with self.tracking_file.open('w') as f:
                json.dump(self.published_posts, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving tracking data: {e}")
    
    def check_platform_status(self, file_path: str) -> Tuple[bool, bool]:
        """
        Check publication status for each platform
        Returns: (medium_published, devto_published)
        """
        post_data = self.published_posts.get(file_path, {})
        medium_published = bool(post_data.get('medium_url'))
        devto_published = bool(post_data.get('devto_url'))
        return medium_published, devto_published
    
    def get_unpublished_files(self, all_files: Set[str]) -> Dict[str, Set[str]]:
        """
        Get files that need publishing for each platform
        Returns: Dict with keys 'medium' and 'devto', values are sets of file paths
        """
        needs_publishing = {
            'medium': set(),
            'devto': set()
        }
        
        for file_path in all_files:
            medium_done, devto_done = self.check_platform_status(file_path)
            
            if not medium_done:
                needs_publishing['medium'].add(file_path)
                self.logger.info(f"File needs Medium publishing: {file_path}")
            
            if not devto_done:
                needs_publishing['devto'].add(file_path)
                self.logger.info(f"File needs Dev.to publishing: {file_path}")
                
        return needs_publishing
    
    def mark_platform_published(self, file_path: str, platform: str, 
                              url: str, platform_id: Optional[str] = None):
        """Mark a specific platform as published"""
        if file_path not in self.published_posts:
            self.published_posts[file_path] = {
                'published_at': datetime.now().isoformat(),
                'platforms': {}
            }
        
        self.published_posts[file_path]['platforms'][platform] = {
            'url': url,
            'platform_id': platform_id,
            'published_at': datetime.now().isoformat()
        }
        
        self._save_tracking_data()
        self.logger.info(f"Marked {file_path} as published on {platform}")
    
    def is_platform_published(self, file_path: str, platform: str) -> bool:
        """Check if a file is published on a specific platform"""
        return bool(
            self.published_posts.get(file_path, {})
            .get('platforms', {})
            .get(platform, {})
            .get('url')
        )