import json
from pathlib import Path
from typing import Dict, Set, Optional, Tuple
from datetime import datetime
import hashlib
from utils.logger import get_logger

class PostTracker:
    """Enhanced tracking system with reliable file handling"""
    
    def __init__(self, base_dir: Optional[str] = None):
        # Use the project root directory if no base_dir is provided
        if base_dir is None:
            base_dir = Path.cwd()
        else:
            base_dir = Path(base_dir)
            
        # Create a .tracking directory in the project root
        self.tracking_dir = base_dir / '.tracking'
        self.tracking_file = self.tracking_dir / 'published_posts.json'
        self.logger = get_logger(__name__)
        self.published_posts: Dict[str, Dict] = {}
        
        # Ensure tracking directory exists
        self.tracking_dir.mkdir(exist_ok=True)
        
        self._load_tracking_data()
        
    def _load_tracking_data(self):
        """Load existing tracking data"""
        try:
            if self.tracking_file.exists():
                with self.tracking_file.open('r') as f:
                    self.published_posts = json.load(f)
                    self.logger.info(f"Loaded tracking data from {self.tracking_file}")
            else:
                self.logger.info("No existing tracking file found, creating new one")
                self._save_tracking_data()  # Create empty file
        except Exception as e:
            self.logger.error(f"Error loading tracking data: {e}")
            self.published_posts = {}
            self._save_tracking_data()  # Create new file if loading failed
    
    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            # Ensure directory exists
            self.tracking_dir.mkdir(exist_ok=True)
            
            # Save with pretty formatting for readability
            with self.tracking_file.open('w') as f:
                json.dump(self.published_posts, f, indent=2)
            
            self.logger.info(f"Saved tracking data to {self.tracking_file}")
        except Exception as e:
            self.logger.error(f"Error saving tracking data: {e}")
            # Log the current state for debugging
            self.logger.debug(f"Current tracking data: {self.published_posts}")
    
    def check_platform_status(self, file_path: str) -> Tuple[bool, bool]:
        """
        Check publication status for each platform
        Returns: (medium_published, devto_published)
        """
        post_data = self.published_posts.get(file_path, {})
        platform_data = post_data.get('platforms', {})
        
        medium_published = bool(platform_data.get('medium', {}).get('url'))
        devto_published = bool(platform_data.get('devto', {}).get('url'))
        
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
                'first_published_at': datetime.now().isoformat(),
                'platforms': {}
            }
        
        self.published_posts[file_path]['platforms'][platform] = {
            'url': url,
            'platform_id': platform_id,
            'published_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_tracking_data()
        self.logger.info(f"Marked {file_path} as published on {platform}: {url}")
    
    def is_platform_published(self, file_path: str, platform: str) -> bool:
        """Check if a file is published on a specific platform"""
        return bool(
            self.published_posts.get(file_path, {})
            .get('platforms', {})
            .get(platform, {})
            .get('url')
        )

    def get_status_report(self) -> Dict[str, Dict]:
        """Get a full status report of all tracked posts"""
        return self.published_posts