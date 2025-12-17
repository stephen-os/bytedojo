"""
Repository management for .dojo directories.

Handles checking for .dojo existence, initialization status, etc.
"""

from pathlib import Path
from typing import Optional
from textwrap import dedent

from bytedojo.core.database import create_database_schema


class DojoRepository:
    """Manages .dojo repository operations."""
    
    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize repository manager.
        
        Args:
            root_dir: Root directory to search for .dojo. Defaults to cwd.
        """
        self.root_dir = root_dir or Path.cwd()
        self.dojo_dir = self.root_dir / ".dojo"
        self.db_path = self.dojo_dir / "db.sqlite"
        self.problems_dir = self.root_dir / "problems"
    
    def exists(self) -> bool:
        """Check if .dojo directory exists."""
        return self.dojo_dir.exists()
    
    def is_initialized(self) -> bool:
        """Check if .dojo is properly initialized with database."""
        return self.exists() and self.db_path.exists()
    
    def get_db_path(self) -> Path:
        """Get path to database file."""
        if not self.is_initialized():
            raise RuntimeError("Repository not initialized. Run 'dojo init' first.")
        return self.db_path
    
    def initialize(self, force: bool = False):
        """
        Initialize the repository.
        
        Args:
            force: If True, reinitialize even if exists
        """
        if self.exists() and not force:
            raise RuntimeError("Repository already initialized")
        
        # Create directories
        self.dojo_dir.mkdir(exist_ok=True)
        self.problems_dir.mkdir(exist_ok=True)
        
        # Create database
        create_database_schema(self.db_path)
        
        # Create .gitignore
        self._create_gitignore()
        
        # Create README
        self._create_readme()
    
    def _create_gitignore(self):
        """Create .gitignore for the .dojo directory."""
        gitignore = self.dojo_dir / ".gitignore"
        
        content = dedent("""
            # Python
            __pycache__/
            *.pyc
            *.pyo
            *.pyd
            .Python
            
            # IDE
            .vscode/
            .idea/
            *.swp
            *.swo
            
            # OS
            .DS_Store
            Thumbs.db
            
            # ByteDojo
            logs/
            *.log
        """).strip()
        
        gitignore.write_text(content, encoding='utf-8')
    
    def _create_readme(self):
        """Create README in .dojo directory."""
        readme = self.dojo_dir / "README.md"
        
        content = dedent("""
            # ByteDojo Repository
            
            This directory contains your ByteDojo data:
            
            ## Structure
```
            .dojo/
            ├── db.sqlite          # Problem tracking database
            ├── logs/              # Debug logs (created in --debug mode)
            ├── .gitignore         # Git ignore rules
            └── README.md          # This file
```
            
            ## Database Schema
            
            - **problems**: Fetched problems and metadata
            - **attempts**: Your solution attempts and results
            - **reviews**: Spaced repetition schedule
            - **stats**: Daily statistics
            - **config**: Repository preferences
            
            ## Usage
```bash
            # Fetch problems
            dojo leetcode fetch 1
            
            # Run tests
            dojo test
            
            # View stats
            dojo stats
```
            
            ## Tip
            
            You can commit the `.dojo/` directory to track your progress across machines.
            Just make sure to add `.dojo/logs/` to your `.gitignore` if you don't want to commit logs.
        """).strip()
        
        readme.write_text(content, encoding='utf-8')