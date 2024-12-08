import requests
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
    
    def _get_user_id(self) -> str:
        """Get Medium user ID with better error handling"""
        try:
            response = requests.get(
                f"{self.api_base}/me", 
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data or 'id' not in data['data']:
                raise PublishError("Invalid response format from Medium API", "medium")
                
            return data['data']['id']
            
        except requests.exceptions.RequestException as e:
            raise PublishError(f"Failed to get Medium user ID: {str(e)}", "medium")
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Medium with improved error handling and content formatting"""
        if not self.token:
            raise PublishError("Medium token is not provided", "medium")
        
        try:
            user_id = self._get_user_id()
            
            # Format tags properly
            tags = content['metadata'].get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            
            # Ensure content is properly formatted
            post_data = {
                'title': content['metadata']['title'],
                'contentFormat': 'html',
                'content': content['content'],
                'tags': tags[:5],  # Medium allows max 5 tags
                'publishStatus': 'draft',
                'notifyFollowers': False
            }
            
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data,
                timeout=10
            )
            
            self.logger.info(f"Medium API Response: {response.status_code} - {response.text}")
            
            if response.status_code == 401:
                raise PublishError("Invalid Medium token", "medium")
            elif response.status_code != 201:
                raise PublishError(f"Failed to publish to Medium: {response.text}", "medium")
            
            return response.json()
            
        except Exception as e:
            raise PublishError(f"Error during Medium publication: {str(e)}", "medium")