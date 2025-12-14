"""
ByteDojo - Main entry point.
"""

import sys
from bytedojo.commands.bytedojo import bytedojo
from bytedojo.core.logger import get_logger


def main():
    """Entry point for the ByteDojo CLI."""
    try:
        bytedojo()
    except Exception as e:
        try:
            logger = get_logger()
            logger.critical(f"Unhandled exception: {e}", exc_info=True)
        except RuntimeError:
            print(f"CRITICAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()