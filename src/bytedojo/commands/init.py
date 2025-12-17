"""
Init command - Creates a .dojo directory in the current folder.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import DojoRepository


@click.command()
@click.option('--force', is_flag=True, help='Reinitialize even if .dojo already exists')
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
    
    repo = DojoRepository()
    
    # Check if already initialized
    if repo.exists() and not force:
        logger.error("ByteDojo repository already initialized in this directory")
        logger.info(f"Location: {repo.dojo_dir}")
        logger.info("Use --force to reinitialize")
        raise click.ClickException("Already initialized")
    
    try:
        logger.info("Initializing ByteDojo repository...")
        
        # Initialize repository
        repo.initialize(force=force)
        
        # Success!
        logger.info("ByteDojo repository initialized successfully!")
        logger.info(f"Location: {repo.dojo_dir}")
        logger.info(f"Database: {repo.db_path}")
        logger.info(f"Problems: {repo.problems_dir}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  dojo leetcode fetch 1    # Fetch a problem")
        logger.info("  dojo stats               # View statistics")
        
    except Exception as e:
        logger.error(f"Failed to initialize ByteDojo: {e}", exc_info=ctx.debug)
        raise click.ClickException(f"Initialization failed: {e}")