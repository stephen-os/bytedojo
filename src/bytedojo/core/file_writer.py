from pathlib import Path
from bytedojo.core.logger import get_logger


class FileWriter:
    """Generic file writer."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def write(self, content: str, filepath: Path) -> Path:
        """
        Write content to file.
        
        Args:
            content: File content
            filepath: Full path including filename
            
        Returns:
            Path to created file
        """
        # Create parent directories
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        
        self.logger.debug(f"Wrote file: {filepath}")
        return filepath