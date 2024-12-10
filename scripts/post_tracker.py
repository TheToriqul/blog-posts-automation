from pathlib import Path
from typing import Dict, Set, Optional, Tuple
from datetime import datetime
import json
from .utils.logger import get_logger
from .utils.exceptions import TrackingError

class PostTracker:
    """Tracks the publication status of blog posts across different platforms"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the post tracker"""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        # Store tracking data in repository instead of runner storage
        self.tracking_dir = self.base_dir / '.tracking'
        self.tracking_file = self.tracking_dir / 'published_posts.json'
        self.logger = get_logger(__name__)
        self.published_posts: Dict[str, Dict] = {}
        
        # Create tracking directory if it doesn't exist
        self.tracking_dir.mkdir(exist_ok=True)
        
        # Initialize tracking file if it doesn't exist
        if not self.tracking_file.exists():
            self._save_tracking_data()
            
        self._load_tracking_data()
    
    def _load_tracking_data(self):
        """Load existing tracking data"""
        try:
            if self.tracking_file.exists():
                with self.tracking_file.open('r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.published_posts = data
                        self.logger.info(f"Loaded tracking data for {len(data)} posts")
                    else:
                        self.logger.warning("Invalid tracking data format, initializing empty tracking")
                        self.published_posts = {}
            else:
                self.logger.info("No existing tracking data found, initializing empty tracking")
                self._save_tracking_data()
                
        except Exception as e:
            self.logger.error(f"Error loading tracking data: {e}")
            self.published_posts = {}
            self._save_tracking_data()
    
    def _save_tracking_data(self):
        """Save tracking data to repository"""
        try:
            # Ensure tracking directory exists
            self.tracking_dir.mkdir(exist_ok=True)
            
            # Save with pretty printing for better readability in git
            with self.tracking_file.open('w') as f:
                json.dump(self.published_posts, f, indent=2, sort_keys=True)
                
            self.logger.info(f"Saved tracking data to {self.tracking_file}")
        except Exception as e:
            self.logger.error(f"Error saving tracking data: {e}")
            raise TrackingError(f"Failed to save tracking data: {str(e)}")
    
    def check_platform_status(self, file_path: str) -> Tuple[bool, bool]:
        """Check if a post is published on Medium and Dev.to"""
        post_data = self.published_posts.get(file_path, {})
        platform_data = post_data.get('platforms', {})
        
        medium_published = bool(platform_data.get('medium', {}).get('url'))
        devto_published = bool(platform_data.get('devto', {}).get('url'))
        
        return medium_published, devto_published
    
    def get_unpublished_files(self, all_files: Set[str]) -> Dict[str, Set[str]]:
        """Get files that need publishing for each platform"""
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
        """Mark a post as published on a specific platform"""
        if file_path not in self.published_posts:
            self.published_posts[file_path] = {
                'first_published_at': datetime.now().isoformat(),
                'platforms': {}
            }
        
        self.published_posts[file_path]['platforms'][platform] = {
            'url': url,
            'platform_id': platform_id,
            'published_at': datetime.now().isoformat()
        }
        
        self._save_tracking_data()
        self.logger.info(f"Marked {file_path} as published on {platform}: {url}")
    
    def get_status_report(self) -> Dict[str, Dict]:
        """Get a complete status report of all tracked posts"""
        return self.published_posts