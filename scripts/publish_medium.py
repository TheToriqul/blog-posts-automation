import requests
import time
from typing import Dict, Any
from .utils.logger import get_logger
from .utils.exceptions import PublishError

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
                    self.logger.info(f"Successfully got Medium user ID: {self._user_id}")
                else:
                    raise PublishError(f"Failed to get user ID: {response.text}", "medium")
            except Exception as e:
                raise PublishError(f"Error getting user ID: {str(e)}", "medium")
        return self._user_id
    
    def _prepare_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for Medium API"""
        # Process tags
        tags = content['metadata'].get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Ensure we have the required fields
        if 'title' not in content['metadata']:
            raise PublishError("Post title is required", "medium")
        
        # Format content for Medium
        post_data = {
            'title': content['metadata']['title'],
            'contentFormat': 'html',
            'content': content['content'],
            'publishStatus': 'public',  # Always publish as public
            'notifyFollowers': True,    # Notify followers about the new post
            'tags': tags[:5]            # Medium allows up to 5 tags
        }
        
        # Add canonical URL if available
        if 'canonical_url' in content['metadata']:
            post_data['canonicalUrl'] = content['metadata']['canonical_url']
        
        # Add license if specified
        if 'license' in content['metadata']:
            post_data['license'] = content['metadata']['license']
        
        self.logger.info(f"Preparing Medium post: {post_data['title']} (public)")
        return post_data
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Medium"""
        try:
            # Get user ID
            user_id = self._get_user_id()
            
            # Prepare post content
            post_data = self._prepare_content(content)
            
            self.logger.info(f"Publishing to Medium as public post: {post_data['title']}")
            
            # Make the API request
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            
            self.logger.info(f"Medium API Response Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                post_url = result['data']['url']
                self.logger.info(f"Successfully published to Medium: {post_url}")
                return result
            elif response.status_code == 429:
                raise PublishError("Rate limit reached. Please try again tomorrow.", "medium")
            else:
                error_msg = "Failed to publish to Medium"
                try:
                    error_details = response.json()
                    error_msg += f". Details: {error_details}"
                except:
                    error_msg += f". Status: {response.status_code}"
                raise PublishError(error_msg, "medium")
                
        except Exception as e:
            raise PublishError(f"Error during Medium publication: {str(e)}", "medium")