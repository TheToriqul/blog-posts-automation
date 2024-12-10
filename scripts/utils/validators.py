from typing import Dict, Any, List
from .exceptions import ValidationError

def validate_frontmatter(metadata: Dict[str, Any]) -> bool:
    """
    Validate post frontmatter metadata
    
    Args:
        metadata: Dictionary containing post metadata
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['title']
    optional_fields = ['description', 'tags', 'canonical_url', 'series']
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in metadata]
    if missing_fields:
        raise ValidationError(
            f"Missing required frontmatter fields: {', '.join(missing_fields)}",
            {'missing_fields': missing_fields}
        )
    
    # Validate title
    if not metadata['title'] or not isinstance(metadata['title'], str):
        raise ValidationError("Title must be a non-empty string")
    
    # Validate tags if present
    tags = metadata.get('tags', [])
    if tags:
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        elif not isinstance(tags, (list, tuple)):
            raise ValidationError("Tags must be a string or list")
    
    # Validate URLs if present
    if 'canonical_url' in metadata and not isinstance(metadata['canonical_url'], str):
        raise ValidationError("Canonical URL must be a string")
    
    return True

def validate_html_content(content: str) -> bool:
    """
    Basic validation of HTML content
    
    Args:
        content: HTML content string
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not content or not isinstance(content, str):
        raise ValidationError("Content must be a non-empty string")
    
    # Basic HTML structure checks
    if not content.strip().startswith('<'):
        raise ValidationError("Content does not appear to be HTML")
    
    # Check for basic required tags
    required_tags = ['<p>', '<h1>', '<h2>']
    if not any(tag in content.lower() for tag in required_tags):
        raise ValidationError(
            "Content missing basic HTML structure",
            {'required_tags': required_tags}
        )
    
    return True

def validate_publication_data(data: Dict[str, Any], platform: str) -> bool:
    """
    Validate data before publication
    
    Args:
        data: Publication data dictionary
        platform: Target platform
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    required_fields = {
        'medium': ['title', 'content'],
        'devto': ['title', 'body_markdown']
    }
    
    if platform not in required_fields:
        raise ValidationError(f"Unsupported platform: {platform}")
    
    # Check required fields for the platform
    fields = required_fields[platform]
    missing_fields = [field for field in fields if field not in data]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields for {platform}: {', '.join(missing_fields)}",
            {'missing_fields': missing_fields}
        )
    
    return True