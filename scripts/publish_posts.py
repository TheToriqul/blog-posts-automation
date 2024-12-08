# scripts/publish_posts.py
from convert_markdown import MarkdownConverter
from publish_medium import MediumPublisher
from publish_devto import DevToPublisher
from config.settings import Settings

def main():
    # Initialize components
    Settings.validate_config()
    converter = MarkdownConverter(Settings.MARKDOWN_DIR, Settings.OUTPUT_DIR)
    medium_publisher = MediumPublisher(Settings.MEDIUM_TOKEN)
    devto_publisher = DevToPublisher(Settings.DEVTO_API_KEY)

    # Process and publish
    converted_posts = converter.convert()
    for post in converted_posts:
        medium_result = medium_publisher.publish(post)
        devto_result = devto_publisher.publish(post)

if __name__ == "__main__":
    main()