"""
Shared utilities for language formatters.

Common functionality for parsing and formatting LeetCode problems.
"""

import re
from typing import Dict
from html import unescape


def html_to_text(html_content: str) -> str:
    """
    Convert HTML content to plain text.

    Args:
        html_content: HTML string

    Returns:
        Plain text with HTML tags removed
    """
    if not html_content:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Unescape HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def parse_input_variables(input_text: str) -> Dict[str, str]:
    """
    Parse input line like 'nums = [2,7,11,15], target = 9' into dict.

    Args:
        input_text: Input specification from example

    Returns:
        Dict like {'nums': '[2,7,11,15]', 'target': '9'}
    """
    result = {}

    # Pattern: varname = value (handling arrays and nested structures)
    # Match variable name, then =, then value up to next var assignment or end
    pattern = r'(\w+)\s*=\s*'

    # Find all variable names and their positions
    var_matches = list(re.finditer(pattern, input_text))

    for i, match in enumerate(var_matches):
        var_name = match.group(1)
        start = match.end()

        # End is either next variable assignment or end of string
        if i + 1 < len(var_matches):
            end = var_matches[i + 1].start()
            # Find the comma before the next variable
            value = input_text[start:end].rstrip().rstrip(',').strip()
        else:
            value = input_text[start:].strip()

        # Clean up the value
        value = value.rstrip(',').strip()
        result[var_name] = value

    return result


def convert_to_python_literal(value: str) -> str:
    """
    Convert LeetCode test case value to Python literal.

    Args:
        value: String value from test case

    Returns:
        Python-compatible literal string
    """
    value = value.strip()

    # Already looks like Python
    if value.startswith('[') or value.startswith('"') or value.startswith("'"):
        return value

    # Boolean conversion
    if value.lower() == 'true':
        return 'True'
    if value.lower() == 'false':
        return 'False'

    # null -> None
    if value.lower() == 'null':
        return 'None'

    return value
