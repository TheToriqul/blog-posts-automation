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

def calculate_content_hash(file_path: Path) -> str:
    """Calculate hash of file content to detect changes"""
    with open(file_path, 'rb') as f:
        content = f.read()
        return hashlib.md5(content).hexdigest()

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
        
        # Find unpublished files
        unpublished_files = tracker.get_unpublished_files(all_files)
        logger.info(f"Found {len(unpublished_files)} unpublished posts")

        for file_path in unpublished_files:
            full_path = markdown_dir / file_path
            logger.info(f"Processing new/modified post: {file_path}")
            
            try:
                # Convert the single file
                post = converter.convert_single_file(full_path)
                medium_url = None
                devto_url = None
                
                # Try Medium publication
                try:
                    medium_result = medium_publisher.publish(post)
                    medium_url = medium_result.get('data', {}).get('url')
                    logger.info(f"Successfully published to Medium: {medium_url}")
                except PublishError as medium_error:
                    logger.error(f"Failed to publish to Medium: {str(medium_error)}")
                    if "rate limited" in str(medium_error).lower():
                        logger.warning("Medium rate limit reached, will retry later")
                    
                # Add delay between publications
                time.sleep(2)
                
                # Try Dev.to publication
                try:
                    devto_result = devto_publisher.publish(post)
                    devto_url = devto_result.get('url')
                    logger.info(f"Successfully published to Dev.to: {devto_url}")
                except PublishError as devto_error:
                    logger.error(f"Failed to publish to Dev.to: {str(devto_error)}")
                
                # Mark as published if at least one platform succeeded
                if medium_url or devto_url:
                    tracker.mark_as_published(
                        file_path=file_path,
                        content_hash=calculate_content_hash(full_path),
                        medium_url=medium_url,
                        devto_url=devto_url
                    )
                    logger.info(f"Marked {file_path} as published")
                
            except Exception as post_error:
                logger.error(f"Error processing post {file_path}: {str(post_error)}")
                continue

        logger.info("Publication process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()