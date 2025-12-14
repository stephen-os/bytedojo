"""
Init command - Creates a .dojo directory in the current folder with:
- SQLite database for tracking problems, solutions, and stats
- Configuration file
- Directory structure for problems
"""

import click
import sqlite3
from pathlib import Path
from datetime import datetime
from textwrap import dedent

from bytedojo.core.logger import get_logger


def create_database(db_path: Path):
    """Create SQLite database with schema for tracking problems and stats."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Problems table - stores fetched problems
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            title TEXT NOT NULL,
            difficulty TEXT,
            category TEXT,
            tags TEXT,
            description TEXT,
            file_path TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, problem_id)
        )
    """)
    
    # Attempts table - tracks solution attempts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            passed BOOLEAN NOT NULL,
            time_taken INTEGER,
            notes TEXT,
            FOREIGN KEY (problem_id) REFERENCES problems(id)
        )
    """)
    
    # Review schedule table - spaced repetition
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            next_review_date DATE NOT NULL,
            interval_days INTEGER DEFAULT 1,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            FOREIGN KEY (problem_id) REFERENCES problems(id)
        )
    """)
    
    # Stats table - aggregate statistics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            problems_attempted INTEGER DEFAULT 0,
            problems_solved INTEGER DEFAULT 0,
            total_time_minutes INTEGER DEFAULT 0
        )
    """)
    
    # User preferences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Set default config values
    cursor.execute("""
        INSERT OR IGNORE INTO config (key, value) VALUES
        ('initialized_at', ?),
        ('default_language', 'python'),
        ('default_source', 'leetcode'),
        ('problems_dir', 'problems')
    """, (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()


def create_gitignore(dojo_dir: Path):
    """Create .gitignore for the .dojo directory."""
    gitignore = dojo_dir / ".gitignore"
    
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


def create_readme(dojo_dir: Path):
    """Create README in .dojo directory."""
    readme = dojo_dir / "README.md"
    
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
        dojo fetch leetcode 1
        
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


@click.command()

# Define options
@click.option('--force', is_flag=True, help='Reinitialize even if .dojo already exists')

# Define main command
@click.pass_obj
def init(ctx, force: bool):
    """
    Initialize a ByteDojo repository in the current directory.
    
    Creates a .dojo directory with:
    - SQLite database for tracking problems and stats
    - Configuration file
    - Directory structure
    """
    logger = get_logger()
    
    # Determine .dojo location (current directory)
    dojo_dir = Path.cwd() / ".dojo"
    db_path = dojo_dir / "db.sqlite"
    
    # Check if already initialized
    if dojo_dir.exists() and not force:
        logger.error("ByteDojo repository already initialized in this directory")
        logger.info(f"Location: {dojo_dir}")
        logger.info("Use --force to reinitialize")
        raise click.ClickException("Already initialized")
    
    try:
        logger.info("Initializing ByteDojo repository...")
        
        # Create .dojo directory
        logger.debug(f"Creating directory: {dojo_dir}")
        dojo_dir.mkdir(exist_ok=True)
        
        # Create problems directory
        problems_dir = Path.cwd() / "problems"
        logger.debug(f"Creating directory: {problems_dir}")
        problems_dir.mkdir(exist_ok=True)
        
        # Create database
        logger.debug(f"Creating database: {db_path}")
        create_database(db_path)
        
        # Create .gitignore
        logger.debug("Creating .gitignore")
        create_gitignore(dojo_dir)
        
        # Create README
        logger.debug("Creating README.md")
        create_readme(dojo_dir)
        
        # Success!
        logger.info("ByteDojo repository initialized successfully!")
        logger.info(f"Location: {dojo_dir}")
        logger.info(f"Database: {db_path}")
        logger.info(f"Problems: {problems_dir}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  dojo fetch leetcode 1    # Fetch a problem")
        logger.info("  dojo stats               # View statistics")
        
    except Exception as e:
        logger.error(f"Failed to initialize ByteDojo: {e}", exc_info=ctx.debug)
        raise click.ClickException(f"Initialization failed: {e}")