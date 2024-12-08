from pathlib import Path
import time
from datetime import datetime, timedelta
import json
from convert_markdown import MarkdownConverter
from publish_medium import MediumPublisher
from publish_devto import DevToPublisher
from post_tracker import PostTracker
from config.settings import Settings
from utils.logger import get_logger
from utils.exceptions import PublishError

class RateLimitManager:
    def __init__(self, limits_file: str = "rate_limits.json"):
        self.limits_file = Path(limits_file)
        self.logger = get_logger(__name__)
        self.limits = self._load_limits()
    
    def _load_limits(self) -> dict:
        if self.limits_file.exists():
            try:
                with self.limits_file.open('r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_limits(self):
        try:
            with self.limits_file.open('w') as f:
                json.dump(self.limits, f)
        except Exception as e:
            self.logger.error(f"Error saving rate limits: {e}")
    
    def is_rate_limited(self, platform: str) -> bool:
        if platform in self.limits:
            reset_time = datetime.fromisoformat(self.limits[platform])
            if datetime.now() < reset_time:
                return True
        return False
    
    def set_rate_limit(self, platform: str, duration_minutes: int):
        reset_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.limits[platform] = reset_time.isoformat()
        self._save_limits()
        self.logger.info(f"Set rate limit for {platform} until {reset_time}")

def main():
    logger = get_logger(__name__)
    try:
        # Initialize components
        logger.info("Starting blog post publication process...")
        
        tracker = PostTracker()
        rate_limits = RateLimitManager()
        converter = MarkdownConverter(Settings.MARKDOWN_DIR, Settings.OUTPUT_DIR)
        medium_publisher = MediumPublisher(Settings.MEDIUM_TOKEN)
        devto_publisher = DevToPublisher(Settings.DEVTO_API_KEY)

        # Get all markdown files
        markdown_dir = Path(Settings.MARKDOWN_DIR)
        all_files = {str(f.relative_to(markdown_dir)) for f in markdown_dir.glob('*.md')}
        needs_publishing = tracker.get_unpublished_files(all_files)
        
        # Check if platforms are rate limited
        if rate_limits.is_rate_limited('medium'):
            logger.warning("Medium is currently rate limited, skipping Medium posts")
            needs_publishing['medium'] = set()
            
        if rate_limits.is_rate_limited('devto'):
            logger.warning("Dev.to is currently rate limited, skipping Dev.to posts")
            needs_publishing['devto'] = set()

        # Process Medium posts
        if needs_publishing['medium']:
            logger.info(f"Found {len(needs_publishing['medium'])} posts for Medium")
            for file_path in needs_publishing['medium']:
                try:
                    if rate_limits.is_rate_limited('medium'):
                        break
                        
                    full_path = markdown_dir / file_path
                    post = converter.convert_single_file(full_path)
                    
                    try:
                        medium_result = medium_publisher.publish(post)
                        medium_url = medium_result.get('data', {}).get('url')
                        medium_id = medium_result.get('data', {}).get('id')
                        
                        if medium_url:
                            tracker.mark_platform_published(
                                file_path, 'medium', medium_url, medium_id
                            )
                            logger.info(f"Successfully published to Medium: {medium_url}")
                            time.sleep(5)  # Wait between posts
                    except PublishError as e:
                        if "rate limit" in str(e).lower():
                            rate_limits.set_rate_limit('medium', 1440)  # 24 hours
                            logger.warning("Medium rate limit reached, skipping remaining posts")
                            break
                        logger.error(f"Failed to publish to Medium: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing {file_path} for Medium: {str(e)}")

        # Process Dev.to posts
        if needs_publishing['devto']:
            logger.info(f"Found {len(needs_publishing['devto'])} posts for Dev.to")
            for file_path in needs_publishing['devto']:
                try:
                    if rate_limits.is_rate_limited('devto'):
                        break
                        
                    full_path = markdown_dir / file_path
                    post = converter.convert_single_file(full_path)
                    
                    try:
                        devto_result = devto_publisher.publish(post)
                        devto_url = devto_result.get('url')
                        devto_id = devto_result.get('id')
                        
                        if devto_url:
                            tracker.mark_platform_published(
                                file_path, 'devto', devto_url, devto_id
                            )
                            logger.info(f"Successfully published to Dev.to: {devto_url}")
                            time.sleep(60)  # Wait 1 minute between posts to avoid duplicates
                    except PublishError as e:
                        if "rate limit" in str(e).lower() or "retry later" in str(e).lower():
                            rate_limits.set_rate_limit('devto', 60)  # 1 hour
                            logger.warning("Dev.to rate limit reached, skipping remaining posts")
                            break
                        elif "title has already been used" in str(e).lower():
                            logger.warning(f"Skipping duplicate post {file_path}")
                            tracker.mark_platform_published(
                                file_path, 'devto', 'skipped-duplicate', None
                            )
                        else:
                            logger.error(f"Failed to publish to Dev.to: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing {file_path} for Dev.to: {str(e)}")

        logger.info("Publication process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()