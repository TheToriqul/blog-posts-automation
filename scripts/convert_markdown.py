# scripts/convert_markdown.py
from pathlib import Path
import frontmatter
import markdown2
import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.exceptions import ConversionError
from utils.validators import validate_frontmatter

class MarkdownConverter:
    """Converts markdown posts to HTML/JSON with metadata"""
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.logger = get_logger(__name__)