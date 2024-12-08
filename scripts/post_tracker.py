import json
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, Any
from datetime import datetime, timedelta
import hashlib
from utils.logger import get_logger
from utils.exceptions import TrackingError

class PostTracker:
    """
    Enhanced tracking system for blog post publications across multiple platforms
    with reliable file handling and state preservation.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the post tracker
        
        Args:
            base_dir: Optional base directory for tracking files. Defaults to current working directory.
        """
        # Use the project root directory if no base_dir is provided
        if base_dir is None:
            base_dir = Path.cwd()
        else:
            base_dir = Path(base_dir)
            
        # Create a .tracking directory in the project root
        self.tracking_dir = base_dir / '.tracking'
        self.tracking_file = self.tracking_dir / 'published_posts.json'
        self.backup_file = self.tracking_dir / 'published_posts.backup.json'
        self.logger = get_logger(__name__)
        self.published_posts: Dict[str, Dict] = {}
        
        # Ensure tracking directory exists
        self.tracking_dir.mkdir(exist_ok=True)
        
        self._load_tracking_data()
    
    def _create_backup(self):
        """Create a backup of the tracking file"""
        try:
            if self.tracking_file.exists():
                with self.tracking_file.open('r') as source:
                    with self.backup_file.open('w') as target:
                        target.write(source.read())
                self.logger.debug("Created backup of tracking data")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
    
    def _restore_from_backup(self):
        """Attempt to restore data from backup file"""
        try:
            if self.backup_file.exists():
                with self.backup_file.open('r') as f:
                    self.published_posts = json.load(f)
                self.logger.info("Restored data from backup file")
                return True
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
        return False
    
    def _load_tracking_data(self):
        """Load existing tracking data with fallback mechanism"""
        try:
            if self.tracking_file.exists():
                with self.tracking_file.open('r') as f:
                    data = json.load(f)
                    # Validate the loaded data
                    if isinstance(data, dict):
                        self.published_posts = data
                        self.logger.info(f"Loaded existing tracking data for {len(data)} posts")
                    else:
                        raise TrackingError("Invalid tracking data format")
            else:
                self.logger.info("No existing tracking file found, starting fresh")
                self.published_posts = {}
                
        except TrackingError:
            self.logger.warning("Invalid tracking data format, attempting restore from backup")
            if not self._restore_from_backup():
                self.published_posts = {}
        except Exception as e:
            self.logger.error(f"Error loading tracking data: {e}")
            if not self._restore_from_backup():
                self.published_posts = {}
        
        # Always save after loading to ensure file exists and is valid
        self._save_tracking_data()
    
    def _save_tracking_data(self):
        """Save tracking data to file with backup"""
        try:
            # Create backup before saving
            self._create_backup()
            
            # Ensure directory exists
            self.tracking_dir.mkdir(exist_ok=True)
            
            # Save with pretty formatting for readability
            with self.tracking_file.open('w') as f:
                json.dump(self.published_posts, f, indent=2)
            
            self.logger.debug(f"Saved tracking data to {self.tracking_file}")
        except Exception as e:
            self.logger.error(f"Error saving tracking data: {e}")
            # Log the current state for debugging
            self.logger.debug(f"Current tracking data: {self.published_posts}")
    
    def is_recently_published(self, file_path: str, platform: str, hours: int = 24) -> bool:
        """
        Check if a post was published recently to avoid duplicates
        
        Args:
            file_path: Path to the markdown file
            platform: Publishing platform (e.g., 'medium', 'devto')
            hours: Number of hours to consider as "recent"
            
        Returns:
            bool: True if published within specified hours
        """
        post_data = self.published_posts.get(file_path, {})
        platform_data = post_data.get('platforms', {}).get(platform, {})
        
        if not platform_data:
            return False
            
        last_published = platform_data.get('published_at')
        if not last_published:
            return False
            
        try:
            publish_time = datetime.fromisoformat(last_published)
            time_diff = datetime.now() - publish_time
            return time_diff.total_seconds() < hours * 3600
        except:
            return False
    
    def check_platform_status(self, file_path: str) -> Tuple[bool, bool]:
        """
        Check publication status for each platform
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Tuple[bool, bool]: (medium_published, devto_published)
        """
        post_data = self.published_posts.get(file_path, {})
        platform_data = post_data.get('platforms', {})
        
        medium_published = bool(platform_data.get('medium', {}).get('url'))
        devto_published = bool(platform_data.get('devto', {}).get('url'))
        
        return medium_published, devto_published
    
    def get_platform_url(self, file_path: str, platform: str) -> Optional[str]:
        """
        Get the published URL for a specific platform
        
        Args:
            file_path: Path to the markdown file
            platform: Publishing platform
            
        Returns:
            Optional[str]: Published URL or None if not published
        """
        return (self.published_posts.get(file_path, {})
                .get('platforms', {})
                .get(platform, {})
                .get('url'))
    
    def get_unpublished_files(self, all_files: Set[str]) -> Dict[str, Set[str]]:
        """
        Get files that need publishing with rate limit consideration
        
        Args:
            all_files: Set of all markdown file paths
            
        Returns:
            Dict[str, Set[str]]: Dictionary of unpublished files per platform
        """
        needs_publishing = {
            'medium': set(),
            'devto': set()
        }
        
        for file_path in all_files:
            medium_done, devto_done = self.check_platform_status(file_path)
            
            # Check if not published or not published recently
            if not medium_done and not self.is_recently_published(file_path, 'medium'):
                needs_publishing['medium'].add(file_path)
                self.logger.info(f"File needs Medium publishing: {file_path}")
            
            if not devto_done and not self.is_recently_published(file_path, 'devto'):
                needs_publishing['devto'].add(file_path)
                self.logger.info(f"File needs Dev.to publishing: {file_path}")
                
        return needs_publishing
    
    def mark_platform_published(self, file_path: str, platform: str, 
                              url: str, platform_id: Optional[str] = None):
        """
        Mark a specific platform as published
        
        Args:
            file_path: Path to the markdown file
            platform: Publishing platform
            url: Published URL
            platform_id: Optional platform-specific post ID
        """
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
    
    def update_platform_status(self, file_path: str, platform: str, 
                             status: str, message: Optional[str] = None):
        """
        Update the status of a post on a specific platform
        
        Args:
            file_path: Path to the markdown file
            platform: Publishing platform
            status: Current status (e.g., 'error', 'in_progress', 'published')
            message: Optional status message
        """
        if file_path not in self.published_posts:
            self.published_posts[file_path] = {
                'first_tracked_at': datetime.now().isoformat(),
                'platforms': {}
            }
        
        if platform not in self.published_posts[file_path]['platforms']:
            self.published_posts[file_path]['platforms'][platform] = {}
        
        self.published_posts[file_path]['platforms'][platform].update({
            'status': status,
            'status_message': message,
            'last_updated': datetime.now().isoformat()
        })
        
        self._save_tracking_data()
    
    def get_publication_history(self, file_path: str) -> Dict[str, Any]:
        """
        Get complete publication history for a file
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Dict[str, Any]: Complete publication history
        """
        return self.published_posts.get(file_path, {})
    
    def get_status_report(self) -> Dict[str, Dict]:
        """
        Get a full status report of all tracked posts
        
        Returns:
            Dict[str, Dict]: Complete tracking status for all posts
        """
        return self.published_posts