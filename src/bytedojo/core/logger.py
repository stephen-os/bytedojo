"""
Logging configuration for ByteDojo.

Modern logging setup using dictConfig with console output only.
"""

import logging
import logging.config
import re
import sys

from typing import Any, ClassVar, Dict, Optional

_logger: Optional[logging.Logger] = None

class Theme:
    """Color theme."""
    RED = '\033[38;2;251;73;52m'        # #fb4934
    GREEN = '\033[38;2;184;187;38m'     # #b8bb26
    YELLOW = '\033[38;2;250;189;47m'    # #fabd2f
    BLUE = '\033[38;2;131;165;152m'     # #83a598
    PURPLE = '\033[38;2;211;134;155m'   # #d3869b
    AQUA = '\033[38;2;142;192;124m'     # #8ec07c
    ORANGE = '\033[38;2;254;128;25m'    # #fe8019
    GRAY = '\033[38;2;168;153;132m'     # #a89984
    BOLD = '\033[1m'                    # Bold text
    RESET = '\033[0m'                   # Reset to default

class LoggerFormatter(logging.Formatter):
    """Terminal formatter."""

    LEVEL_COLORS: ClassVar[Dict[str, str]] = {
        'DEBUG': Theme.GRAY,
        'INFO': Theme.BLUE,
        'WARNING': Theme.YELLOW,
        'ERROR': Theme.RED,
        'CRITICAL': Theme.RED + Theme.BOLD,
    }

    MESSAGE_COLORS: ClassVar[Dict[str, str]] = {
        'DEBUG': Theme.GRAY,
        'INFO': Theme.AQUA,
        'WARNING': Theme.YELLOW,
        'ERROR': Theme.RED,
        'CRITICAL': Theme.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        record_copy = logging.makeLogRecord(record.__dict__)

        record_copy.levelname = f"{self.LEVEL_COLORS.get(record_copy.levelname, '')}{record_copy.levelname}{Theme.RESET}"
        msg_color = self.MESSAGE_COLORS.get(record_copy.levelname, '')
        record_copy.msg = f"{msg_color}{record_copy.msg}{Theme.RESET}"

        formatted_record = super().format(record_copy)
        formatted_record = re.sub(r'\[(\d{2}:\d{2}:\d{2})\]', f'[{Theme.ORANGE}\\1{Theme.RESET}]', formatted_record)
        formatted_record = re.sub(r'\[([\w.]+)\.([\w]+):(\d+)\]', f'[{Theme.PURPLE}\\1.\\2:\\3{Theme.RESET}]', formatted_record)

        return formatted_record

def get_config(debug: bool = False) -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                '()': LoggerFormatter,
                'format': '%(message)s',
            },
            'detailed': {
                '()': LoggerFormatter,
                'format': '[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                'datefmt': '%H:%M:%S',
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

def setup_logger(debug: bool = False) -> None:
    """Setup the global logger instance."""
    global _logger
    logging.config.dictConfig(get_config(debug=debug))
    _logger = logging.getLogger('bytedojo')
    if debug:
        _logger.debug("Debug mode enabled")

def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call setup_logger() first.")
    return _logger