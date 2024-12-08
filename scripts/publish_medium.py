import requests
from typing import Dict, Any
import json
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
        """Get Medium user ID with enhanced error handling and logging"""
        try:
            self.logger.info("Attempting to fetch Medium user ID...")
            self.logger.debug(f"Request headers: {self.headers}")
            
            response = requests.get(
                f"{self.api_base}/me", 
                headers=self.headers,
                timeout=10
            )
            
            self.logger.info(f"Medium /me endpoint response status: {response.status_code}")
            self.logger.debug(f"Medium /me endpoint response: {response.text}")
            
            if response.status_code == 401:
                self.logger.error("Medium authentication failed. Please check your token.")
                raise PublishError("Invalid Medium token. Please check your authentication.", "medium")
            
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data or 'id' not in data['data']:
                self.logger.error(f"Unexpected Medium API response format: {data}")
                raise PublishError("Invalid response format from Medium API", "medium")
            
            user_id = data['data']['id']
            self.logger.info(f"Successfully retrieved Medium user ID: {user_id}")
            return user_id
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed when getting Medium user ID: {str(e)}")
            raise PublishError(f"Failed to get Medium user ID: {str(e)}", "medium")
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Medium with enhanced error handling and logging"""
        if not self.token:
            self.logger.error("Medium token is not provided")
            raise PublishError("Medium token is not provided", "medium")
        
        try:
            user_id = self._get_user_id()
            
            # Format tags properly
            tags = content['metadata'].get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            
            # Clean and prepare content
            title = content['metadata'].get('title', '').strip()
            html_content = content.get('content', '').strip()
            
            if not title:
                raise PublishError("Post title is required", "medium")
            if not html_content:
                raise PublishError("Post content is required", "medium")
            
            # Ensure content is properly formatted
            post_data = {
                'title': title,
                'contentFormat': 'html',
                'content': html_content,
                'tags': tags[:5],  # Medium allows max 5 tags
                'publishStatus': 'draft'
            }
            
            self.logger.info(f"Attempting to publish to Medium with title: {title}")
            self.logger.debug(f"Post data: {json.dumps(post_data, indent=2)}")
            
            response = requests.post(
                f"{self.api_base}/users/{user_id}/posts",
                headers=self.headers,
                json=post_data,
                timeout=15  # Increased timeout
            )
            
            self.logger.info(f"Medium publish response status: {response.status_code}")
            self.logger.debug(f"Medium publish response: {response.text}")
            
            if response.status_code == 401:
                raise PublishError("Invalid Medium token", "medium")
            elif response.status_code == 400:
                error_msg = f"Medium API rejected the request: {response.text}"
                self.logger.error(error_msg)
                raise PublishError(error_msg, "medium")
            elif response.status_code != 201:
                error_msg = f"Failed to publish to Medium: {response.text}"
                self.logger.error(error_msg)
                raise PublishError(error_msg, "medium")
            
            result = response.json()
            self.logger.info(f"Successfully published to Medium. Post URL: {result.get('data', {}).get('url', 'URL not available')}")
            return result
            
        except Exception as e:
            error_msg = f"Error during Medium publication: {str(e)}"
            self.logger.error(error_msg)
            raise PublishError(error_msg, "medium")