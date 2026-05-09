"""
Python formatter for LeetCode problems with intelligent test generation.
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from html import unescape

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.test_case import TestCase
from bytedojo.core.formatters.base import BaseFormatter
from bytedojo.core.logger import get_logger

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
    test_cases: List[TestCase]  # Pre-parsed test cases

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
            # Extract and process code
            code_template = self._get_python_code(problem)
            description = self._format_description(detail.description)

            # Create context with all metadata and pre-parsed test examples
            ctx = FormatContext(
                code=code_template,
                description=detail.description,
                test_cases=problem.test_cases,
                _logger=self.logger
            )

            # Build final content
            content = self._build_file_content(problem, description, code_template, ctx)

            self.logger.debug(f"Successfully formatted problem #{detail.id}")
            return content

        except Exception as e:
            self.logger.error(f"Error formatting problem #{detail.id}: {e}", exc_info=True)
            raise
    
    # ========================================================================
    # Main Content Building
    # ========================================================================
    
    def _build_file_content(self, problem: Problem, description: str, code_template: str, ctx: FormatContext) -> str:
        """Build the complete file content from components."""
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

# ============================================================================
# SOLUTION
# ============================================================================

{code_template}

# ============================================================================
# TEST
# ============================================================================

{main_block}
'''

    def _generate_main_block(self, ctx: FormatContext) -> str:
        """Generate main block with test examples."""
        lines = ['if __name__ == "__main__":']
        lines.append(f'    {ctx.instance_name} = {ctx.class_name}()')
        lines.append('')

        if ctx.test_cases:
            for i, example in enumerate(ctx.test_cases, 1):
                lines.append(f'    # Example {i}')
                test_call = self._generate_test_call(ctx, example.input, example.output, i)
                lines.extend(test_call)
                lines.append('')
        else:
            # Default placeholder
            lines.append('    # TODO: Add test cases')
            args = ', '.join(self._get_default_arg(p[1]) for p in ctx.param_info)
            lines.append(f'    result = {ctx.instance_name}.{ctx.method_name}({args})')
            lines.append('    print(result)')

        return '\n'.join(lines)

    def _generate_test_call(self, ctx: FormatContext, input_text: str, output_text: str, index: int) -> List[str]:
        """Generate Python code for a single test case."""
        lines = []

        # Parse input variables
        input_vars = self._parse_input_variables(input_text)

        # Generate variable assignments
        for param_name, param_type in ctx.param_info:
            if param_name in input_vars:
                value = self._convert_to_python_literal(input_vars[param_name])
                lines.append(f'    {param_name}{index} = {value}')

        # Generate method call
        args = ', '.join(f'{p[0]}{index}' for p in ctx.param_info if p[0] in input_vars)
        if not args:
            args = ', '.join(self._get_default_arg(p[1]) for p in ctx.param_info)

        lines.append(f'    result{index} = {ctx.instance_name}.{ctx.method_name}({args})')
        lines.append(f'    print(f"Result {index}: {{result{index}}}")')

        if output_text:
            lines.append(f'    # Expected: {output_text}')

        return lines

    def _parse_input_variables(self, input_text: str) -> Dict[str, str]:
        """Parse input line like 'nums = [2,7,11,15], target = 9' into dict."""
        result = {}
        pattern = r'(\w+)\s*=\s*'
        var_matches = list(re.finditer(pattern, input_text))

        for i, match in enumerate(var_matches):
            var_name = match.group(1)
            start = match.end()

            if i + 1 < len(var_matches):
                end = var_matches[i + 1].start()
                value = input_text[start:end].rstrip().rstrip(',').strip()
            else:
                value = input_text[start:].strip()

            value = value.rstrip(',').strip()
            result[var_name] = value

        return result

    def _convert_to_python_literal(self, value: str) -> str:
        """Convert LeetCode test case value to Python literal."""
        value = value.strip()

        # Boolean conversion
        if value.lower() == 'true':
            return 'True'
        if value.lower() == 'false':
            return 'False'

        # null -> None
        if value.lower() == 'null':
            return 'None'

        return value

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
    
    def _get_python_code(self, problem: Problem) -> str:
        """Extract and process Python code."""
        detail = problem.problem_detail
        self.logger.debug(f"Extracting Python code for problem #{detail.id}")

        code = problem.get_snippet(CodeLanguage.PYTHON)
        if not code:
            self.logger.warning(f"No Python3 snippet found for problem #{detail.id}")
            return "# No Python template available"
        
        self.logger.debug("Processing code: uncommenting classes, extracting imports")
        code = self._uncomment_class_definitions(code)
        imports = self._extract_imports(code)
        code = self._ensure_pass_in_methods(code)
        
        if imports:
            self.logger.debug(f"Adding imports: {imports}")
            code = imports + '\n\n' + code
        
        return code
    
    def _uncomment_class_definitions(self, code: str) -> str:
        """Uncomment ListNode, TreeNode, etc."""
        self.logger.debug("Uncommenting class definitions")
        
        lines = code.split('\n')
        result = []
        in_comment_block = False
        comment_block = []
        base_indent = 0
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('# class ') and ':' in stripped:
                self.logger.debug(f"Found commented class: {stripped}")
                in_comment_block = True
                base_indent = len(line) - len(line.lstrip())
                uncommented = line[base_indent:].lstrip('#').lstrip()
                comment_block = [uncommented]
            elif in_comment_block and stripped.startswith('#'):
                line_indent = len(line) - len(line.lstrip())
                if line_indent >= base_indent:
                    uncommented_line = line[base_indent:].lstrip('#')
                    if uncommented_line and not uncommented_line.isspace():
                        if uncommented_line.startswith(' '):
                            uncommented_line = uncommented_line[1:]
                        comment_block.append(uncommented_line)
                    else:
                        comment_block.append('')
                else:
                    comment_block.append(line.lstrip('#').lstrip())
            elif in_comment_block and not stripped.startswith('#'):
                result.extend(comment_block)
                result.append('')
                in_comment_block = False
                comment_block = []
                result.append(line)
            else:
                result.append(line)
        
        if comment_block:
            result.extend(comment_block)
            result.append('')
        
        return '\n'.join(result)
    
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