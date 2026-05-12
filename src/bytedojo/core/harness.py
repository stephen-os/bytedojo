"""
Harness management - Load templates and generate test code.

This module handles:
- Loading language configuration files
- Loading harness templates
- Generating combined code (harness + user solution)
- Preparing test input in the unified JSON format
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml

from bytedojo.core.models.test_case import TestCase


# Package data directory (relative to this file)
_DATA_DIR = Path(__file__).parent.parent / "data"
_HARNESSES_DIR = _DATA_DIR / "harnesses"
_LANGUAGES_DIR = _DATA_DIR / "languages"


@dataclass
class LanguageConfig:
    """Configuration for a programming language harness."""
    language: str           # Display name (e.g., "python3")
    extension: str          # File extension (e.g., ".py")
    solution_placeholder: str = "{{SOLUTION}}"  # Placeholder in harness template


class HarnessError(Exception):
    """Raised when harness operations fail."""
    pass


def _get_data_dir() -> Path:
    """Get the data directory path."""
    # Try package directory first
    if _DATA_DIR.exists():
        return _DATA_DIR
    # Fallback to project root data directory
    project_data = Path(__file__).parent.parent.parent.parent.parent / "data"
    if project_data.exists():
        return project_data
    raise HarnessError(f"Data directory not found. Expected at: {_DATA_DIR}")


def load_language_config(language: str) -> LanguageConfig:
    """
    Load language configuration from YAML file.

    Args:
        language: Language identifier (e.g., "python3", "java")

    Returns:
        LanguageConfig with language settings
    """
    # Normalize language name
    lang_key = _normalize_language(language)

    # Try to load from file
    config_path = _LANGUAGES_DIR / f"{lang_key}.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return LanguageConfig(
                language=data.get("language", language),
                extension=data.get("extension", ".txt"),
                solution_placeholder=data.get("solution_placeholder", "{{SOLUTION}}"),
            )

    # Fallback to built-in defaults
    return _get_default_config(lang_key)


def _normalize_language(language: str) -> str:
    """Normalize language identifier."""
    lang_map = {
        "python": "python3",
        "python3": "python3",
        "java": "java",
        "cpp": "cpp",
        "c++": "cpp",
        "javascript": "javascript",
        "js": "javascript",
        "typescript": "typescript",
        "ts": "typescript",
        "go": "go",
        "golang": "go",
        "rust": "rust",
        "ruby": "ruby",
        "swift": "swift",
        "kotlin": "kotlin",
        "scala": "scala",
        "csharp": "csharp",
        "c#": "csharp",
        "php": "php",
        "dart": "dart",
    }
    return lang_map.get(language.lower(), language.lower())


def _get_default_config(language: str) -> LanguageConfig:
    """Get default configuration for a language."""
    defaults = {
        "python3": LanguageConfig("python3", ".py"),
        "java": LanguageConfig("java", ".java"),
        "cpp": LanguageConfig("cpp", ".cpp"),
        "javascript": LanguageConfig("javascript", ".js"),
        "typescript": LanguageConfig("typescript", ".ts"),
        "go": LanguageConfig("go", ".go"),
        "rust": LanguageConfig("rust", ".rs"),
        "ruby": LanguageConfig("ruby", ".rb"),
    }
    return defaults.get(language, LanguageConfig(language, ".txt"))


def load_harness_template(language: str) -> str:
    """
    Load harness template for a language.

    Args:
        language: Language identifier

    Returns:
        Template string with {{SOLUTION}} placeholder
    """
    lang_key = _normalize_language(language)
    template_path = _HARNESSES_DIR / f"{lang_key}.txt"

    if template_path.exists():
        return template_path.read_text(encoding="utf-8")

    # Fallback to embedded templates
    return _get_embedded_harness(lang_key)


def _get_embedded_harness(language: str) -> str:
    """Get embedded harness template for common languages."""
    templates = {
        "python3": _PYTHON_HARNESS,
        "java": _JAVA_HARNESS,
        "cpp": _CPP_HARNESS,
    }
    if language not in templates:
        raise HarnessError(
            f"No harness template for language: {language}. "
            f"Supported: {', '.join(templates.keys())}"
        )
    return templates[language]


def generate_test_code(
    solution_code: str,
    language: str,
    config: Optional[LanguageConfig] = None,
    test_data: Optional[dict] = None
) -> str:
    """
    Generate complete test code by combining harness with solution.

    Args:
        solution_code: User's solution code
        language: Programming language
        config: Optional language config (loaded if not provided)
        test_data: Optional test data to embed in the code

    Returns:
        Complete code ready for execution
    """
    if config is None:
        config = load_language_config(language)

    harness = load_harness_template(language)
    code = harness.replace(config.solution_placeholder, solution_code)

    # Embed test data if provided
    if test_data is not None:
        import json
        # Convert JSON to Python syntax
        json_str = json.dumps(test_data)
        python_str = json_str.replace("null", "None").replace("true", "True").replace("false", "False")
        code = code.replace("{{TEST_DATA}}", python_str)

    return code


def prepare_test_input(
    method_name: str,
    test_cases: List[TestCase],
    language: str = "python3"
) -> dict:
    """
    Prepare test input in unified JSON format.

    Args:
        method_name: Name of the method to test
        test_cases: List of test cases
        language: Target language (for any language-specific handling)

    Returns:
        Dict ready to be JSON-serialized and sent to harness
    """
    cases = []
    for case in test_cases:
        args = _parse_test_input(case.input)
        expected = _parse_expected_output(case.output)
        cases.append({
            "args": args,
            "expected": expected,
            "input_str": case.input,  # Original string for display
            "expected_str": case.output,
        })

    return {
        "method": method_name,
        "cases": cases,
    }


def _parse_test_input(input_str: str) -> Dict[str, Any]:
    """
    Parse test input string into a dictionary of arguments.

    Example: "nums = [3,3], target = 6" -> {"nums": [3, 3], "target": 6}
    """
    result = {}

    # Split by top-level commas (not inside brackets/strings)
    parts = _split_by_comma(input_str)

    for part in parts:
        if "=" in part:
            var_name, value_str = part.split("=", 1)
            var_name = var_name.strip()
            value_str = value_str.strip()

            # Parse the value
            result[var_name] = _parse_value(value_str)

    return result


def _split_by_comma(s: str) -> List[str]:
    """Split string by commas, respecting brackets and quotes."""
    parts = []
    current = ""
    depth = 0
    in_string = False
    string_char = None

    for char in s:
        if char in "\"'":
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
        elif char in "[{(":
            if not in_string:
                depth += 1
        elif char in "]})":
            if not in_string:
                depth -= 1
        elif char == "," and depth == 0 and not in_string:
            parts.append(current.strip())
            current = ""
            continue
        current += char

    if current.strip():
        parts.append(current.strip())

    return parts


def _parse_value(value_str: str) -> Any:
    """Parse a value string to Python object."""
    # Normalize special values
    value_str = value_str.replace("null", "None")
    value_str = value_str.replace("true", "True")
    value_str = value_str.replace("false", "False")

    try:
        return eval(value_str)
    except Exception:
        # Return as string if eval fails
        return value_str


def _parse_expected_output(output_str: str) -> Any:
    """Parse expected output string to Python object."""
    return _parse_value(output_str)


def parse_method_name(code_snippet: str, language: str) -> Optional[str]:
    """
    Parse method name from a code snippet.

    Args:
        code_snippet: Code snippet (usually from LeetCode)
        language: Programming language

    Returns:
        Method name or None if not found
    """
    lang_key = _normalize_language(language)

    if lang_key == "python3":
        # Python: def methodName(self, ...
        match = re.search(r"def\s+(\w+)\s*\(\s*self", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "java":
        # Java: public ReturnType methodName(...)
        match = re.search(r"public\s+\S+\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "cpp":
        # C++: ReturnType methodName(...)
        match = re.search(r"^\s*\S+\s+(\w+)\s*\(", code_snippet, re.MULTILINE)
        if match:
            return match.group(1)

    elif lang_key in ("javascript", "typescript"):
        # JS/TS: methodName(... or var methodName = function
        match = re.search(r"(?:var|let|const)?\s*(\w+)\s*[=:]\s*(?:function|\()", code_snippet)
        if not match:
            match = re.search(r"(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "go":
        # Go: func (s *Solution) methodName(...)
        match = re.search(r"func\s*\([^)]+\)\s*(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "rust":
        # Rust: pub fn methodName(...)
        match = re.search(r"(?:pub\s+)?fn\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "ruby":
        # Ruby: def methodName
        match = re.search(r"def\s+(\w+)", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "swift":
        # Swift: func methodName(...)
        match = re.search(r"func\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "kotlin":
        # Kotlin: fun methodName(...)
        match = re.search(r"fun\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "scala":
        # Scala: def methodName(...)
        match = re.search(r"def\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "csharp":
        # C#: public ReturnType MethodName(...)
        match = re.search(r"public\s+\S+\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "php":
        # PHP: function methodName(...)
        match = re.search(r"function\s+(\w+)\s*\(", code_snippet)
        if match:
            return match.group(1)

    elif lang_key == "dart":
        # Dart: ReturnType methodName(...)
        match = re.search(r"^\s*\S+\s+(\w+)\s*\(", code_snippet, re.MULTILINE)
        if match:
            return match.group(1)

    return None


# ============================================================================
# EMBEDDED HARNESS TEMPLATES
# These are fallbacks when template files don't exist
# ============================================================================

PYTHON_RESULTS_BEGIN = "###BYTEDOJO_RESULTS_BEGIN###"
PYTHON_RESULTS_END = "###BYTEDOJO_RESULTS_END###"

_PYTHON_HARNESS = '''
import json as _bytedojo_json

{{SOLUTION}}

# Test data is embedded here by the harness generator
_BYTEDOJO_TEST_DATA = {{TEST_DATA}}


def _bytedojo_normalize(val):
    """Normalize value for comparison."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)):
        return [_bytedojo_normalize(v) for v in val]
    if isinstance(val, dict):
        return {k: _bytedojo_normalize(v) for k, v in val.items()}
    return val


