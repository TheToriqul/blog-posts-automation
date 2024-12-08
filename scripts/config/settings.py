# config/settings.py
from pathlib import Path
import os

class Settings:
    """Configuration management"""
    # API Tokens
    MEDIUM_TOKEN = os.environ.get("MEDIUM_TOKEN")
    DEVTO_API_KEY = os.environ.get("DEVTO_API_KEY")
    
    # Directories
    BASE_DIR = Path(__file__).parent.parent.parent
    MARKDOWN_DIR = Path(os.environ.get("MARKDOWN_DIR", BASE_DIR / "posts"))
    OUTPUT_DIR = Path(os.environ.get("HTML_OUTPUT_DIR", BASE_DIR / "dist"))
    
    # API Endpoints
    MEDIUM_API_BASE = "https://api.medium.com/v1"
    DEVTO_API_BASE = "https://dev.to/api"
    
    # Rate Limiting
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    @classmethod
    def validate_config(cls):
        """Validates that all required configuration is present"""
        if not cls.MEDIUM_TOKEN:
            raise ValueError("MEDIUM_TOKEN environment variable is required")
        if not cls.DEVTO_API_KEY:
            raise ValueError("DEVTO_API_KEY environment variable is required")
        
        # Ensure directories exist
        cls.MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)