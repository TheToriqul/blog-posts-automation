from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Configuration management for blog automation"""
    
    # API Credentials
    MEDIUM_TOKEN: str = os.getenv("MEDIUM_TOKEN")
    DEVTO_API_KEY: str = os.getenv("DEVTO_API_KEY")
    
    # Directory Configuration
    MARKDOWN_DIR: Path = Path(os.getenv("MARKDOWN_DIR", "./posts"))
    OUTPUT_DIR: Path = Path(os.getenv("HTML_OUTPUT_DIR", "./dist"))
    
    # Publishing Configuration
    PUBLISH_STATUS: str = os.getenv("PUBLISH_STATUS", "public")  # public, draft
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))  # seconds
    
    # Schedule Configuration
    SCHEDULE_TIMES: list = [
        {'hour': 13, 'days': [1, 3]},  # Tuesday, Thursday
        {'hour': 15, 'days': [5]}      # Saturday
    ]
    
    # Content Configuration
    DEFAULT_TAGS: list = ['programming', 'technology']
    MAX_TAGS: int = 4
    CANONICAL_URL_REQUIRED: bool = False
    
    # Rate Limiting
    RATE_LIMIT_DELAY: int = int(os.getenv("RATE_LIMIT_DELAY", "60"))  # seconds
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "./logs"))
    
    @classmethod
    def validate(cls) -> Optional[Dict[str, str]]:
        """
        Validate required settings
        
        Returns:
            Dict of missing/invalid settings if any, None if all valid
        """
        missing = {}
        
        # Check required credentials
        if not cls.MEDIUM_TOKEN:
            missing['MEDIUM_TOKEN'] = "Missing Medium API token"
        if not cls.DEVTO_API_KEY:
            missing['DEVTO_API_KEY'] = "Missing Dev.to API key"
        
        # Check directories
        if not cls.MARKDOWN_DIR.exists():
            missing['MARKDOWN_DIR'] = f"Directory does not exist: {cls.MARKDOWN_DIR}"
        if not cls.OUTPUT_DIR.parent.exists():
            missing['OUTPUT_DIR'] = f"Parent directory does not exist: {cls.OUTPUT_DIR.parent}"
        
        return missing if missing else None
    
    @classmethod
    def load_custom_config(cls, config_file: str):
        """
        Load custom configuration from JSON file
        
        Args:
            config_file: Path to JSON configuration file
        """
        if Path(config_file).exists():
            with open(config_file, 'r') as f:
                custom_config = json.load(f)
                for key, value in custom_config.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
    
    @classmethod
    def get_platform_config(cls, platform: str) -> Dict[str, Any]:
        """
        Get platform-specific configuration
        
        Args:
            platform: Platform name ('medium' or 'devto')
            
        Returns:
            Dictionary of platform-specific settings
        """
        platform_config = {
            'medium': {
                'api_token': cls.MEDIUM_TOKEN,
                'api_base': "https://api.medium.com/v1",
                'max_tags': 5,
                'publish_status': cls.PUBLISH_STATUS,
            },
            'devto': {
                'api_key': cls.DEVTO_API_KEY,
                'api_base': "https://dev.to/api",
                'max_tags': 4,
                'publish_status': 'published',  # Dev.to only supports published state
            }
        }
        
        return platform_config.get(platform, {})
    
    @classmethod
    def initialize(cls):
        """
        Initialize settings and create required directories
        """
        # Create required directories
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Validate settings
        if issues := cls.validate():
            issues_str = "\n".join(f"- {k}: {v}" for k, v in issues.items())
            raise ValueError(f"Invalid configuration:\n{issues_str}")