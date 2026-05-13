"""
C++ formatter for LeetCode problems with intelligent test generation.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

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

#: Baseline stdlib includes preincluded in every fetched solution.cpp.
#: Matches the LeetCode "kitchen sink" UX so users don't have to
#: remember which header has `unordered_map` vs `queue` vs `priority_queue`.
#: ~1s of extra compile cost; well worth the friction reduction.
_CPP_BASELINE_INCLUDES: Tuple[str, ...] = (
    "#include <algorithm>",
    "#include <climits>",
    "#include <cmath>",
    "#include <cstdint>",
    "#include <deque>",
    "#include <functional>",
    "#include <iostream>",
    "#include <map>",
    "#include <queue>",
    "#include <set>",
    "#include <stack>",
    "#include <string>",
    "#include <unordered_map>",
    "#include <unordered_set>",
    "#include <utility>",
    "#include <vector>",
)


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

    _logger: Optional[object] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialise the logger handle and populate the metadata fields."""
        if self._logger is None:
            self._logger = get_logger()
        self._extract_metadata()

    def _extract_metadata(self):
        """Populate every metadata field in one pass over the code."""
        self.class_name = self._extract_class_name()
        self.method_name = self._extract_method_name()
        self.param_info = self._extract_parameter_info()
        self.return_type = self._extract_return_type()

        self._logger.debug(
            f"C++ metadata: class={self.class_name} method={self.method_name} "
            f"params={len(self.param_info)} returns={self.return_type}"
        )

    # ========================================================================
    # Class and Method Extraction
    # ========================================================================

    def _extract_class_name(self) -> str:
        """Extract the main class / struct name from the snippet."""
        match = re.search(r'\b(?:class|struct)\s+(\w+)\s*[{:<]', self.code)
        if match:
            return match.group(1)
        self._logger.warning("No primary class found; defaulting to 'Solution'")
        return 'Solution'

    def _extract_method_name(self) -> str:
        """Extract the main method name from the `public:` section."""
        public_section = re.search(r'public:\s*(.*)', self.code, re.DOTALL)
        if public_section:
            match = re.search(
                r'(?:[\w<>&*,\s]+)\s+(\w+)\s*\([^)]*\)', public_section.group(1)
            )
            if match:
                return match.group(1)

        self._logger.warning("No method found; defaulting to 'solve'")
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
        """Extract return type from method signature; 'void' when absent."""
        public_section = re.search(r'public:\s*(.*)', self.code, re.DOTALL)
        if not public_section:
            return 'void'
        match = re.search(
            r'([\w<>&*,\s]+)\s+\w+\s*\([^)]*\)', public_section.group(1)
        )
        if match:
            return match.group(1).strip()
        return 'void'

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
        """Generate the complete content of a C++ solution.cpp for `problem`."""
        detail = problem.problem_detail
        try:
            code_template = self._get_cpp_code(problem)

            ctx = CppFormatContext(
                code=code_template,
                description=detail.description,
                _logger=self.logger,
            )

            # Inject default return statement if the snippet has an empty body.
            code_template = self._inject_default_return(code_template, ctx.return_type)

            return self._build_file_content(problem, code_template, ctx)
        except Exception as e:
            self.logger.error(f"Error formatting problem #{detail.id}: {e}", exc_info=True)
            raise

    # ========================================================================
    # Main Content Building
    # ========================================================================

    def _build_file_content(self, problem: Problem, code_template: str, ctx: CppFormatContext) -> str:
        """Assemble the placed solution.cpp.

        Layout: file docstring -> PROBLEM DESCRIPTION -> includes (with
        `using namespace std;`) -> SOLUTION -> TEST. C++ allows includes
        anywhere before use, so placing them between description and
        the class is fine and matches the Python / Java convention.
        """
        detail = problem.problem_detail
        description = self._format_description(detail.description)
        main_function = self._generate_main_function(ctx)
        includes_section = self._compute_includes_section(problem)

        return f'''/**
 * LeetCode Problem #{detail.id}: {detail.title}
 * Difficulty: {detail.difficulty}
 */

// ============================================================================
// PROBLEM DESCRIPTION
// ============================================================================
{description}

{includes_section}

// ============================================================================
// SOLUTION
// ============================================================================

{code_template}

// ============================================================================
// TEST
// ============================================================================

{main_function}
'''

    def _compute_includes_section(self, problem: Problem) -> str:
        """Build the include block placed between description and SOLUTION.

        Order:
          1. Baseline stdlib (vector, queue, unordered_map, ...)
          2. Sibling node headers (`#include "list_node.hpp"`, etc.)
          3. `using namespace std;` (LeetCode-style, matches user's habits)
        """
        snippet = problem.get_snippet(CodeLanguage.CPP) or ""
        _, extracted = self._extract_node_classes(snippet)

        node_includes = [
            f'#include "{_CPP_NODE_HEADER.get(name, name.lower())}.hpp"'
            for name in extracted
        ]
        lines = list(_CPP_BASELINE_INCLUDES) + node_includes
        return "\n".join(lines) + "\n\nusing namespace std;"

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
        """Extract just the class body — includes + `using` move out.

        Doxygen-wrapped node structs are pulled into sibling .hpp files
        via `extra_files()`. Any `#include` / `using namespace` lines
        from the snippet are stripped so the includes section owns
        them all (it has the baseline anyway).
        """
        code = problem.get_snippet(CodeLanguage.CPP)
        if not code:
            self.logger.warning(
                f"No C++ snippet for problem #{problem.problem_detail.id}"
            )
            return "// No C++ template available"

        stripped, _ = self._extract_node_classes(code)
        return self._strip_top_level_directives(stripped)

    def _strip_top_level_directives(self, code: str) -> str:
        """Drop top-level `#include ...` and `using ...;` lines from the snippet."""
        out = []
        for line in code.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("#include"):
                continue
            if stripped.startswith("using ") and stripped.rstrip().endswith(";"):
                continue
            out.append(line)
        # Trim leading blank lines that get left behind.
        result = "\n".join(out)
        return result.lstrip("\n")

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
            return ''

        new_code = block_re.sub(replacer, code)
        return new_code, extracted


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
        """Convert problem HTML into `//`-prefixed C++ comments."""
        try:
            text = html_to_text(html_content)
            lines = text.strip().split('\n')
            return '\n'.join(f"// {line}" if line else "//" for line in lines)
        except Exception as e:
            self.logger.error(f"Error formatting description: {e}")
            return "// Error formatting description"
