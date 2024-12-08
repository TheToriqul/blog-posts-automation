import requests
import logging
import json
import base64
import mimetypes
import os
import time
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

class PublishError(Exception):
    def __init__(self, message: str, platform: str):
        self.message = message
        self.platform = platform
        super().__init__(self.message)

class MediumPublisher:
    def __init__(self, token: str):
        self.token = self._format_token(token)
        self.api_base = "https://api.medium.com/v1"
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self._user_id = None
        
        # Updated headers
        self.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.session.headers.update(self.headers)

    def _format_token(self, token: str) -> str:
        """Ensure token is properly formatted"""
        token = token.strip()
        if not token.startswith(('Bearer ', 'Token ')):
            return f'Bearer {token}'
        return token

    def _get_user_id(self) -> str:
        """Get the authenticated user's id"""
        try:
            response = self.session.get(
                f"{self.api_base}/me",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['id']
            else:
                self.logger.error(f"Failed to get user ID. Response: {response.text}")
                raise PublishError(f"Failed to get Medium user ID. Status: {response.status_code}", "medium")
                
        except Exception as e:
            self.logger.error(f"Error getting Medium user ID: {str(e)}")
            raise PublishError(f"Failed to get Medium user ID: {str(e)}", "medium")

    def _upload_image_to_medium(self, image_path: str) -> str:
        """Upload an image to Medium"""
        try:
            self.logger.info(f"Attempting to upload image: {image_path}")
            
            if not os.path.exists(image_path):
                raise PublishError(f"Image file not found: {image_path}", "medium")
            
            # Read image file
            with open(image_path, 'rb') as img_file:
                files = {
                    'image': (os.path.basename(image_path), img_file, 'image/jpeg')
                }
                
                # Remove Content-Type from headers for multipart upload
                headers = self.headers.copy()
                headers.pop('Content-Type', None)
                
                response = self.session.post(
                    f"{self.api_base}/images",
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 201:
                    data = response.json()
                    image_url = data['data']['url']
                    self.logger.info(f"Successfully uploaded image: {image_url}")
                    return image_url
                else:
                    self.logger.error(f"Upload failed. Response: {response.text}")
                    raise PublishError(f"Failed to upload image. Status: {response.status_code}", "medium")
                    
        except Exception as e:
            self.logger.error(f"Error uploading image: {str(e)}")
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
                    
                if not src.startswith(('http://', 'https://')):
                    image_path = os.path.join(base_path, src)
                    image_path = os.path.abspath(image_path)
                    
                    if os.path.exists(image_path):
                        try:
                            medium_url = self._upload_image_to_medium(str(image_path))
                            img['src'] = medium_url
                        except PublishError as e:
                            self.logger.warning(f"Skipping image {image_path}: {str(e)}")
                            continue
                    else:
                        self.logger.warning(f"Image not found: {image_path}")
            
            return str(soup)
            
        except Exception as e:
            self.logger.error(f"Error processing images: {str(e)}")
            raise PublishError(f"Image processing failed: {str(e)}", "medium")

    def publish(self, content: Dict[str, Any], publish_status: str = 'public') -> Dict[str, Any]:
        """Publish content to Medium"""
        try:
            if not self._user_id:
                self._user_id = self._get_user_id()
            
            base_path = content.get('metadata', {}).get('image_base_path', './posts')
            processed_content = self._process_images(content['content'], base_path)
            
            # Format tags
            tags = content['metadata'].get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            
            # Only include supported fields
            post_data = {
                'title': content['metadata']['title'],
                'contentFormat': 'html',
                'content': processed_content,
                'tags': tags[:5],
                'publishStatus': publish_status
            }
            
            self.logger.info(f"Publishing to Medium: {content['metadata']['title']}")
            response = self.session.post(
                f"{self.api_base}/users/{self._user_id}/posts",
                json=post_data,
                timeout=15
            )
            
            if response.status_code == 201:
                result = response.json()
                post_url = result.get('data', {}).get('url', 'URL not available')
                self.logger.info(f"Successfully published to Medium: {post_url}")
                return result
            else:
                self.logger.error(f"Publication failed. Response: {response.text}")
                raise PublishError(f"Failed to publish to Medium. Status: {response.status_code}", "medium")
                
        except Exception as e:
            self.logger.error(f"Error during Medium publication: {str(e)}")
            raise PublishError(f"Failed to publish to Medium: {str(e)}", "medium")