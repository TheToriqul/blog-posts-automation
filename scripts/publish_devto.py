import requests
import logging
import json
import mimetypes
import os
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any

class PublishError(Exception):
    def __init__(self, message: str, platform: str):
        self.message = message
        self.platform = platform
        super().__init__(self.message)

class DevToPublisher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = "https://dev.to/api"
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'api-key': self.api_key,
            'accept': 'application/vnd.forem.api-v1+json'
        }

    def _upload_image_to_devto(self, image_path: str) -> str:
        """Upload an image to Dev.to and return its URL"""
        try:
            self.logger.info(f"Attempting to upload image: {image_path}")
            
            if not os.path.exists(image_path):
                raise PublishError(f"Image file not found: {image_path}", "dev.to")
            
            # Get MIME type
            mime_type = mimetypes.guess_type(image_path)[0]
            if not mime_type:
                mime_type = 'image/jpeg'
                
            self.logger.info(f"Image MIME type: {mime_type}")
            
            # Prepare the file upload
            with open(image_path, 'rb') as img_file:
                files = {
                    'image': (os.path.basename(image_path), img_file, mime_type)
                }
                
                # Set headers specifically for file upload
                headers = {
                    'api-key': self.api_key
                }
                
                self.logger.info("Sending image upload request to Dev.to")
                # Updated endpoint for image upload
                response = requests.post(
                    f"{self.api_base}/uploads",
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                self.logger.info(f"Upload response status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    # The response structure changed in newer API versions
                    image_url = data.get('url', '')
                    if not image_url:
                        image_url = data.get('urls', {}).get('regular', '')
                    self.logger.info(f"Successfully uploaded image: {image_url}")
                    return image_url
                else:
                    self.logger.error(f"Failed to upload image. Status: {response.status_code}")
                    self.logger.error(f"Response: {response.text}")
                    raise PublishError(f"Failed to upload image to Dev.to. Status: {response.status_code}", "dev.to")
                    
        except Exception as e:
            self.logger.error(f"Error uploading image {image_path}: {str(e)}")
            raise PublishError(f"Image upload failed: {str(e)}", "dev.to")

    def _convert_html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to Markdown format"""
        try:
            # Use BeautifulSoup to parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove any script tags
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multiple headlines into chunks
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            self.logger.error(f"Error converting HTML to Markdown: {str(e)}")
            return html_content

    def _process_content(self, content: str, base_path: str) -> str:
        """Process all images and convert content to markdown"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            images = soup.find_all('img')
            
            for img in images:
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                if not src:
                    continue
                    
                if not src.startswith(('http://', 'https://')):
                    image_path = os.path.join(base_path, src)
                    image_path = os.path.abspath(image_path)
                    
                    if os.path.exists(image_path):
                        try:
                            devto_url = self._upload_image_to_devto(str(image_path))
                            img['src'] = devto_url
                        except PublishError as e:
                            self.logger.warning(f"Skipping image {image_path}: {str(e)}")
                            continue
                    else:
                        self.logger.warning(f"Image not found: {image_path}")
            
            # Convert to markdown-style content
            processed_content = str(soup)
            return processed_content
            
        except Exception as e:
            self.logger.error(f"Error processing content: {str(e)}")
            raise PublishError(f"Content processing failed: {str(e)}", "dev.to")

    def publish(self, content: Dict[str, Any], publish_status: bool = True) -> Dict[str, Any]:
        """Publish content to Dev.to"""
        try:
            base_path = content.get('metadata', {}).get('image_base_path', './posts')
            
            # Process content and handle images
            processed_content = self._process_content(content['content'], base_path)
            
            # Format tags
            tags = content['metadata'].get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            
            # Prepare post data
            post_data = {
                'article': {
                    'title': content['metadata']['title'],
                    'body_markdown': processed_content,
                    'published': publish_status,
                    'tags': tags[:4]  # Dev.to allows up to 4 tags
                }
            }
            
            # Add series if specified
            if 'series' in content['metadata']:
                post_data['article']['series'] = content['metadata']['series']
            
            self.logger.info(f"Publishing to Dev.to: {content['metadata']['title']}")
            
            # Update headers for JSON content
            headers = self.headers.copy()
            headers['content-type'] = 'application/json'
            
            response = requests.post(
                f"{self.api_base}/articles",
                headers=headers,
                json=post_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_url = result.get('url', 'URL not available')
                self.logger.info(f"Successfully published to Dev.to. Post URL: {post_url}")
                return result
            else:
                self.logger.error(f"Failed to publish. Response: {response.text}")
                raise PublishError(f"Failed to publish to Dev.to. Status: {response.status_code}", "dev.to")
                
        except Exception as e:
            self.logger.error(f"Error during Dev.to publication: {str(e)}")
            raise PublishError(f"Failed to publish to Dev.to: {str(e)}", "dev.to")