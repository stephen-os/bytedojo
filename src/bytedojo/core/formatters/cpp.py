"""
C++ formatter for LeetCode problems with intelligent test generation.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.base import BaseFormatter
from bytedojo.core.formatters.utils import (
    html_to_text,
    get_cpp_default,
)
from bytedojo.core.logger import get_logger


#: Map of node class name → C++ header file stem. Determines both the
#: sibling filename and the `#include` line emitted in solution.cpp.
_CPP_NODE_HEADER: Dict[str, str] = {
    "TreeNode": "tree_node",
    "ListNode": "list_node",
    "Node":     "node",
}


# =========================================================================
# Format Context
# ==========================================================================

@dataclass
class CppFormatContext:
    """
    Context for formatting a single C++ problem.
    Contains all extracted metadata to avoid redundant parsing.
    """
    code: str
    description: str

    # Extracted metadata (populated lazily)
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    param_info: List[Tuple[str, str]] = field(default_factory=list)  # [(name, type), ...]
    return_type: Optional[str] = None
    includes_needed: Set[str] = field(default_factory=set)

    _logger: Optional[object] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize logger and extract metadata."""
        if self._logger is None:
            self._logger = get_logger()

        self._extract_metadata()

    def _extract_metadata(self):
        """Extract all metadata from code in one pass."""
        self._logger.debug("Extracting metadata from C++ code")

        self.class_name = self._extract_class_name()
        self.method_name = self._extract_method_name()
        self.param_info = self._extract_parameter_info()
        self.return_type = self._extract_return_type()
        self.includes_needed = self._detect_includes_needed()

        self._logger.debug(
            f"Metadata extracted: class={self.class_name}, method={self.method_name}, "
            f"params={len(self.param_info)}, return_type={self.return_type}"
        )

    # ========================================================================
    # Class and Method Extraction
    # ========================================================================

    def _extract_class_name(self) -> str:
        """Extract the main class name from the snippet."""
        match = re.search(r'\b(?:class|struct)\s+(\w+)\s*[{:<]', self.code)
        if match:
            class_name = match.group(1)
            self._logger.debug(f"Found class name: {class_name}")
            return class_name
        self._logger.warning("No primary class found, defaulting to 'Solution'")
        return 'Solution'

    def _extract_method_name(self) -> str:
        """Extract the main method name from the class."""
        # Pattern for C++ public method
        # Look for method after "public:" section
        public_section = re.search(r'public:\s*(.*)', self.code, re.DOTALL)
        if public_section:
            section = public_section.group(1)
            # Find first method: returnType methodName(params)
            match = re.search(
                r'(?:[\w<>&*,\s]+)\s+(\w+)\s*\([^)]*\)',
                section
            )
            if match:
                method_name = match.group(1)
                self._logger.debug(f"Found method name: {method_name}")
                return method_name

        self._logger.warning("Could not find method name, using 'solve'")
        return 'solve'

    def _extract_parameter_info(self) -> List[Tuple[str, str]]:
        """Extract parameter names and types from method signature."""
        # Find the method signature in public section
        public_section = re.search(r'public:\s*(.*)', self.code, re.DOTALL)
        if not public_section:
            return []

        section = public_section.group(1)

        # Find method with parameters
        match = re.search(
            r'(?:[\w<>&*,\s]+)\s+\w+\s*\(([^)]*)\)',
            section
        )
        if not match:
            return []

        params_str = match.group(1).strip()
        if not params_str:
            return []

        params = []
        # Split by comma, respecting angle brackets
        current_param = ""
        bracket_depth = 0

        for char in params_str + ',':
            if char == '<':
                bracket_depth += 1
                current_param += char
            elif char == '>':
                bracket_depth -= 1
                current_param += char
            elif char == ',' and bracket_depth == 0:
                param = current_param.strip()
                if param:
                    param_info = self._parse_cpp_parameter(param)
                    if param_info:
                        params.append(param_info)
                current_param = ""
            else:
                current_param += char

        self._logger.debug(f"Extracted {len(params)} parameters: {params}")
        return params

    def _parse_cpp_parameter(self, param_str: str) -> Optional[Tuple[str, str]]:
        """Parse a single C++ parameter string into (name, type)."""
        # C++ param format: "vector<int>& nums" or "int target"
        # Handle reference types with &
        param_str = param_str.strip()

        # Find the last word as the parameter name
        match = re.match(r'(.+?)\s+(\w+)\s*$', param_str)
        if match:
            param_type = match.group(1).strip()
            param_name = match.group(2).strip()
            return (param_name, param_type)

        return None

    def _extract_return_type(self) -> str:
        """Extract return type from method signature."""
        public_section = re.search(r'public:\s*(.*)', self.code, re.DOTALL)
        if not public_section:
            return 'void'

        section = public_section.group(1)

        # Match return type before method name
        match = re.search(
            r'([\w<>&*,\s]+)\s+\w+\s*\([^)]*\)',
            section
        )
        if match:
            return_type = match.group(1).strip()
            self._logger.debug(f"Found return type: {return_type}")
            return return_type

        return 'void'

    def _detect_includes_needed(self) -> Set[str]:
        """Detect what #includes are needed based on code and types."""
        includes = set()
        all_code = self.code

        # Standard type checks
        type_to_include = {
            'vector': '<vector>',
            'string': '<string>',
            'map': '<map>',
            'unordered_map': '<unordered_map>',
            'set': '<set>',
            'unordered_set': '<unordered_set>',
            'queue': '<queue>',
            'stack': '<stack>',
            'deque': '<deque>',
            'priority_queue': '<queue>',
            'pair': '<utility>',
            'algorithm': '<algorithm>',
            'numeric_limits': '<limits>',
            'INT_MAX': '<climits>',
            'INT_MIN': '<climits>',
        }

        for type_name, include in type_to_include.items():
            if type_name in all_code:
                includes.add(include)

        # Always need iostream for main
        includes.add('<iostream>')

        return includes

    # ========================================================================
    # Helper Properties
    # ========================================================================

    @property
    def instance_name(self) -> str:
        """Get the lowercase instance name for the class."""
        return self.class_name.lower() if self.class_name else 'solution'


