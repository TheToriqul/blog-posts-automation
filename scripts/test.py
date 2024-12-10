import unittest
from pathlib import Path
import json
import shutil
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, mock_open
from scripts.queue_manager import PostQueue
from scripts.utils.exceptions import QueueError

class TestPostQueue(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = Path("test_queue_data")
        self.test_dir.mkdir(exist_ok=True)
        self.queue = PostQueue(base_dir=str(self.test_dir))
        
    def tearDown(self):
        """Clean up test environment after each test"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            
    def test_initialize_queue(self):
        """Test queue initialization"""
        self.assertTrue(self.queue.queue_dir.exists())
        self.assertTrue(self.queue.queue_file.exists())
        with self.queue.queue_file.open() as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
            
    def test_add_to_queue(self):
        """Test adding posts to queue"""
        file_path = "test_post.md"
        platforms = ["medium", "devto"]
        
        self.queue.add_to_queue(file_path, platforms)
        
        # Verify post was added
        self.assertIn(file_path, self.queue.queued_posts)
        self.assertEqual(self.queue.queued_posts[file_path]["platforms"], platforms)
        self.assertEqual(self.queue.queued_posts[file_path]["status"], "queued")
        
    def test_add_to_queue_with_schedule(self):
        """Test adding posts with scheduled time"""
        file_path = "scheduled_post.md"
        platforms = ["medium"]
        scheduled_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        
        self.queue.add_to_queue(file_path, platforms, scheduled_time)
        
        self.assertIn(file_path, self.queue.queued_posts)
        self.assertEqual(self.queue.queued_posts[file_path]["scheduled_time"], scheduled_time)
        
    def test_get_ready_posts(self):
        """Test retrieving posts ready for publishing"""
        # Add a post scheduled for now
        current_post = "current_post.md"
        self.queue.add_to_queue(current_post, ["medium"])
        
        # Add a post scheduled for future
        future_post = "future_post.md"
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        self.queue.add_to_queue(future_post, ["devto"], future_time)
        
        ready_posts = self.queue.get_ready_posts()
        
        self.assertEqual(len(ready_posts), 1)
        self.assertEqual(ready_posts[0]["file_path"], current_post)
        
    def test_mark_completed(self):
        """Test marking posts as completed"""
        file_path = "test_post.md"
        platforms = ["medium", "devto"]
        self.queue.add_to_queue(file_path, platforms.copy())  # Use copy to preserve original list
        
        # Mark medium as completed
        self.queue.mark_completed(file_path, "medium")
        
        # After marking medium complete, only devto should remain
        self.assertEqual(self.queue.queued_posts[file_path]["platforms"], ["devto"])
        self.assertEqual(self.queue.queued_posts[file_path]["status"], "queued")
        
        # Mark devto as completed
        self.queue.mark_completed(file_path, "devto")
        
        # After marking both complete, status should be completed and platforms empty
        self.assertEqual(self.queue.queued_posts[file_path]["status"], "completed")
        self.assertEqual(self.queue.queued_posts[file_path]["platforms"], [])
        self.assertTrue("completed_at" in self.queue.queued_posts[file_path])
        
    def test_get_queue_status(self):
        """Test getting queue status"""
        # Add queued post
        self.queue.add_to_queue("queued_post.md", ["medium"])
        
        # Add completed post
        self.queue.add_to_queue("completed_post.md", ["devto"])
        self.queue.mark_completed("completed_post.md", "devto")
        
        status = self.queue.get_queue_status()
        
        self.assertEqual(len(status["queued"]), 1)
        self.assertEqual(len(status["completed"]), 1)
        
    def test_clean_completed(self):
        """Test cleaning old completed posts"""
        # Add old completed post
        file_path = "old_post.md"
        self.queue.add_to_queue(file_path, ["medium"])
        self.queue.mark_completed(file_path, "medium")
        
        # Modify completed_at to be older
        old_time = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        self.queue.queued_posts[file_path]["completed_at"] = old_time
        
        self.queue.clean_completed(days_old=7)
        self.assertNotIn(file_path, self.queue.queued_posts)
        
    @patch('builtins.open', side_effect=IOError("Failed to write"))
    def test_save_queue_data_failure(self, mock_open):
        """Test handling of save failures"""
        queue = PostQueue(base_dir=str(self.test_dir))
        
        # Attempt to save data which should raise QueueError
        with self.assertRaises(QueueError) as context:
            queue._save_queue_data()
            
        self.assertIn("Failed to save queue data", str(context.exception))
                
    def test_load_queue_data_failure(self):
        """Test handling of load failures"""
        # Corrupt the queue file
        with self.queue.queue_file.open("w") as f:
            f.write("invalid json")
            
        # Create new queue instance to trigger load
        with self.assertLogs() as captured:
            new_queue = PostQueue(base_dir=str(self.test_dir))
            self.assertEqual(new_queue.queued_posts, {})
            self.assertTrue(any("Error loading queue data" in msg for msg in captured.output))
            
    def test_invalid_queue_data_format(self):
        """Test handling of invalid queue data format"""
        # Write invalid format (array instead of dict)
        with self.queue.queue_file.open("w") as f:
            json.dump([], f)
            
        # Create new queue instance to trigger load
        with self.assertLogs() as captured:
            new_queue = PostQueue(base_dir=str(self.test_dir))
            self.assertEqual(new_queue.queued_posts, {})
            self.assertTrue(any("Invalid queue data format" in msg for msg in captured.output))

if __name__ == "__main__":
    unittest.main()