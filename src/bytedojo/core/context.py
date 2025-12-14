
from pathlib import Path
from typing import Optional

from bytedojo.core.logger import get_logger

class Context:
    """Context object passed between CLI commands."""
    
    def __init__(self, debug: bool = False, config_path: Optional[Path] = None):
        self.debug = debug
        self.config_path = config_path
        self.logger = get_logger()
