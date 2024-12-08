import requests
from typing import Dict, Any
import re
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
    
    def _prepare_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content for Dev.to with proper formatting"""
        # Get content and metadata
        html_content = content.get('content', '')
        title = content['metadata'].get('title', '')
        description = content['metadata'].get('description', '')
        
        # Process tags
        tags = content['metadata'].get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Ensure tags meet Dev.to requirements
        processed_tags = []
        for tag in tags:
            # Remove special characters and spaces
            cleaned_tag = re.sub(r'[^\w\s]', '', tag)
            # Replace spaces with underscores
            cleaned_tag = cleaned_tag.replace(' ', '_').lower()
            processed_tags.append(cleaned_tag)
        
        # Limit to 4 tags as per Dev.to requirements
        processed_tags = processed_tags[:4]
        
        # Add front matter for better formatting
        markdown_content = f"""---
title: {title}
published: true
description: {description}
tags: {','.join(processed_tags)}
---

{html_content}
"""
        
        return {
            'article': {
                'title': title,
                'body_markdown': markdown_content,
                'published': True,
                'tags': processed_tags,
                'series': None  # Optional: Add series support if needed
            }
        }
    
    def _validate_content(self, content: Dict[str, Any]) -> None:
        """Validate content meets Dev.to requirements"""
        title = content['metadata'].get('title', '')
        if len(title) > 128:
            raise PublishError("Dev.to title must be less than 128 characters", "dev.to")
        
        if not title:
            raise PublishError("Title is required for Dev.to", "dev.to")
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Dev.to with improved error handling"""
        try:
            self.logger.info("Preparing content for Dev.to publication...")
            
            # Validate content
            self._validate_content(content)
            
            # Prepare content with proper formatting
            post_data = self._prepare_content(content)
            
            self.logger.info("Attempting to publish to Dev.to...")
            response = requests.post(
                f"{self.api_base}/articles",
                headers=self.headers,
                json=post_data,
                timeout=30  # Increased timeout for larger content
            )
            
            self.logger.info(f"Dev.to API Response Status: {response.status_code}")
            self.logger.debug(f"Dev.to API Response: {response.text}")
            
            if response.status_code == 401:
                raise PublishError("Invalid Dev.to API key", "dev.to")
            elif response.status_code == 422:
                raise PublishError(f"Dev.to validation error: {response.text}", "dev.to")
            elif response.status_code != 201:
                raise PublishError(f"Failed to publish to Dev.to: {response.text}", "dev.to")
            
            result = response.json()
            self.logger.info(f"Successfully published to Dev.to. URL: {result.get('url')}")
            return result
            
        except requests.exceptions.Timeout:
            raise PublishError("Timeout while publishing to Dev.to - content may be too large", "dev.to")
        except requests.exceptions.RequestException as e:
            raise PublishError(f"Network error during Dev.to publication: {str(e)}", "dev.to")
        except Exception as e:
            raise PublishError(f"Error during Dev.to publication: {str(e)}", "dev.to")