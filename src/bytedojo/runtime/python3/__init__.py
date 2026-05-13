"""
Python universal runner package.

The two source files in this directory (runner.py + converters.py) are
copied into a per-problem build directory by TestService and executed
in place. They have zero bytedojo dependencies — they read `cases.json`
and import the user's solution as plain modules.
"""

from pathlib import Path

#: Directory holding the runtime source files. TestService uses this
#: path to copy runner.py and converters.py into the build dir.
RUNTIME_DIR = Path(__file__).resolve().parent
