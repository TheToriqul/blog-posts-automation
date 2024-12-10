class PublishError(Exception):
    """Base exception for publishing errors"""
    def __init__(self, message: str, platform: str):
        self.platform = platform
        super().__init__(message)

class ConversionError(Exception):
    """Exception raised when markdown conversion fails"""
    def __init__(self, message: str, file_path: str):
        self.file_path = file_path
        super().__init__(message)

class ValidationError(Exception):
    """Exception raised when content validation fails"""
    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)

class TrackingError(Exception):
    """Exception raised when tracking operations fail"""
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        super().__init__(message)

class RateLimitError(PublishError):
    """Exception raised when hitting platform rate limits"""
    def __init__(self, platform: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit reached for {platform}", platform)

class AuthenticationError(PublishError):
    """Exception raised when authentication fails"""
    def __init__(self, platform: str):
        super().__init__(f"Authentication failed for {platform}", platform)

class NetworkError(PublishError):
    """Exception raised when network operations fail"""
    def __init__(self, platform: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(f"Network error for {platform}", platform)

class QueueError(Exception):
    """Raised when queue operations fail"""
    def __init__(self, message: str, operation: str = None):
        self.operation = operation
        super().__init__(message)