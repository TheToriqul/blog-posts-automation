# convert_markdown.py
from pathlib import Path
import frontmatter
import markdown2
import json
from typing import Dict, Any, List
from .utils.logger import get_logger
from .utils.exceptions import ConversionError
from .utils.validators import validate_frontmatter

class MarkdownConverter:
    """Converts markdown posts to HTML/JSON with metadata"""
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.logger = get_logger(__name__)
        
    def _process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single markdown file"""
        try:
            post = frontmatter.load(file_path)
            validate_frontmatter(post.metadata)
            
            # Convert tags to list if string
            if isinstance(post.metadata['tags'], str):
                post.metadata['tags'] = [tag.strip() for tag in post.metadata['tags'].split(',')]
            
            # Convert content to HTML
            html_content = markdown2.markdown(
                post.content,
                extras=['fenced-code-blocks', 'tables', 'metadata']
            )
            
            return {
                'metadata': post.metadata,
                'content': html_content,
                'original_file': file_path.name
            }
            
        except Exception as e:
            raise ConversionError(f"Error converting {file_path}: {str(e)}", str(file_path))
    
    def convert(self) -> List[Dict[str, Any]]:
        """Convert all markdown files in the input directory"""
        self.logger.info(f"Starting conversion from {self.input_dir}")
        converted_posts = []
        
        for md_file in self.input_dir.glob('*.md'):
            try:
                self.logger.info(f"Converting {md_file}")
                converted = self._process_file(md_file)
                
                # Save to output directory
                output_file = self.output_dir / f"{md_file.stem}.json"
                with output_file.open('w') as f:
                    json.dump(converted, f, indent=2)
                
                converted_posts.append(converted)
                self.logger.info(f"Successfully converted {md_file}")
                
            except ConversionError as e:
                self.logger.error(f"Failed to convert {e.file_path}: {e.message}")
                continue
            
        return converted_posts