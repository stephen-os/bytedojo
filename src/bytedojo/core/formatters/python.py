"""
Python formatter for LeetCode problems with intelligent test generation.
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from html import unescape

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.base import BaseFormatter
from bytedojo.core.logger import get_logger


#: Map of node class name → Python module name (file stem). Determines
#: where the user's `from X import Y` lands and what the sibling file
#: gets named.
_PYTHON_NODE_MODULES: Dict[str, str] = {
    "TreeNode": "tree_node",
    "ListNode": "list_node",
    "Node":     "node",
}

#: Baseline stdlib imports preincluded in every fetched solution.py.
#: Matches the "kitchen sink" Python LeetCode users come from — the
#: friction of remembering which module has `defaultdict` vs `Counter`
#: vs `deque` doesn't add learning value, just yak-shaving.
_PYTHON_BASELINE_IMPORTS: Tuple[str, ...] = (
    "from collections import Counter, defaultdict, deque",
    "from functools import lru_cache",
    "from heapq import heappop, heappush",
    "from math import inf",
    "from typing import Dict, List, Optional, Set, Tuple",
)

# =========================================================================
# Format Context
# ==========================================================================

@dataclass
class FormatContext:
    """
    Context for formatting a single Python problem.
    Contains all extracted metadata to avoid redundant parsing.
    """
    code: str
    description: str

    # Extracted metadata (populated lazily)
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    param_info: List[Tuple[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    param_count: Optional[int] = None
    helpers_needed: Dict[str, bool] = field(default_factory=dict)

    _logger: Optional[object] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize logger and extract metadata."""
        if self._logger is None:
            self._logger = get_logger()

        # Extract all metadata once during initialization
        self._extract_metadata()

    def _extract_metadata(self):
        """Extract all metadata from code in one pass."""
        self._logger.debug("Extracting metadata from code")

        # Extract class and method information
        self.class_name = self._extract_class_name()
        self.method_name = self._extract_method_name()
        self.param_info = self._extract_parameter_info()
        self.return_type = self._extract_return_type()
        self.param_count = self._count_method_params()

        # Detect helper functions needed
        self.helpers_needed = self._detect_helpers_needed()

        self._logger.debug(f"Metadata extracted: class={self.class_name}, method={self.method_name}, "
                          f"params={len(self.param_info)}, helpers={list(self.helpers_needed.keys())}")
    
    # ========================================================================
    # Class and Method Extraction
    # ========================================================================
    
    def _extract_class_name(self) -> str:
        """Extract the main class name (Solution, Codec, etc.)."""
        lines = self.code.split('\n')
        
        # Priority: Solution class first
        for line in lines:
            if 'class Solution' in line:
                return 'Solution'
        
        # Otherwise find first non-node class
        for line in lines:
            match = re.match(r'^\s*class\s+(\w+)', line)
            if match:
                class_name = match.group(1)
                # Skip node/data structure classes
                if class_name not in ['TreeNode', 'ListNode', 'Node']:
                    self._logger.debug(f"Found main class: {class_name}")
                    return class_name
        
        self._logger.warning("No main class found, defaulting to 'Solution'")
        return 'Solution'
    
    def _extract_method_name(self) -> str:
        """Extract the method name from the main class."""
        lines = self.code.split('\n')
        in_target_class = False
        
        for line in lines:
            if f'class {self.class_name}' in line:
                in_target_class = True
                continue
            
            if in_target_class and line and not line[0].isspace() and 'class' in line:
                in_target_class = False
            
            if in_target_class:
                match = re.search(r'def\s+(\w+)\s*\(', line)
                if match:
                    method = match.group(1)
                    if not method.startswith('__'):
                        self._logger.debug(f"Found method name: {method}")
                        return method
        
        # Fallback: find any non-dunder method
        match = re.search(r'def\s+(?!__)(\w+)\s*\(', self.code)
        if match:
            method = match.group(1)
            self._logger.debug(f"Found fallback method name: {method}")
            return method
        
        self._logger.warning("Could not find method name, using default 'solve'")
        return 'solve'
    
    def _extract_parameter_info(self) -> List[Tuple[str, str]]:
        """Extract parameter names and types from method signature."""
        lines = self.code.split('\n')
        in_target_class = False
        
        for line in lines:
            if f'class {self.class_name}' in line:
                in_target_class = True
                continue
            
            if in_target_class and line.strip().startswith('class ') and self.class_name not in line:
                in_target_class = False
                continue
            
            if in_target_class and 'def ' in line and '__' not in line:
                params = self._parse_method_signature(line)
                if params is not None:
                    self._logger.debug(f"Extracted {len(params)} parameters")
                    return params
        
        self._logger.warning("Could not extract parameter info")
        return []
    
    def _parse_method_signature(self, line: str) -> Optional[List[Tuple[str, str]]]:
        """Parse a method signature line to extract parameters."""
        match = re.search(r'def\s+\w+\s*\(\s*self\s*(?:,\s*([^)]+))?\)', line)
        
        if not match or not match.group(1):
            return []
        
        params_str = match.group(1)
        params = []
        
        # Split by comma, respecting brackets
        current_param = ""
        bracket_depth = 0
        
        for char in params_str + ',':
            if char in '[{(':
                bracket_depth += 1
                current_param += char
            elif char in ']})':
                bracket_depth -= 1
                current_param += char
            elif char == ',' and bracket_depth == 0:
                if current_param.strip():
                    param_info = self._parse_parameter(current_param.strip())
                    if param_info:
                        params.append(param_info)
                current_param = ""
            else:
                current_param += char
        
        return params
    
    def _parse_parameter(self, param_str: str) -> Optional[Tuple[str, str]]:
        """Parse a single parameter string into (name, type)."""
        # Remove default values
        param_clean = param_str.split('=')[0].strip()
        
        if ':' in param_clean:
            name, type_hint = param_clean.split(':', 1)
            return (name.strip(), type_hint.strip())
        else:
            return (param_clean, 'Any')
    
    def _extract_return_type(self) -> str:
        """Extract return type from method signature."""
        match = re.search(r'->\s*([^:]+):', self.code)
        if match:
            return_type = match.group(1).strip()
            self._logger.debug(f"Found return type: {return_type}")
            return return_type
        
        self._logger.debug("No return type found, using 'Any'")
        return 'Any'
    
    def _count_method_params(self) -> int:
        """Count the number of parameters in the method (excluding self)."""
        match = re.search(r'def\s+\w+\s*\(([^)]+)\)', self.code)
        if match:
            params_str = match.group(1)
            # Split by comma, but respect brackets
            params = []
            current = ""
            bracket_depth = 0
            
            for char in params_str:
                if char in '[{(':
                    bracket_depth += 1
                    current += char
                elif char in ']})':
                    bracket_depth -= 1
                    current += char
                elif char == ',' and bracket_depth == 0:
                    if current.strip():
                        params.append(current.strip())
                    current = ""
                else:
                    current += char
            
            if current.strip():
                params.append(current.strip())
            
            # Exclude 'self' parameter
            count = len([p for p in params if 'self' not in p.strip()])
            self._logger.debug(f"Method has {count} parameters")
            return count
        return 0
    
    # ========================================================================
    # Helper Detection
    # ========================================================================
    
    def _detect_helpers_needed(self) -> Dict[str, bool]:
        """Detect what helper functions are needed by analyzing the code."""
        helpers = {
            'listnode': 'ListNode' in self.code and 'class ListNode' in self.code,
            'treenode': 'TreeNode' in self.code and 'class TreeNode' in self.code,
        }

        needed = [k for k, v in helpers.items() if v]
        if needed:
            self._logger.debug(f"Helpers needed: {needed}")

        return helpers
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    @property
    def instance_name(self) -> str:
        """Get the lowercase instance name for the class."""
        return self.class_name.lower() if self.class_name else 'solution'
    
    def needs_conversion(self, param_type: str) -> Optional[str]:
        """Check if parameter type needs conversion."""
        if 'ListNode' in param_type:
            return 'list_to_listnode'
        elif 'TreeNode' in param_type:
            return 'list_to_treenode'
        return None
    
    def find_param_type(self, param_name: str) -> Optional[str]:
        """Find the type for a given parameter name."""
        for info_name, info_type in self.param_info:
            if info_name == param_name:
                return info_type
        return None
    
    
