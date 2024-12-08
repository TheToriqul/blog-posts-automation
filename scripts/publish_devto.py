# publish_devto.py
class DevToPublisher:
    """Handles publishing to Dev.to"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = Settings.DEVTO_API_BASE
        self.logger = get_logger(__name__)
        self.headers = {
            'api-key': self.api_key,
            'content-type': 'application/json'
        }
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Dev.to"""
        try:
            post_data = {
                'article': {
                    'title': content['metadata']['title'],
                    'body_markdown': content['content'],
                    'published': False,
                    'tags': content['metadata']['tags']
                }
            }
            
            response = requests.post(
                f"{self.api_base}/articles",
                headers=self.headers,
                json=post_data
            )
            
            if response.status_code != 201:
                raise PublishError(f"Failed to publish to Dev.to: {response.text}", "dev.to")
            
            return response.json()
            
        except Exception as e:
            raise PublishError(str(e), "dev.to")