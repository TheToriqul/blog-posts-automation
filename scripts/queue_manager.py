from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import json
from .utils.logger import get_logger
from .utils.exceptions import QueueError

class PostQueue:
    """Manages the queuing system for blog post publications"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the post queue"""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.queue_dir = self.base_dir / '.queue'
        self.queue_file = self.queue_dir / 'post_queue.json'
        self.logger = get_logger(__name__)
        self.queued_posts: Dict[str, Dict] = {}
        
        # Create queue directory if it doesn't exist
        self.queue_dir.mkdir(exist_ok=True)
        
        # Initialize queue file if it doesn't exist
        if not self.queue_file.exists():
            self._save_queue_data()
            
        self._load_queue_data()
    
    def _load_queue_data(self):
        """Load existing queue data"""
        try:
            if self.queue_file.exists():
                with self.queue_file.open('r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.queued_posts = data
                        self.logger.info(f"Loaded queue data for {len(data)} posts")
                    else:
                        self.logger.warning("Invalid queue data format, initializing empty queue")
                        self.queued_posts = {}
            else:
                self.logger.info("No existing queue data found, initializing empty queue")
                self._save_queue_data()
                
        except Exception as e:
            self.logger.error(f"Error loading queue data: {e}")
            self.queued_posts = {}
            self._save_queue_data()
    
    def _save_queue_data(self):
        """Save queue data to repository"""
        try:
            # Ensure queue directory exists
            self.queue_dir.mkdir(exist_ok=True)
            
            # Save with pretty printing for better readability
            with self.queue_file.open('w') as f:
                json.dump(self.queued_posts, f, indent=2, sort_keys=True)
                
            self.logger.info(f"Saved queue data to {self.queue_file}")
        except Exception as e:
            self.logger.error(f"Error saving queue data: {e}")
            raise QueueError(f"Failed to save queue data: {str(e)}")

    def _get_next_schedule_time(self, schedule_times: List[Dict]) -> str:
        """
        Calculate the next available schedule time
        """
        now = datetime.now(timezone.utc)
        next_time = None
        
        for schedule in schedule_times:
            for day in schedule['days']:
                # Get next occurrence of this day
                next_date = now
                while next_date.weekday() != day:
                    next_date += timedelta(days=1)
                
                # Set the scheduled hour
                next_date = next_date.replace(
                    hour=schedule['hour'],
                    minute=0,
                    second=0,
                    microsecond=0
                )
                
                # If this time is in the past, move to next week
                if next_date <= now:
                    next_date += timedelta(days=7)
                
                # Update if this is sooner than current next_time
                if next_time is None or next_date < next_time:
                    next_time = next_date
        
        return next_time.isoformat()
    
    def add_to_queue(self, file_path: str, platforms: List[str], scheduled_time: Optional[str] = None):
        """
        Add a post to the queue with the next scheduled publish time
        """
        now = datetime.now(timezone.utc)
        
        # If no specific time provided, set to next available schedule
        if not scheduled_time:
            # Define schedule times (13:00 UTC Tue/Thu, 15:00 UTC Sat)
            schedule_times = [
                {'hour': 13, 'days': [1, 3]},  # Tuesday, Thursday
                {'hour': 15, 'days': [5]}      # Saturday
            ]
            
            # Find next scheduled time
            scheduled_time = self._get_next_schedule_time(schedule_times)
        
        self.queued_posts[file_path] = {
            'added_at': now.isoformat(),
            'scheduled_time': scheduled_time,
            'platforms': platforms,
            'status': 'queued'
        }
        
        self._save_queue_data()
        self.logger.info(f"Added {file_path} to queue for platforms: {platforms}, scheduled for {scheduled_time}")
    
    def get_ready_posts(self) -> List[Dict]:
        """Get posts that are ready to be published"""
        now = datetime.now(timezone.utc)
        ready_posts = []
        
        for file_path, data in self.queued_posts.items():
            if data['status'] == 'queued':
                scheduled_time = datetime.fromisoformat(data['scheduled_time'])
                if scheduled_time <= now:
                    ready_posts.append({
                        'file_path': file_path,
                        'platforms': data['platforms'],
                        'queued_at': data['added_at']
                    })
        
        return ready_posts
    
    def mark_completed(self, file_path: str, platform: str):
        """Mark a post as completed for a specific platform"""
        if file_path in self.queued_posts:
            # Remove platform from queue
            if platform in self.queued_posts[file_path]['platforms']:
                self.queued_posts[file_path]['platforms'].remove(platform)
            
            # If no platforms left, mark as completed
            if not self.queued_posts[file_path]['platforms']:
                self.queued_posts[file_path]['status'] = 'completed'
                self.queued_posts[file_path]['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            self._save_queue_data()
            self.logger.info(f"Marked {file_path} as completed for {platform}")
    
    def get_queue_status(self) -> Dict[str, List[Dict]]:
        """Get current queue status"""
        status = {
            'queued': [],
            'completed': []
        }
        
        for file_path, data in self.queued_posts.items():
            queue_item = {
                'file_path': file_path,
                'platforms': data['platforms'],
                'scheduled_time': data['scheduled_time'],
                'added_at': data['added_at']
            }
            
            if data['status'] == 'completed':
                queue_item['completed_at'] = data['completed_at']
                status['completed'].append(queue_item)
            else:
                status['queued'].append(queue_item)
        
        return status