# =========================================================================
# Python Formatter
# ==========================================================================

class PythonFormatter(BaseFormatter):
    """Formats LeetCode problems as Python files."""

    def __init__(self):
        """Initialize the formatter with a logger."""
        self.logger = get_logger()

    def format(self, problem: Problem) -> str:
        """Generate complete Python file content."""
        detail = problem.problem_detail
        self.logger.debug(f"Starting format for problem #{detail.id}: {detail.title}")

        try:
            class_body = self._get_class_body(problem)
            imports_section = self._compute_imports_section(problem)
            description = self._format_description(detail.description)

            # Context inspects the class body for metadata (class name, method
            # name, param info). Imports aren't relevant to its analysis.
            ctx = FormatContext(
                code=class_body,
                description=detail.description,
                _logger=self.logger,
            )

            content = self._build_file_content(
                problem, description, imports_section, class_body, ctx,
            )
            self.logger.debug(f"Successfully formatted problem #{detail.id}")
            return content

        except Exception as e:
            self.logger.error(f"Error formatting problem #{detail.id}: {e}", exc_info=True)
            raise

    # ========================================================================
    # Main Content Building
    # ========================================================================

    def _build_file_content(
        self, problem: Problem, description: str,
        imports_section: str, class_body: str, ctx: FormatContext,
    ) -> str:
        """Assemble the placed solution.py:

        docstring -> PROBLEM DESCRIPTION -> imports -> SOLUTION -> TEST.

        Imports sit between description and solution so the user reads
        the problem, sees what stdlib is available, then dives into the
        class. Matches the convention requested for cross-language
        consistency (Java + C++ get the same layout).
        """
        main_block = self._generate_main_block(ctx)
        detail = problem.problem_detail

        return f'''"""
LeetCode Problem #{detail.id}: {detail.title}
Difficulty: {detail.difficulty}
"""

# ============================================================================
# PROBLEM DESCRIPTION
# ============================================================================
{description}

{imports_section}

# ============================================================================
# SOLUTION
# ============================================================================

{class_body}

# ============================================================================
# TEST
# ============================================================================

{main_block}
'''

    def _generate_main_block(self, ctx: FormatContext) -> str:
        """Generate the `if __name__ == "__main__":` block with a TODO placeholder.

        The full test suite runs via `dojo test`. We only emit a placeholder
        here so the user has a hook to edit when they want a quick local run.
        """
        lines = ['if __name__ == "__main__":']
        lines.append(f'    {ctx.instance_name} = {ctx.class_name}()')
        lines.append('')
        lines.append('    # TODO: edit me, or run `dojo test` for the full suite')
        args = ', '.join(self._get_default_arg(p[1]) for p in ctx.param_info)
        lines.append(f'    result = {ctx.instance_name}.{ctx.method_name}({args})')
        lines.append('    print(result)')
        return '\n'.join(lines)

    def _get_default_arg(self, param_type: str) -> str:
        """Get default argument value for a Python type."""
        defaults = {
            'int': '0',
            'float': '0.0',
            'str': '""',
            'bool': 'False',
            'List': '[]',
            'Optional': 'None',
        }

        for type_name, default in defaults.items():
            if type_name in param_type:
                return default

        if 'List' in param_type:
            return '[]'

        return 'None'
    
    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================
    
    def _get_class_body(self, problem: Problem) -> str:
        """Extract the `class Solution:` body, sans imports and node classes.

        Node-class comment blocks (`# class TreeNode:` / `# class ListNode:`)
        are pulled out — they become sibling modules via `extra_files()`.
        Any inline import lines from the snippet are stripped so the
        imports section owns them all; the typical LeetCode Python
        snippet doesn't have any, but be defensive.
        """
        detail = problem.problem_detail
        self.logger.debug(f"Extracting Python class body for problem #{detail.id}")

        code = problem.get_snippet(CodeLanguage.PYTHON)
        if not code:
            self.logger.warning(f"No Python3 snippet found for problem #{detail.id}")
            return "# No Python template available"

        code, _ = self._extract_node_classes(code)
        code = self._ensure_pass_in_methods(code)
        code = self._strip_top_level_imports(code)
        return code.strip("\n") + "\n"

    def _compute_imports_section(self, problem: Problem) -> str:
        """Build the import block placed between description and SOLUTION.

        Order:
          1. Baseline stdlib (`typing`, `collections`, `heapq`, ...)
          2. Sibling node modules (`from tree_node import TreeNode`, etc.)

        The baseline covers every typing name the LeetCode snippets
        actually reference, so we no longer need the regex-driven
        `_extract_imports` pass — it would only duplicate what's
        already there.
        """
        snippet = problem.get_snippet(CodeLanguage.PYTHON) or ""
        _, extracted = self._extract_node_classes(snippet)

        node_imports = [
            f"from {_PYTHON_NODE_MODULES.get(name, name.lower())} import {name}"
            for name in extracted
        ]
        lines = list(_PYTHON_BASELINE_IMPORTS) + node_imports
        return "\n".join(lines)

    def _strip_top_level_imports(self, code: str) -> str:
        """Remove any `import`/`from ... import` lines at top level."""
        out = []
        for line in code.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                continue
            out.append(line)
        return "\n".join(out)

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        """Sibling files: one per extracted node class."""
        snippet = problem.get_snippet(CodeLanguage.PYTHON) or ""
        _, extracted = self._extract_node_classes(snippet)
        return {
            f"{_PYTHON_NODE_MODULES.get(name, name.lower())}.py": body
            for name, body in extracted.items()
        }
    
    def _extract_node_classes(self, code: str) -> Tuple[str, Dict[str, str]]:
        """Find `# class X:` comment blocks; pull them out of the snippet.

        Returns a tuple of (stripped_code, {class_name: body}). `body` is
        the unwrapped class definition, ready to be written to its own
        module file. `stripped_code` is the snippet with the comment
        blocks removed entirely (replaced by an `import` line back in the
        caller).
        """
        self.logger.debug("Extracting commented node-class definitions")

        lines = code.split("\n")
        result: List[str] = []
        extracted: Dict[str, str] = {}

        in_block = False
        block_lines: List[str] = []
        block_class: Optional[str] = None
        base_indent = 0

        for line in lines:
            stripped = line.strip()

            if not in_block and stripped.startswith("# class ") and ":" in stripped:
                in_block = True
                base_indent = len(line) - len(line.lstrip())
                uncommented = line[base_indent:].lstrip("#").lstrip()
                match = re.match(r"class\s+(\w+)", uncommented)
                block_class = match.group(1) if match else "UnknownNode"
                self.logger.debug(f"Found commented node class: {block_class}")
                block_lines = [uncommented]
                # Drop a leading "# Definition for ..." comment that
                # belongs to this block — it's a leader, not part of
                # the class declaration, and looks orphaned otherwise.
                if result and result[-1].lstrip().startswith("# Definition for"):
                    result.pop()
            elif in_block and stripped.startswith("#"):
                line_indent = len(line) - len(line.lstrip())
                if line_indent >= base_indent:
                    uncommented_line = line[base_indent:].lstrip("#")
                    if uncommented_line and not uncommented_line.isspace():
                        if uncommented_line.startswith(" "):
                            uncommented_line = uncommented_line[1:]
                        block_lines.append(uncommented_line)
                    else:
                        block_lines.append("")
                else:
                    block_lines.append(line.lstrip("#").lstrip())
            elif in_block and not stripped.startswith("#"):
                # Block ends — store the extracted definition; the comment
                # block itself does NOT go into result.
                if block_class is not None:
                    extracted[block_class] = "\n".join(block_lines).rstrip() + "\n"
                in_block = False
                block_lines = []
                block_class = None
                result.append(line)
            else:
                result.append(line)

        if in_block and block_class is not None:
            extracted[block_class] = "\n".join(block_lines).rstrip() + "\n"

        return "\n".join(result), extracted
    
    def _extract_imports(self, code: str) -> str:
        """Extract required typing imports."""
        import_types = {
            'List[': 'List',
            'Optional[': 'Optional',
            'Dict[': 'Dict',
            'Dictionary[': 'Dict',
            'Set[': 'Set',
            'Tuple[': 'Tuple',
            'Union[': 'Union',
            'Deque[': 'Deque',
            'deque': 'Deque',
        }
        
        imports = set()
        for pattern, import_name in import_types.items():
            if pattern in code:
                imports.add(import_name)
        
        if imports:
            typing_imports = sorted(imports)
            self.logger.debug(f"Found typing imports: {typing_imports}")
            return f"from typing import {', '.join(typing_imports)}"
        
        return ""
    
    def _ensure_pass_in_methods(self, code: str) -> str:
        """Add pass to empty methods."""
        self.logger.debug("Ensuring pass statements in empty methods")
        
        lines = code.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            result.append(line)
            
            stripped = line.strip()
            if stripped.startswith('#'):
                i += 1
                continue
            
            if 'def ' in line and line.strip().endswith(':'):
                if self._is_empty_method(lines, i):
                    current_indent = len(line) - len(line.lstrip())
                    result.append(' ' * (current_indent + 4) + 'pass')
                    self.logger.debug(f"Added pass to empty method: {stripped}")
            
            i += 1
        
        return '\n'.join(result)
    
    def _is_empty_method(self, lines: List[str], method_line_idx: int) -> bool:
        """Check if a method definition is empty."""
        if method_line_idx + 1 >= len(lines):
            return True
        
        next_line = lines[method_line_idx + 1]
        next_stripped = next_line.strip()
        
        if next_stripped.startswith('#'):
            return False
        
        current_indent = len(lines[method_line_idx]) - len(lines[method_line_idx].lstrip())
        next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else current_indent
        
        return next_indent <= current_indent or not next_line.strip()
    
    # ========================================================================
    # Description Formatting
    # ========================================================================
    
    def _format_description(self, html_content: str) -> str:
        """Convert HTML to commented text."""
        self.logger.debug("Formatting problem description")
        
        try:
            text = self._html_to_text(html_content)
            lines = text.strip().split('\n')
            return '\n'.join(f"# {line}" if line else "#" for line in lines)
        except Exception as e:
            self.logger.error(f"Error formatting description: {e}")
            return "# Error formatting description"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text."""
        text = re.sub(r'<[^>]+>', '', html_content)
        text = unescape(text)
        return text