# =========================================================================
# C++ Formatter
# ==========================================================================

class CppFormatter(BaseFormatter):
    """Formats LeetCode problems as C++ files."""

    def __init__(self):
        """Initialize the formatter with a logger."""
        self.logger = get_logger()

    def format(self, problem: Problem) -> str:
        """Generate complete C++ file content."""
        detail = problem.problem_detail
        self.logger.debug(f"Starting C++ format for problem #{detail.id}: {detail.title}")

        try:
            code_template = self._get_cpp_code(problem)

            ctx = CppFormatContext(
                code=code_template,
                description=detail.description,
                _logger=self.logger,
            )

            # Inject default return statement if needed
            code_template = self._inject_default_return(code_template, ctx.return_type)

            content = self._build_file_content(problem, code_template, ctx)

            self.logger.debug(f"Successfully formatted problem #{detail.id} as C++")
            return content

        except Exception as e:
            self.logger.error(f"Error formatting problem #{detail.id}: {e}", exc_info=True)
            raise

    # ========================================================================
    # Main Content Building
    # ========================================================================

    def _build_file_content(self, problem: Problem, code_template: str, ctx: CppFormatContext) -> str:
        """Build the complete C++ file content."""
        detail = problem.problem_detail
        includes = self._generate_includes(ctx)
        description = self._format_description(detail.description)
        main_function = self._generate_main_function(ctx)

        return f'''/**
 * LeetCode Problem #{detail.id}: {detail.title}
 * Difficulty: {detail.difficulty}
 */

{includes}

using namespace std;

// ============================================================================
// PROBLEM DESCRIPTION
// ============================================================================
{description}

// ============================================================================
// SOLUTION
// ============================================================================

{code_template}

// ============================================================================
// TEST
// ============================================================================

{main_function}
'''

    def _generate_includes(self, ctx: CppFormatContext) -> str:
        """Generate required C++ includes."""
        includes = sorted(ctx.includes_needed)
        return '\n'.join(f'#include {inc}' for inc in includes)

    def _generate_main_function(self, ctx: CppFormatContext) -> str:
        """Generate the main function with a TODO placeholder call.

        The full test suite runs via `dojo test`. We only emit a placeholder
        here so the user has a hook to edit when they want a quick local run.
        """
        lines = ['int main() {']
        lines.append(f'    {ctx.class_name} {ctx.instance_name};')
        lines.append('')
        lines.append('    // TODO: edit me, or run `dojo test` for the full suite')
        args = ', '.join(get_cpp_default(t) for _, t in ctx.param_info)
        if ctx.return_type != 'void':
            lines.append(f'    {ctx.return_type} result = {ctx.instance_name}.{ctx.method_name}({args});')
            lines.extend(self._generate_print_code('result', ctx.return_type))
        else:
            lines.append(f'    {ctx.instance_name}.{ctx.method_name}({args});')
        lines.append('    return 0;')
        lines.append('}')
        return '\n'.join(lines)

    def _generate_print_code(self, var_name: str, cpp_type: str) -> List[str]:
        """Generate appropriate print code for the type."""
        lines = []

        if 'vector<vector' in cpp_type:
            # 2D vector
            lines.append(f'    cout << "[";')
            lines.append(f'    for (size_t i = 0; i < {var_name}.size(); i++) {{')
            lines.append(f'        cout << "[";')
            lines.append(f'        for (size_t j = 0; j < {var_name}[i].size(); j++) {{')
            lines.append(f'            cout << {var_name}[i][j];')
            lines.append(f'            if (j < {var_name}[i].size() - 1) cout << ",";')
            lines.append(f'        }}')
            lines.append(f'        cout << "]";')
            lines.append(f'        if (i < {var_name}.size() - 1) cout << ",";')
            lines.append(f'    }}')
            lines.append(f'    cout << "]" << endl;')
        elif 'vector<' in cpp_type:
            # 1D vector
            lines.append(f'    cout << "[";')
            lines.append(f'    for (size_t i = 0; i < {var_name}.size(); i++) {{')
            lines.append(f'        cout << {var_name}[i];')
            lines.append(f'        if (i < {var_name}.size() - 1) cout << ",";')
            lines.append(f'    }}')
            lines.append(f'    cout << "]" << endl;')
        else:
            # Simple type
            lines.append(f'    cout << {var_name} << endl;')

        return lines

    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================

    def _get_cpp_code(self, problem: Problem) -> str:
        """Extract C++ code, lifting embedded node structs into siblings.

        LeetCode wraps `TreeNode` / `ListNode` definitions in Doxygen
        blocks at the top of the snippet. We *remove* those blocks from
        the snippet (they become `tree_node.hpp` / `list_node.hpp`
        siblings via `extra_files()`) and prepend `#include "..."`
        directives so the user's solution.cpp wires up.
        """
        detail = problem.problem_detail
        self.logger.debug(f"Extracting C++ code for problem #{detail.id}")

        code = problem.get_snippet(CodeLanguage.CPP)
        if not code:
            self.logger.warning(f"No C++ snippet found for problem #{detail.id}")
            return "// No C++ template available"

        stripped, extracted = self._extract_node_classes(code)
        if extracted:
            include_lines = [
                f'#include "{_CPP_NODE_HEADER.get(name, name.lower())}.hpp"'
                for name in extracted
            ]
            stripped = self._inject_node_includes(stripped, include_lines)
        return stripped

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        """Emit one `<snake>.hpp` per node struct found in the snippet."""
        snippet = problem.get_snippet(CodeLanguage.CPP) or ""
        _, extracted = self._extract_node_classes(snippet)
        files: Dict[str, str] = {}
        for name, body in extracted.items():
            stem = _CPP_NODE_HEADER.get(name, name.lower())
            guard = stem.upper() + "_HPP_"
            files[f"{stem}.hpp"] = (
                f"#ifndef {guard}\n"
                f"#define {guard}\n\n"
                f"{body}\n"
                f"#endif  // {guard}\n"
            )
        return files

    def _extract_node_classes(self, code: str) -> Tuple[str, Dict[str, str]]:
        """Pull Doxygen-wrapped node-struct definitions out of the snippet.

        Returns (stripped_code, {class_name: body}). `body` is the bare
        `struct X { ... };` declaration ready to drop into its own .hpp
        file. The stripped code has the Doxygen block removed entirely.
        """
        block_re = re.compile(r'/\*\*(.*?)\*/\s*\n?', re.DOTALL)
        extracted: Dict[str, str] = {}

        def replacer(match):
            body = match.group(1)
            class_match = re.search(
                r'^\s*\*\s*(?:struct|class)\s+(\w+)\b', body, re.MULTILINE
            )
            if not class_match:
                return match.group(0)
            class_name = class_match.group(1)

            out_lines: List[str] = []
            for raw in body.split('\n'):
                stripped = raw.lstrip()
                if not stripped.startswith('*'):
                    continue
                content = stripped[1:]
                if content.startswith(' '):
                    content = content[1:]
                if content.startswith('Definition for') or not content.strip():
                    continue
                out_lines.append(content.rstrip())

            extracted[class_name] = '\n'.join(out_lines).rstrip() + '\n'
            self.logger.debug(
                f"Extracted Doxygen node-class block: {class_name} "
                f"({len(out_lines)} lines)"
            )
            return ''

        new_code = block_re.sub(replacer, code)
        return new_code, extracted

    def _inject_node_includes(self, code: str, include_lines: List[str]) -> str:
        """Drop node-class #include directives in after the existing #include block."""
        lines = code.split('\n')
        last_include_idx = -1
        for i, line in enumerate(lines):
            if line.lstrip().startswith('#include'):
                last_include_idx = i
        if last_include_idx >= 0:
            lines[last_include_idx + 1:last_include_idx + 1] = include_lines
        else:
            lines = include_lines + lines
        return '\n'.join(lines)

    def _inject_default_return(self, code: str, return_type: str) -> str:
        """
        Inject a default return statement into an empty method body.

        Args:
            code: The C++ code template
            return_type: The method's return type

        Returns:
            Code with default return statement injected
        """
        if return_type == 'void':
            return code

        default_value = get_cpp_default(return_type)

        # Pattern to find empty or whitespace-only method body
        # Matches: { followed by optional whitespace/newlines, then }
        pattern = r'(\{\s*)\n(\s*)\}'

        def replacer(match):
            opening = match.group(1)
            indent = match.group(2)
            return f'{opening}\n{indent}    return {default_value};\n{indent}}}'

        # Only replace the first occurrence (the main method)
        return re.sub(pattern, replacer, code, count=1)

    # ========================================================================
    # Description Formatting
    # ========================================================================

    def _format_description(self, html_content: str) -> str:
        """Convert HTML to C++ comments."""
        self.logger.debug("Formatting problem description for C++")

        try:
            text = html_to_text(html_content)
            lines = text.strip().split('\n')
            return '\n'.join(f"// {line}" if line else "//" for line in lines)
        except Exception as e:
            self.logger.error(f"Error formatting description: {e}")
            return "// Error formatting description"
