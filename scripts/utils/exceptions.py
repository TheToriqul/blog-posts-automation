# utils/exceptions.py
class ConversionError(Exception):
    """Raised when markdown conversion fails"""
    def __init__(self, message: str, file_path: str = None):
        self.message = message
        self.file_path = file_path
        super().__init__(self.message)

class PublishError(Exception):
    """Raised when publishing fails"""
    def __init__(self, message: str, platform: str = None):
        self.message = message
        self.platform = platform
        super().__init__(self.message)

class ValidationError(Exception):
    """Raised when validation fails"""
    pass