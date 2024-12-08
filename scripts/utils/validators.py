# utils/validators.py
from typing import Dict, Any

def validate_frontmatter(metadata: Dict[str, Any]) -> bool:
    """Validates required frontmatter fields"""
    required_fields = ['title', 'description', 'tags']
    
    if not all(field in metadata for field in required_fields):
        missing = [field for field in required_fields if field not in metadata]
        raise ValidationError(f"Missing required frontmatter fields: {', '.join(missing)}")
    
    if not isinstance(metadata['tags'], (list, str)):
        raise ValidationError("Tags must be either a string or list")
    
    return True