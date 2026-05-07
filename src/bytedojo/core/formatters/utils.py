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


def convert_to_java_literal(value: str, java_type: str) -> str:
    """
    Convert LeetCode input format to Java literal.

    Args:
        value: String value from test case
        java_type: Java type string

    Returns:
        Java-compatible literal string
    """
    value = value.strip()

    if java_type in ('int', 'long', 'double', 'float'):
        return value

    if java_type == 'String':
        if not value.startswith('"'):
            return f'"{value}"'
        return value

    if java_type == 'int[]':
        # [1,2,3] -> new int[]{1,2,3}
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1]
            return f'new int[]{{{inner}}}'
        return value

    if java_type == 'int[][]':
        # [[1,2],[3,4]] -> new int[][]{{1,2},{3,4}}
        if value.startswith('[['):
            inner = value[1:-1]
            inner = inner.replace('[', '{').replace(']', '}')
            return f'new int[][]{{{inner}}}'
        return value

    if java_type == 'String[]':
        # ["a","b"] -> new String[]{"a","b"}
        if value.startswith('['):
            inner = value[1:-1]
            return f'new String[]{{{inner}}}'
        return value

    if 'List<Integer>' in java_type:
        # [1,2,3] -> Arrays.asList(1,2,3)
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1]
            return f'Arrays.asList({inner})'
        return value

    if java_type == 'boolean':
        return value.lower()

    return value


def convert_to_cpp_literal(value: str, cpp_type: str) -> str:
    """
    Convert LeetCode input format to C++ literal.

    Args:
        value: String value from test case
        cpp_type: C++ type string

    Returns:
        C++-compatible literal string
    """
    value = value.strip()

    if cpp_type in ('int', 'long', 'long long', 'double', 'float'):
        return value

    # Check vector types before simple string to avoid matching 'string' in 'vector<string>'
    if 'vector<string>' in cpp_type.lower():
        # ["a","b"] -> {"a","b"}
        if value.startswith('['):
            inner = value[1:-1]
            return f'{{{inner}}}'
        return value

    if 'vector<vector<int>>' in cpp_type:
        # [[1,2],[3,4]] -> {{1,2},{3,4}}
        if value.startswith('[['):
            inner = value[1:-1]
            inner = inner.replace('[', '{').replace(']', '}')
            return f'{{{inner}}}'
        return value

    if 'vector<int>' in cpp_type:
        # [1,2,3] -> {1,2,3}
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1]
            return f'{{{inner}}}'
        return value

    # Simple string type (not vector<string>)
    if cpp_type == 'string' or cpp_type == 'string&':
        if not value.startswith('"'):
            return f'"{value}"'
        return value

    if cpp_type == 'bool':
        return value.lower()

    return value


def get_java_default(java_type: str) -> str:
    """
    Get default argument value for a Java type.

    Args:
        java_type: Java type string

    Returns:
        Default value string
    """
    defaults = {
        'int': '0',
        'long': '0L',
        'double': '0.0',
        'float': '0.0f',
        'boolean': 'false',
        'String': '""',
        'int[]': 'new int[]{}',
        'int[][]': 'new int[][]{}',
        'String[]': 'new String[]{}',
        'ListNode': 'null',
        'TreeNode': 'null',
    }

    if java_type in defaults:
        return defaults[java_type]

    if 'List<' in java_type:
        return 'new ArrayList<>()'

    return 'null'


def get_cpp_default(cpp_type: str) -> str:
    """
    Get default argument value for a C++ type.

    Args:
        cpp_type: C++ type string

    Returns:
        Default value string
    """
    defaults = {
        'int': '0',
        'long': '0L',
        'long long': '0LL',
        'double': '0.0',
        'float': '0.0f',
        'bool': 'false',
        'string': '""',
        'ListNode*': 'nullptr',
        'TreeNode*': 'nullptr',
    }

    if cpp_type in defaults:
        return defaults[cpp_type]

    # Handle reference types
    base_type = cpp_type.rstrip('&').strip()
    if base_type in defaults:
        return defaults[base_type]

    if 'vector' in cpp_type.lower():
        return '{}'

    return '{}'
