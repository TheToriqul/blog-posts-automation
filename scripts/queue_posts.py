from pathlib import Path
from scripts.queue_manager import PostQueue
from scripts.utils.logger import get_logger
from scripts.config.settings import Settings

def main():
    logger = get_logger(__name__)
    try:
        # Initialize components
        project_root = Path.cwd()
        logger.info(f"Project root directory: {project_root}")
        
        queue = PostQueue(base_dir=project_root)
        
        # Get all markdown files from the posts directory
        markdown_dir = Path(Settings.MARKDOWN_DIR)
        all_files = {str(f.relative_to(markdown_dir)) for f in markdown_dir.glob('*.md')}
        
        # Add new files to queue
        platforms = ['medium', 'devto']  # Default platforms
        for file_path in all_files:
            logger.info(f"Queueing file: {file_path}")
            queue.add_to_queue(file_path, platforms)
            
        # Get queue status
        status = queue.get_queue_status()
        logger.info("Queue status: %s", status)
        
        logger.info("Queuing process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()