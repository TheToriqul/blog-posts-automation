import requests
from typing import Dict, Any
import json
import time
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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        self._user_id = None
    
    def _get_user_id(self) -> str:
        if self._user_id:
            return self._user_id
            
        try:
            self.logger.info("Fetching Medium user ID...")
            response = requests.get(
                f"{self.api_base}/me",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self._user_id = data['data']['id']
                self.logger.info(f"Successfully got Medium user ID: {self._user_id}")
                return self._user_id
            else:
                raise PublishError(f"Failed to get Medium user ID. Status: {response.status_code}", "medium")
                
        except Exception as e:
            self.logger.error(f"Error getting Medium user ID: {str(e)}")
            raise
    
    def _prepare_content(self, content: Dict[str, Any], publish_status: str = 'public') -> Dict[str, Any]:
        """Prepare content for Medium API with publication status"""
        tags = content['metadata'].get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        elif not isinstance(tags, list):
            tags = []
            
        title = content['metadata'].get('title', '').strip()
        html_content = content.get('content', '').strip()
        
        if not title:
            raise PublishError("Post title is required", "medium")
        if not html_content:
            raise PublishError("Post content is required", "medium")
            
        return {
            'title': title,
            'contentFormat': 'html',
            'content': html_content,
            'tags': tags[:5],
            'publishStatus': publish_status,  # 'public' for direct publishing
            'notifyFollowers': True  # Enable notifications for published posts
        }
    
    def publish(self, content: Dict[str, Any], publish_status: str = 'public') -> Dict[str, Any]:
        """
        Publish content to Medium
        
        Args:
            content (Dict[str, Any]): The content to publish
            publish_status (str): 'public', 'draft', or 'unlisted'
        """
        try:
            user_id = self._get_user_id()
            
            self.logger.info(f"Preparing post: {content['metadata'].get('title', 'Untitled')}")
            self.logger.info(f"Publication status: {publish_status}")
            
            post_data = self._prepare_content(content, publish_status)
            
            # Add a small delay to avoid rate limits
            time.sleep(1)
            
            self.logger.info("Attempting to publish to Medium...")
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data,
                timeout=15
            )
            
            self.logger.info(f"Medium API Response Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                post_url = result.get('data', {}).get('url', 'URL not available')
                self.logger.info(f"Successfully published to Medium. Post URL: {post_url}")
                return result
            else:
                self.logger.error(f"Failed to publish. Response: {response.text}")
                raise PublishError(f"Failed to publish to Medium. Status: {response.status_code}", "medium")
                
        except Exception as e:
            self.logger.error(f"Error during Medium publication: {str(e)}")
            raise PublishError(f"Failed to publish to Medium: {str(e)}", "medium")