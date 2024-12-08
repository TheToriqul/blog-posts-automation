import requests
from typing import Dict, Any, List
import json
import time
from bs4 import BeautifulSoup
from pathlib import Path
import base64
import mimetypes
from utils.logger import get_logger
from utils.exceptions import PublishError

class DevToPublisher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = "https://dev.to/api"
        self.logger = get_logger(__name__)
        self.headers = {
            'api-key': self.api_key,
            'content-type': 'application/json',
            'accept': 'application/vnd.forem.api-v1+json'
        }
        
    def _upload_image_to_devto(self, image_path: str) -> str:
        """Upload an image to Dev.to and return its URL"""
        try:
            # Read image file
            with open(image_path, 'rb') as img_file:
                files = {'image': img_file}
                
                response = requests.post(
                    f"{self.api_base}/images",
                    headers={'api-key': self.api_key},
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return data['image'][0]  # Dev.to returns the URL directly
                else:
                    self.logger.error(f"Failed to upload image. Status: {response.status_code}")
                    self.logger.error(f"Response: {response.text}")
                    raise PublishError(f"Failed to upload image to Dev.to. Status: {response.status_code}", "dev.to")
                    
        except Exception as e:
            self.logger.error(f"Error uploading image {image_path}: {str(e)}")
            raise PublishError(f"Image upload failed: {str(e)}", "dev.to")

    def _process_images_markdown(self, content: str, base_path: str) -> str:
        """Process images in markdown content for Dev.to"""
        try:
            # First convert HTML content to BeautifulSoup for processing
            soup = BeautifulSoup(content, 'html.parser')
            images = soup.find_all('img')
            
            # Keep track of replacements to make
            replacements = []
            
            for img in images:
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                if not src:
                    continue
                    
                # Handle relative paths
                if not src.startswith(('http://', 'https://')):
                    image_path = Path(base_path) / src
                    if image_path.exists():
                        # Upload to Dev.to and get URL
                        devto_url = self._upload_image_to_devto(str(image_path))
                        
                        # Create markdown image syntax
                        if alt:
                            markdown_img = f"![{alt}]({devto_url})"
                        else:
                            markdown_img = f"![]({devto_url})"
                            
                        # Store the replacement
                        replacements.append((str(img), markdown_img))
                    else:
                        self.logger.warning(f"Image not found: {image_path}")
                else:
                    # For external URLs, just convert to markdown format
                    if alt:
                        markdown_img = f"![{alt}]({src})"
                    else:
                        markdown_img = f"![]({src})"
                    replacements.append((str(img), markdown_img))
            
            # Apply replacements
            processed_content = str(soup)
            for old, new in replacements:
                processed_content = processed_content.replace(old, new)
            
            return processed_content
            
        except Exception as e:
            self.logger.error(f"Error processing images: {str(e)}")
            raise PublishError(f"Image processing failed: {str(e)}", "dev.to")

    def publish(self, content: Dict[str, Any], publish_status: bool = True) -> Dict[str, Any]:
        """Publish content to Dev.to with image support"""
        try:
            # Get the base path for images
            base_path = content.get('metadata', {}).get('image_base_path', 'posts/images')
            
            # Process content and handle images
            processed_content = self._process_images_markdown(content['content'], base_path)
            
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
            
            # Publish to Dev.to
            self.logger.info(f"Publishing to Dev.to: {content['metadata']['title']}")
            response = requests.post(
                f"{self.api_base}/articles",
                headers=self.headers,
                json=post_data,
                timeout=15
            )
            
            if response.status_code == 201:
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