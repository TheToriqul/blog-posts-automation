import requests
import time
from typing import Dict, Any
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
            'Accept': 'application/json'
        }
        self._user_id = None
    
    def _get_user_id(self) -> str:
        """Get or fetch Medium user ID"""
        if not self._user_id:
            try:
                response = requests.get(
                    f"{self.api_base}/me",
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    self._user_id = response.json()['data']['id']
                else:
                    raise PublishError(f"Failed to get user ID: {response.text}", "medium")
            except Exception as e:
                raise PublishError(f"Error getting user ID: {str(e)}", "medium")
        return self._user_id
    
    def _prepare_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for Medium API"""
        # Get tags
        tags = content['metadata'].get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Prepare content with proper formatting for Medium
        return {
            'title': content['metadata']['title'],
            'contentFormat': 'html',
            'content': content['content'],
            'tags': tags[:5],  # Medium allows up to 5 tags
            'publishStatus': 'public'
        }
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Medium with proper error handling"""
        try:
            # Get user ID first
            user_id = self._get_user_id()
            self.logger.info(f"Publishing to Medium with user ID: {user_id}")
            
            # Prepare content
            post_data = self._prepare_content(content)
            self.logger.debug(f"Prepared Medium content: {post_data}")
            
            # Attempt publication
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            
            self.logger.info(f"Medium API Response Status: {response.status_code}")
            self.logger.debug(f"Medium API Response: {response.text}")
            
            if response.status_code == 201:
                result = response.json()
                self.logger.info(f"Successfully published to Medium: {result['data']['url']}")
                return result
            else:
                error_msg = f"Failed to publish to Medium. Status: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f" Details: {error_details}"
                except:
                    pass
                raise PublishError(error_msg, "medium")
                
        except Exception as e:
            raise PublishError(f"Error during Medium publication: {str(e)}", "medium")