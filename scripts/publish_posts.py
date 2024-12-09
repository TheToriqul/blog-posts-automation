from pathlib import Path
import time
from datetime import datetime
from scripts.convert_markdown import MarkdownConverter
from scripts.publish_medium import MediumPublisher
from scripts.publish_devto import DevToPublisher
from scripts.post_tracker import PostTracker
from scripts.queue_manager import PostQueue
from scripts.config.settings import Settings
from scripts.utils.logger import get_logger
from scripts.utils.exceptions import PublishError

def main():
    logger = get_logger(__name__)
    try:
        # Initialize components with project root directory
        project_root = Path.cwd()
        logger.info(f"Project root directory: {project_root}")
        
        tracker = PostTracker(base_dir=project_root)
        queue = PostQueue(base_dir=project_root)
        converter = MarkdownConverter(Settings.MARKDOWN_DIR, Settings.OUTPUT_DIR)
        medium_publisher = MediumPublisher(Settings.MEDIUM_TOKEN)
        devto_publisher = DevToPublisher(Settings.DEVTO_API_KEY)

        # Get all markdown files
        markdown_dir = Path(Settings.MARKDOWN_DIR)
        all_files = {str(f.relative_to(markdown_dir)) for f in markdown_dir.glob('*.md')}
        
        logger.info(f"Found markdown files: {all_files}")
        
        # Get unpublished files
        needs_publishing = tracker.get_unpublished_files(all_files)
        logger.info(f"Found {len(needs_publishing['medium'])} posts for Medium")
        logger.info(f"Found {len(needs_publishing['devto'])} posts for Dev.to")

        # Process ready posts
        ready_posts = queue.get_ready_posts()
        for post in ready_posts:
            file_path = post['file_path']
            full_path = markdown_dir / file_path
            
            try:
                converted_post = converter.convert_single_file(full_path)
                
                # Publish to each platform
                if 'medium' in post['platforms']:
                    try:
                        medium_result = medium_publisher.publish(converted_post)
                        medium_url = medium_result.get('data', {}).get('url')
                        medium_id = medium_result.get('data', {}).get('id')
                        
                        if medium_url:
                            tracker.mark_platform_published(
                                file_path, 'medium', medium_url, medium_id
                            )
                            queue.mark_completed(file_path, 'medium')
                            logger.info(f"Successfully published to Medium: {medium_url}")
                    except PublishError as e:
                        logger.error(f"Failed to publish to Medium: {str(e)}")
                
                if 'devto' in post['platforms']:
                    try:
                        devto_result = devto_publisher.publish(converted_post)
                        devto_url = devto_result.get('url')
                        devto_id = devto_result.get('id')
                        
                        if devto_url:
                            tracker.mark_platform_published(
                                file_path, 'devto', devto_url, devto_id
                            )
                            queue.mark_completed(file_path, 'devto')
                            logger.info(f"Successfully published to Dev.to: {devto_url}")
                    except PublishError as e:
                        logger.error(f"Failed to publish to Dev.to: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue

        # Clean old completed posts
        queue.clean_completed(days_old=7)
        logger.info("Publication process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()