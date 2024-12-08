import requests
from typing import Dict, Any, List
import json
import time
import re
from bs4 import BeautifulSoup
import base64
from pathlib import Path
from utils.logger import get_logger
from utils.exceptions import PublishError

class MediumPublisher:
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.medium.com/v1"
        self.logger = get_logger(__name__)
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
        }
        self._user_id = None
        
    def _upload_image_to_medium(self, image_path: str) -> str:
        """Upload an image to Medium and return its URL"""
        try:
            # Read image file
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                
            # Prepare the image data
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Get the MIME type based on file extension
            extension = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif'
            }
            content_type = mime_types.get(extension, 'image/jpeg')
            
            # Upload to Medium
            upload_data = {
                'contentType': content_type,
                'image': img_base64
            }
            
            response = requests.post(
                f"{self.api_base}/images",
                headers=self.headers,
                json=upload_data,
                timeout=30  # Longer timeout for image upload
            )
            
            if response.status_code == 201:
                data = response.json()
                return data['data']['url']
            else:
                raise PublishError(f"Failed to upload image. Status: {response.status_code}", "medium")
                
        except Exception as e:
            self.logger.error(f"Error uploading image {image_path}: {str(e)}")
            raise PublishError(f"Image upload failed: {str(e)}", "medium")

    def _process_images(self, content: str, base_path: str) -> str:
        """Process all images in the content"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            images = soup.find_all('img')
            
            for img in images:
                src = img.get('src', '')
                if not src:
                    continue
                    
                # Handle relative paths
                if not src.startswith(('http://', 'https://')):
                    # Convert relative path to absolute
                    image_path = Path(base_path) / src
                    if image_path.exists():
                        # Upload to Medium and get URL
                        medium_url = self._upload_image_to_medium(str(image_path))
                        img['src'] = medium_url
                    else:
                        self.logger.warning(f"Image not found: {image_path}")
                
                # Add figure and caption if alt text exists
                if img.get('alt'):
                    figure = soup.new_tag('figure')
                    figcaption = soup.new_tag('figcaption')
                    figcaption.string = img['alt']
                    img.wrap(figure)
                    figure.append(figcaption)
            
            return str(soup)
            
        except Exception as e:
            self.logger.error(f"Error processing images: {str(e)}")
            raise PublishError(f"Image processing failed: {str(e)}", "medium")

    def publish(self, content: Dict[str, Any], publish_status: str = 'public') -> Dict[str, Any]:
        """Publish content to Medium with image support"""
        try:
            if not self._user_id:
                self._user_id = self._get_user_id()
            
            # Get the base path for images (assuming it's in the content metadata)
            base_path = content.get('metadata', {}).get('image_base_path', 'posts/images')
            
            # Process the content and handle images
            processed_content = self._process_images(content['content'], base_path)
            
            post_data = {
                'title': content['metadata']['title'],
                'contentFormat': 'html',
                'content': processed_content,
                'tags': content['metadata'].get('tags', [])[:5],
                'publishStatus': publish_status,
                'notifyFollowers': True
            }
            
            # Publish to Medium
            response = requests.post(
                f"{self.api_base}/users/{self._user_id}/posts",
                headers=self.headers,
                json=post_data,
                timeout=15
            )
            
            if response.status_code == 201:
                result = response.json()
                post_url = result.get('data', {}).get('url', 'URL not available')
                self.logger.info(f"Successfully published to Medium. Post URL: {post_url}")
                return result
            else:
                raise PublishError(f"Failed to publish to Medium. Status: {response.status_code}", "medium")
                
        except Exception as e:
            self.logger.error(f"Error during Medium publication: {str(e)}")
            raise PublishError(f"Failed to publish to Medium: {str(e)}", "medium")