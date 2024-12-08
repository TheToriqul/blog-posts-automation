from convert_markdown import MarkdownConverter
from publish_medium import MediumPublisher
from publish_devto import DevToPublisher
from config.settings import Settings
from utils.logger import get_logger
from utils.exceptions import PublishError

def main():
    logger = get_logger(__name__)
    try:
        # Initialize components
        logger.info("Starting blog post publication process...")
        
        converter = MarkdownConverter(Settings.MARKDOWN_DIR, Settings.OUTPUT_DIR)
        medium_publisher = MediumPublisher(Settings.MEDIUM_TOKEN)
        devto_publisher = DevToPublisher(Settings.DEVTO_API_KEY)

        # Process and publish
        converted_posts = converter.convert()
        logger.info(f"Successfully converted {len(converted_posts)} posts")

        for post in converted_posts:
            logger.info(f"Publishing post: {post['metadata']['title']}")
            
            # Try Medium publication
            try:
                medium_result = medium_publisher.publish(post)
                logger.info("Successfully published to Medium")
            except PublishError as e:
                logger.error(f"Failed to publish to Medium: {str(e)}")
            
            # Try Dev.to publication
            try:
                devto_result = devto_publisher.publish(post)
                logger.info("Successfully published to Dev.to")
            except PublishError as e:
                logger.error(f"Failed to publish to Dev.to: {str(e)}")

        logger.info("Publication process completed")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()