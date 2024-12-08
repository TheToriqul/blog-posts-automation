from pathlib import Path
import time
import hashlib
from convert_markdown import MarkdownConverter
from publish_medium import MediumPublisher
from publish_devto import DevToPublisher
from post_tracker import PostTracker
from config.settings import Settings
from utils.logger import get_logger
from utils.exceptions import PublishError

def main():
    logger = get_logger(__name__)
    try:
        # Initialize components
        logger.info("Starting blog post publication process...")
        
        tracker = PostTracker()
        converter = MarkdownConverter(Settings.MARKDOWN_DIR, Settings.OUTPUT_DIR)
        medium_publisher = MediumPublisher(Settings.MEDIUM_TOKEN)
        devto_publisher = DevToPublisher(Settings.DEVTO_API_KEY)

        # Get all markdown files
        markdown_dir = Path(Settings.MARKDOWN_DIR)
        all_files = {str(f.relative_to(markdown_dir)) for f in markdown_dir.glob('*.md')}
        
        # Get platform-specific unpublished files
        needs_publishing = tracker.get_unpublished_files(all_files)
        
        # Process Medium posts
        if needs_publishing['medium']:
            logger.info(f"Found {len(needs_publishing['medium'])} posts for Medium")
            for file_path in needs_publishing['medium']:
                try:
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
                    except PublishError as e:
                        logger.error(f"Failed to publish to Medium: {str(e)}")
                        if "rate limit" in str(e).lower():
                            logger.warning("Medium rate limit reached, skipping remaining Medium posts")
                            break
                except Exception as e:
                    logger.error(f"Error processing {file_path} for Medium: {str(e)}")
        
        # Process Dev.to posts
        if needs_publishing['devto']:
            logger.info(f"Found {len(needs_publishing['devto'])} posts for Dev.to")
            for file_path in needs_publishing['devto']:
                try:
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
                            
                        # Add delay between Dev.to posts
                        time.sleep(2)
                    except PublishError as e:
                        logger.error(f"Failed to publish to Dev.to: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing {file_path} for Dev.to: {str(e)}")

        logger.info("Publication process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()