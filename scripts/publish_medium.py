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
        self.retry_after = 0
    
    def _should_retry(self, response: requests.Response) -> bool:
        """Check if we should retry based on rate limit headers"""
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 3600))
            self.retry_after = time.time() + retry_after
            return True
        return False
    
    def publish(self, content: Dict[str, Any], publish_status: str = 'public') -> Dict[str, Any]:
        """Publish content to Medium with rate limit handling"""
        try:
            # Check if we're still rate limited
            if time.time() < self.retry_after:
                wait_time = int(self.retry_after - time.time())
                raise PublishError(
                    f"Rate limited. Please wait {wait_time} seconds before retrying.",
                    "medium"
                )
            
            # Prepare content
            self.logger.info(f"Preparing post: {content['metadata'].get('title')}")
            
            response = requests.post(
                f"{self.api_base}/users/{self._user_id}/posts",
                headers=self.headers,
                json=content,
                timeout=30
            )
            
            if self._should_retry(response):
                raise PublishError(
                    f"Rate limited. Please wait {int(self.retry_after - time.time())} seconds.",
                    "medium"
                )
            
            if response.status_code == 201:
                result = response.json()
                self.logger.info(f"Successfully published to Medium. URL: {result['data']['url']}")
                return result
            else:
                raise PublishError(f"Failed to publish to Medium. Status: {response.status_code}", "medium")
                
        except Exception as e:
            raise PublishError(f"Error during Medium publication: {str(e)}", "medium")