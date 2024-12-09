from pathlib import Path
import frontmatter
import markdown2
import json
from typing import Dict, Any, List
from .utils.logger import get_logger
from .utils.exceptions import ConversionError

class MarkdownConverter:
    """Converts markdown posts to HTML/JSON with metadata"""
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.logger = get_logger(__name__)
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def validate_post(self, post: frontmatter.Post, file_path: str) -> None:
        """
        Validate post content and metadata
        
        Args:
            post: Frontmatter post object
            file_path: Path to the markdown file for error reporting
        
        Raises:
            ConversionError: If validation fails
        """
        # Check required fields
        required_fields = ['title', 'description']
        missing_fields = [field for field in required_fields if field not in post.metadata]
        
        if missing_fields:
            raise ConversionError(
                f"Missing required frontmatter fields: {', '.join(missing_fields)}", 
                file_path
            )
        
        # Validate title is not empty
        if not post.metadata['title'].strip():
            raise ConversionError("Title cannot be empty", file_path)
        
        # Validate description is not empty
        if not post.metadata['description'].strip():
            raise ConversionError("Description cannot be empty", file_path)
        
        # Validate content is not empty
        if not post.content.strip():
            raise ConversionError("Post content cannot be empty", file_path)
    
    def process_tags(self, tags: Any) -> List[str]:
        """
        Process and validate tags
        
        Args:
            tags: Tags from frontmatter (string or list)
            
        Returns:
            List of processed tags
        """
        if isinstance(tags, str):
            # Split string tags and clean them
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif isinstance(tags, list):
            # Clean list tags
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        else:
            # Return empty list if no tags
            return []
    
    def convert_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Convert a single markdown file to HTML/JSON
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Dict containing converted content and metadata
            
        Raises:
            ConversionError: If conversion fails
        """
        try:
            self.logger.info(f"Converting single file: {file_path}")
            
            # Ensure input file exists
            if not file_path.exists():
                raise ConversionError(f"Input file does not exist: {file_path}", str(file_path))
            
            # Load frontmatter
            try:
                post = frontmatter.load(file_path)
            except Exception as e:
                raise ConversionError(f"Failed to parse frontmatter: {str(e)}", str(file_path))
            
            # Validate post
            self.validate_post(post, str(file_path))
            
            # Process tags
            post.metadata['tags'] = self.process_tags(post.metadata.get('tags', []))
            
            # Convert content to HTML with extended features
            try:
                html_content = markdown2.markdown(
                    post.content,
                    extras=[
                        'fenced-code-blocks',
                        'tables',
                        'metadata',
                        'strike',
                        'tasklist',
                        'code-friendly'
                    ]
                )
            except Exception as e:
                raise ConversionError(f"Failed to convert markdown to HTML: {str(e)}", str(file_path))
            
            # Create output structure
            converted = {
                'metadata': {
                    'title': post.metadata['title'],
                    'description': post.metadata['description'],
                    'tags': post.metadata['tags'],
                    # Include any additional metadata
                    **{k: v for k, v in post.metadata.items() 
                       if k not in ['title', 'description', 'tags']}
                },
                'content': html_content,
                'original_file': file_path.name,
                'converted_at': datetime.now().isoformat()
            }
            
            # Save to output directory
            output_file = self.output_dir / f"{file_path.stem}.json"
            try:
                with output_file.open('w', encoding='utf-8') as f:
                    json.dump(converted, f, indent=2, ensure_ascii=False)
            except Exception as e:
                raise ConversionError(f"Failed to save converted file: {str(e)}", str(file_path))
            
            self.logger.info(f"Successfully converted {file_path}")
            return converted
            
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"Unexpected error converting {file_path}: {str(e)}", str(file_path))
    
    def convert(self) -> List[Dict[str, Any]]:
        """
        Convert all markdown files in the input directory
        
        Returns:
            List of converted post dictionaries
        """
        self.logger.info(f"Starting conversion from {self.input_dir}")
        converted_posts = []
        
        # Get all markdown files
        markdown_files = list(self.input_dir.glob('*.md'))
        self.logger.info(f"Found {len(markdown_files)} markdown files")
        
        for md_file in markdown_files:
            try:
                converted = self.convert_single_file(md_file)
                converted_posts.append(converted)
                self.logger.info(f"Successfully converted {md_file}")
                
            except ConversionError as e:
                self.logger.error(f"Failed to convert {e.file_path}: {str(e)}")
                continue
                
            except Exception as e:
                self.logger.error(f"Unexpected error with {md_file}: {str(e)}")
                continue
        
        self.logger.info(f"Completed conversion of {len(converted_posts)} posts")
        return converted_posts