def _bytedojo_display(val):
    """Format value for display."""
    if val is None:
        return "None"
    return repr(val)


def _bytedojo_run():
    method_name = _BYTEDOJO_TEST_DATA["method"]
    cases = _BYTEDOJO_TEST_DATA["cases"]

    solution = Solution()
    method = getattr(solution, method_name)
    results = []

    for i, case in enumerate(cases):
        try:
            result = method(**case["args"])
            actual_norm = _bytedojo_normalize(result)
            expected_norm = _bytedojo_normalize(case["expected"])
            passed = actual_norm == expected_norm

            results.append({
                "case": i + 1,
                "passed": passed,
                "expected": case["expected_str"],
                "actual": _bytedojo_display(result),
                "error": None
            })
        except Exception as e:
            results.append({
                "case": i + 1,
                "passed": False,
                "expected": case["expected_str"],
                "actual": "",
                "error": str(e)
            })

    # Wrap output in sentinels so the parent parser isn't confused by any
    # output the user's solution (e.g. an `if __name__ == "__main__":` block)
    # may have produced earlier in the run.
    print("###BYTEDOJO_RESULTS_BEGIN###")
    print(_bytedojo_json.dumps(results))
    print("###BYTEDOJO_RESULTS_END###")


_bytedojo_run()
'''

_JAVA_HARNESS = '''
import java.util.*;
import java.io.*;
import java.lang.reflect.*;

{{SOLUTION}}

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }

        // Simple JSON parsing (no external dependencies)
        String json = sb.toString();
        // Extract method name
        int methodStart = json.indexOf("\\"method\\"") + 10;
        int methodEnd = json.indexOf("\\"", methodStart);
        String methodName = json.substring(methodStart, methodEnd);

        // For Java, we need proper JSON parsing which requires more setup
        // This is a simplified version that works for basic cases
        System.out.println("[{\\"case\\": 1, \\"passed\\": false, \\"expected\\": \\"\\", \\"actual\\": \\"\\", \\"error\\": \\"Java harness requires GSON library\\"}]");
    }
}
'''

_CPP_HARNESS = '''
#include <iostream>
#include <vector>
#include <string>
#include <sstream>

using namespace std;

{{SOLUTION}}

int main() {
    // C++ harness requires JSON library
    // This is a placeholder
    cout << "[{\\"case\\": 1, \\"passed\\": false, \\"expected\\": \\"\\", \\"actual\\": \\"\\", \\"error\\": \\"C++ harness requires nlohmann/json\\"}]" << endl;
    return 0;
}
'''
