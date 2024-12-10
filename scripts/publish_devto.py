import requests
import re
from typing import Dict, Any, List
from .utils.logger import get_logger
from .utils.exceptions import PublishError

class DevToPublisher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = "https://dev.to/api"
        self.logger = get_logger(__name__)
        self.headers = {
            'api-key': self.api_key,
            'content-type': 'application/json'
        }
    
    def _clean_tag(self, tag: str) -> str:
        """Clean tag to meet Dev.to requirements"""
        # Remove special characters including underscores
        clean = re.sub(r'[^\w\s]', '', tag)
        # Replace spaces with hyphens
        clean = clean.replace('_', '').replace(' ', '-').lower()
        # Ensure it's not empty
        return clean if clean else 'uncategorized'
    
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
        
        # Clean each tag
        processed_tags = []
        for tag in tags:
            cleaned_tag = self._clean_tag(tag)
            if cleaned_tag and cleaned_tag not in processed_tags:
                processed_tags.append(cleaned_tag)
        
        # Ensure we have at least one tag
        if not processed_tags:
            processed_tags = ['programming']
        
        # Limit to 4 tags
        processed_tags = processed_tags[:4]
        
        self.logger.info(f"Processed tags: {processed_tags}")
        
        # Add front matter
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
                'tags': processed_tags
            }
        }
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Dev.to with improved error handling"""
        try:
            self.logger.info("Preparing content for Dev.to publication...")
            post_data = self._prepare_content(content)
            
            self.logger.info(f"Publishing with tags: {post_data['article']['tags']}")
            
            response = requests.post(
                f"{self.api_base}/articles",
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            
            self.logger.info(f"Dev.to API Response Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                self.logger.info(f"Successfully published to Dev.to. URL: {result.get('url')}")
                return result
            elif response.status_code == 422:
                error_msg = response.json().get('error', 'Unknown validation error')
                raise PublishError(f"Dev.to validation error: {error_msg}", "dev.to")
            else:
                raise PublishError(f"Failed to publish to Dev.to: {response.text}", "dev.to")
                
        except Exception as e:
            raise PublishError(f"Error during Dev.to publication: {str(e)}", "dev.to")