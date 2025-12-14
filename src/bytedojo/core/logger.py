"""
Logging configuration for ByteDojo.

Modern logging setup using dictConfig with console output only.
"""

import logging
import logging.config
import sys


# Gruvbox color theme
class Theme:
    """Gruvbox color palette (dark mode)."""
    # Gruvbox colors
    RED = '\033[38;2;251;73;52m'         # #fb4934
    GREEN = '\033[38;2;184;187;38m'      # #b8bb26
    YELLOW = '\033[38;2;250;189;47m'     # #fabd2f
    BLUE = '\033[38;2;131;165;152m'      # #83a598
    PURPLE = '\033[38;2;211;134;155m'    # #d3869b
    AQUA = '\033[38;2;142;192;124m'      # #8ec07c
    ORANGE = '\033[38;2;254;128;25m'     # #fe8019
    GRAY = '\033[38;2;168;153;132m'      # #a89984
    BOLD = '\033[1m'
    RESET = '\033[0m'


class TerminalFormatter(logging.Formatter):
    """Terminal formatter."""
    
    LEVEL_COLORS = {
        'DEBUG': Theme.GRAY,
        'INFO': Theme.BLUE,
        'WARNING': Theme.YELLOW,
        'ERROR': Theme.RED,
        'CRITICAL': Theme.RED + Theme.BOLD,
    }
    
    MESSAGE_COLORS = {
        'DEBUG': Theme.GRAY,
        'INFO': Theme.AQUA,
        'WARNING': Theme.YELLOW,
        'ERROR': Theme.RED,
        'CRITICAL': Theme.RED,
    }
    
    def format(self, record):
        record_copy = logging.makeLogRecord(record.__dict__)
        
        record_copy.levelname = f"{self.LEVEL_COLORS.get(record_copy.levelname, '')}{record_copy.levelname}{Theme.RESET}"
        msg_color = self.MESSAGE_COLORS.get(record_copy.levelname, '')
        record_copy.msg = f"{msg_color}{record_copy.msg}{Theme.RESET}"
        
        formatted_record = super().format(record_copy)
        
        import re
        formatted_record = re.sub(r'\[(\d{2}:\d{2}:\d{2})\]', f'[{Theme.ORANGE}\\1{Theme.RESET}]', formatted_record)
        formatted_record = re.sub(r'\[([\w.]+)\.([\w]+):(\d+)\]', f'[{Theme.PURPLE}\\1.\\2:\\3{Theme.RESET}]', formatted_record)
        
        return formatted_record


class FileFormatter(logging.Formatter):
    """File formatter."""
    
    def format(self, record):
        return super().format(record)


# Singleton logger instance
_logger = None


def get_config(debug: bool = False):
    """
    Get logging configuration dictionary.
    
    Args:
        debug: Enable debug mode (verbose output)
        
    Returns:
        Dictionary for logging.config.dictConfig()
    """
    from pathlib import Path
    from datetime import datetime
    
    # Base config
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                '()': TerminalFormatter,
                'format': '%(message)s',
            },
            'detailed': {
                '()': TerminalFormatter,
                'format': '[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                'datefmt': '%H:%M:%S',
            },
            'file': {
                '()': FileFormatter,
                'fmt': '%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG' if debug else 'INFO',
                'formatter': 'detailed' if debug else 'simple',
                'stream': sys.stdout,
            },
        },
        'loggers': {
            'bytedojo': {
                'level': 'DEBUG' if debug else 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }
    
    if debug:
        log_dir = Path.home() / '.bytedojo' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"debug_{datetime.now().strftime('%Y%m%d')}.log"
        
        config['handlers']['file'] = {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'file',
            'filename': str(log_file),
            'mode': 'a',
        }
        
        config['loggers']['bytedojo']['handlers'].append('file')
    
    return config


def setup_logger(debug: bool = False):
    """
    Setup the global logger instance (singleton).
    
    Args:
        debug: Enable debug mode
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    # Configure logging
    config = get_config(debug=debug)
    logging.config.dictConfig(config)
    
    # Get the logger
    _logger = logging.getLogger('bytedojo')
    
    if debug:
        _logger.debug("Debug mode enabled - verbose logging active")
        from pathlib import Path
        log_dir = Path.home() / '.bytedojo' / 'logs'
        _logger.debug(f"Logging to: {log_dir}")
    
    return _logger


def get_logger():
    """
    Get the global logger instance.
    
    Returns:
        Logger instance
        
    Raises:
        RuntimeError: If logger hasn't been initialized
    """
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call setup_logger() first.")
    return _logger


def main():
    """Demo of ByteDojo logging functionality."""
    import time
    
    # Production mode
    print("=== Production Mode ===")
    prod_logger = setup_logger(debug=False)
    prod_logger.debug("This debug message won't appear")
    prod_logger.info("Starting ByteDojo...")
    prod_logger.info("Fetching problem from LeetCode")
    prod_logger.warning("Network latency detected")
    prod_logger.error("Failed to fetch problem: Connection timeout")
    
    time.sleep(1)
    print("\n=== Debug Mode ===")
    
    # Debug mode
    debug_logger = setup_logger(debug=True)
    debug_logger.debug("This debug message WILL appear")
    debug_logger.debug("Parsing problem IDs: 1..5")
    debug_logger.info("Starting problem fetch")
    debug_logger.info("Connecting to api.leetcode.com")
    debug_logger.warning("Rate limit approaching")
    debug_logger.error("API request failed")


if __name__ == "__main__":
    main()