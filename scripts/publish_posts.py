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

def validate_credentials():
    """Validate that required API credentials are set"""
    missing = []
    if not Settings.MEDIUM_TOKEN:
        missing.append("MEDIUM_TOKEN")
    if not Settings.DEVTO_API_KEY:
        missing.append("DEVTO_API_KEY")
    return missing

def main():
    logger = get_logger(__name__)
    try:
        # Validate credentials first
        missing_creds = validate_credentials()
        if missing_creds:
            logger.error(f"Missing required credentials: {', '.join(missing_creds)}")
            return

        # Initialize components with project root directory
        project_root = Path.cwd()
        logger.info(f"Project root directory: {project_root}")
        
        tracker = PostTracker(base_dir=project_root)
        queue = PostQueue(base_dir=project_root)
        
        # Initialize publishers
        logger.info("Initializing publishers...")
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

        # Initialize converter
        converter = MarkdownConverter(Settings.MARKDOWN_DIR, Settings.OUTPUT_DIR)

        # Process each file that needs publishing
        for file_path in all_files:
            logger.info(f"Processing file: {file_path}")
            full_path = markdown_dir / file_path
            
            try:
                converted_post = converter.convert_single_file(full_path)
                logger.info(f"Successfully converted {file_path}")

                # Publish to Medium if needed
                if file_path in needs_publishing['medium']:
                    try:
                        logger.info(f"Attempting to publish {file_path} to Medium...")
                        medium_result = medium_publisher.publish(converted_post)
                        medium_url = medium_result.get('data', {}).get('url')
                        medium_id = medium_result.get('data', {}).get('id')
                        
                        if medium_url:
                            logger.info(f"Successfully published to Medium: {medium_url}")
                            tracker.mark_platform_published(file_path, 'medium', medium_url, medium_id)
                            queue.add_to_queue(file_path, ['medium'])
                            queue.mark_completed(file_path, 'medium')
                    except PublishError as e:
                        logger.error(f"Failed to publish to Medium: {str(e)}")
                
                # Publish to Dev.to if needed
                if file_path in needs_publishing['devto']:
                    try:
                        logger.info(f"Attempting to publish {file_path} to Dev.to...")
                        devto_result = devto_publisher.publish(converted_post)
                        devto_url = devto_result.get('url')
                        devto_id = devto_result.get('id')
                        
                        if devto_url:
                            logger.info(f"Successfully published to Dev.to: {devto_url}")
                            tracker.mark_platform_published(file_path, 'devto', devto_url, devto_id)
                            queue.add_to_queue(file_path, ['devto'])
                            queue.mark_completed(file_path, 'devto')
                    except PublishError as e:
                        logger.error(f"Failed to publish to Dev.to: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue

        # Clean old completed posts
        queue.clean_completed(days_old=7)
        
        # Get final status
        queue_status = queue.get_queue_status()
        tracking_status = tracker.get_status_report()
        logger.info("Final queue status: %s", queue_status)
        logger.info("Final tracking status: %s", tracking_status)
        
        logger.info("Publication process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()