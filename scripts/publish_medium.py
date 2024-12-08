# publish_medium.py
import requests
import time
from typing import Dict, Any
from .utils.logger import get_logger
from .utils.exceptions import PublishError
from .config.settings import Settings

class MediumPublisher:
    """Handles publishing to Medium"""
    def __init__(self, token: str):
        self.token = token
        self.api_base = Settings.MEDIUM_API_BASE
        self.logger = get_logger(__name__)
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _get_user_id(self) -> str:
        """Get Medium user ID"""
        response = requests.get(f"{self.api_base}/me", headers=self.headers)
        if response.status_code != 200:
            raise PublishError("Failed to get Medium user ID", "medium")
        return response.json()['data']['id']
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Medium"""
        try:
            user_id = self._get_user_id()
            
            post_data = {
                'title': content['metadata']['title'],
                'contentFormat': 'html',
                'content': content['content'],
                'tags': content['metadata']['tags'],
                'publishStatus': 'draft'
            }
            
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data
            )
            
            if response.status_code != 201:
                raise PublishError(f"Failed to publish to Medium: {response.text}", "medium")
            
            return response.json()
            
        except Exception as e:
            raise PublishError(str(e), "medium")

