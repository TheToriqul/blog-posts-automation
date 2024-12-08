# scripts/publish_medium.py
import requests
from typing import Dict, Any
from utils.logger import get_logger
from utils.exceptions import PublishError
from config.settings import Settings

class MediumPublisher:
    """Handles publishing to Medium"""
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.medium.com/v1"
        self.logger = get_logger(__name__)
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _get_user_id(self) -> str:
        """Get Medium user ID"""
        try:
            self.logger.info("Getting Medium user ID...")
            response = requests.get(f"{self.api_base}/me", headers=self.headers)
            
            self.logger.info(f"Medium API Response Status: {response.status_code}")
            self.logger.info(f"Medium API Response: {response.text}")
            
            if response.status_code != 200:
                error_msg = f"Failed to get Medium user ID. Status: {response.status_code}, Response: {response.text}"
                self.logger.error(error_msg)
                raise PublishError(error_msg, "medium")
                
            data = response.json()
            if 'data' not in data or 'id' not in data['data']:
                error_msg = "Invalid response format from Medium API"
                self.logger.error(error_msg)
                raise PublishError(error_msg, "medium")
                
            return data['data']['id']
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while getting Medium user ID: {str(e)}"
            self.logger.error(error_msg)
            raise PublishError(error_msg, "medium")
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Medium"""
        try:
            self.logger.info("Starting Medium publication process...")
            
            if not self.token:
                raise PublishError("Medium token is not set", "medium")
            
            user_id = self._get_user_id()
            self.logger.info(f"Got Medium user ID: {user_id}")
            
            post_data = {
                'title': content['metadata']['title'],
                'contentFormat': 'html',
                'content': content['content'],
                'tags': content['metadata']['tags'],
                'publishStatus': 'draft'
            }
            
            self.logger.info("Sending post to Medium...")
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data
            )
            
            self.logger.info(f"Medium publish response status: {response.status_code}")
            self.logger.info(f"Medium publish response: {response.text}")
            
            if response.status_code != 201:
                error_msg = f"Failed to publish to Medium: {response.text}"
                self.logger.error(error_msg)
                raise PublishError(error_msg, "medium")
            
            return response.json()
            
        except Exception as e:
            error_msg = f"Error during Medium publication: {str(e)}"
            self.logger.error(error_msg)
            raise PublishError(error_msg, "medium")