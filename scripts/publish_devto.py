import requests
from typing import Dict, Any
from utils.logger import get_logger
from utils.exceptions import PublishError

class DevToPublisher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = "https://dev.to/api"
        self.logger = get_logger(__name__)
        self.headers = {
            'api-key': self.api_key,
            'content-type': 'application/json'
        }
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Dev.to with improved handling"""
        try:
            # Format tags properly
            tags = content['metadata'].get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            
            post_data = {
                'article': {
                    'title': content['metadata']['title'],
                    'body_markdown': content['content'],
                    'published': True,  # Changed to True to publish immediately
                    'tags': tags
                }
            }
            
            response = requests.post(
                f"{self.api_base}/articles",
                headers=self.headers,
                json=post_data,
                timeout=10
            )
            
            self.logger.info(f"Dev.to API Response: {response.status_code} - {response.text}")
            
            if response.status_code == 401:
                raise PublishError("Invalid Dev.to API key", "dev.to")
            elif response.status_code != 201:
                raise PublishError(f"Failed to publish to Dev.to: {response.text}", "dev.to")
            
            return response.json()
            
        except Exception as e:
            raise PublishError(f"Error during Dev.to publication: {str(e)}", "dev.to")