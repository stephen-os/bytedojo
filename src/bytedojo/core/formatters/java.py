"""
Java formatter for LeetCode problems with intelligent test generation.
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.base import BaseFormatter
from bytedojo.core.formatters.utils import (
    html_to_text,
    get_java_default,
)
from bytedojo.core.logger import get_logger


# =========================================================================
# Format Context
# ==========================================================================

@dataclass
class JavaFormatContext:
    """
    Context for formatting a single Java problem.
    Contains all extracted metadata to avoid redundant parsing.
    """
    code: str
    description: str

    # Extracted metadata (populated lazily)
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    param_info: List[Tuple[str, str]] = field(default_factory=list)  # [(name, type), ...]
    return_type: Optional[str] = None
    needs_arrays_import: bool = False
    needs_list_import: bool = False

    _logger: Optional[object] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize logger and extract metadata."""
        if self._logger is None:
            self._logger = get_logger()

        self._extract_metadata()

    def _extract_metadata(self):
        """Extract all metadata from code in one pass."""
        self._logger.debug("Extracting metadata from Java code")

        self.class_name = self._extract_class_name()
        self.method_name = self._extract_method_name()
        self.param_info = self._extract_parameter_info()
        self.return_type = self._extract_return_type()
        self._detect_imports_needed()

        self._logger.debug(
            f"Metadata extracted: class={self.class_name}, method={self.method_name}, "
            f"params={len(self.param_info)}, return_type={self.return_type}"
        )

    # ========================================================================
    # Class and Method Extraction
    # ========================================================================

    def _extract_class_name(self) -> str:
        """Extract the main class name."""
        match = re.search(r'class\s+(\w+)\s*\{', self.code)
        if match:
            class_name = match.group(1)
            self._logger.debug(f"Found class name: {class_name}")
            return class_name
        return 'Solution'

    def _extract_method_name(self) -> str:
        """Extract the main method name from the class."""
        # Pattern for Java method: public returnType methodName(params)
        match = re.search(
            r'public\s+[\w<>\[\],\s]+\s+(\w+)\s*\(',
            self.code
        )
        if match:
            method_name = match.group(1)
            self._logger.debug(f"Found method name: {method_name}")
            return method_name

        self._logger.warning("Could not find method name, using 'solve'")
        return 'solve'

    def _extract_parameter_info(self) -> List[Tuple[str, str]]:
        """Extract parameter names and types from method signature."""
        # Find the method signature
        match = re.search(
            r'public\s+[\w<>\[\],\s]+\s+\w+\s*\(([^)]*)\)',
            self.code
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
                    param_info = self._parse_java_parameter(param)
                    if param_info:
                        params.append(param_info)
                current_param = ""
            else:
                current_param += char

        self._logger.debug(f"Extracted {len(params)} parameters: {params}")
        return params

    def _parse_java_parameter(self, param_str: str) -> Optional[Tuple[str, str]]:
        """Parse a single Java parameter string into (name, type)."""
        # Java param format: "int[] nums" or "List<Integer> list"
        parts = param_str.strip().rsplit(' ', 1)
        if len(parts) == 2:
            param_type, param_name = parts
            return (param_name.strip(), param_type.strip())
        return None

    def _extract_return_type(self) -> str:
        """Extract return type from method signature."""
        match = re.search(
            r'public\s+([\w<>\[\],\s]+)\s+\w+\s*\(',
            self.code
        )
        if match:
            return_type = match.group(1).strip()
            self._logger.debug(f"Found return type: {return_type}")
            return return_type
        return 'void'

    def _detect_imports_needed(self):
        """Detect what imports are needed based on code and types."""
        all_types = self.code + self.return_type + ' '.join(t for _, t in self.param_info)

        # Check for array types that might need Arrays.toString()
        if '[]' in self.return_type or any('[]' in t for _, t in self.param_info):
            self.needs_arrays_import = True

        # Check for List types
        if 'List<' in all_types:
            self.needs_list_import = True

    # ========================================================================
    # Helper Properties
    # ========================================================================

    @property
    def instance_name(self) -> str:
        """Get the lowercase instance name for the class."""
        return self.class_name.lower() if self.class_name else 'solution'


# =========================================================================
# Java Formatter
# ==========================================================================

class JavaFormatter(BaseFormatter):
    """Formats LeetCode problems as Java files."""

    def __init__(self):
        """Initialize the formatter with a logger."""
        self.logger = get_logger()

    def format(self, problem: Problem) -> str:
        """Generate complete Java file content."""
        detail = problem.problem_detail
        self.logger.debug(f"Starting Java format for problem #{detail.id}: {detail.title}")

        try:
            code_template = self._get_java_code(problem)

            ctx = JavaFormatContext(
                code=code_template,
                description=detail.description,
                _logger=self.logger,
            )

            # Inject default return statement if needed
            code_template = self._inject_default_return(code_template, ctx.return_type)

            content = self._build_file_content(problem, code_template, ctx)

            self.logger.debug(f"Successfully formatted problem #{detail.id} as Java")
            return content

        except Exception as e:
            self.logger.error(f"Error formatting problem #{detail.id}: {e}", exc_info=True)
            raise

    # ========================================================================
    # Main Content Building
    # ========================================================================

    def _build_file_content(self, problem: Problem, code_template: str, ctx: JavaFormatContext) -> str:
        """Build the complete Java file content."""
        detail = problem.problem_detail
        imports = self._generate_imports(ctx)
        description = self._format_description(detail.description)
        main_class = self._generate_main_class(ctx)

        imports_section = '\n'.join(imports) + '\n\n' if imports else ''

        return f'''/**
 * LeetCode Problem #{detail.id}: {detail.title}
 * Difficulty: {detail.difficulty}
 */

{imports_section}// ============================================================================
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

{main_class}
'''

    def _generate_imports(self, ctx: JavaFormatContext) -> List[str]:
        """Generate required Java imports."""
        imports = []

        if ctx.needs_arrays_import:
            imports.append('import java.util.Arrays;')

        if ctx.needs_list_import:
            imports.append('import java.util.ArrayList;')
            imports.append('import java.util.List;')

        # Check for other common types in code
        if 'Map<' in ctx.code or 'HashMap' in ctx.code:
            imports.append('import java.util.HashMap;')
            imports.append('import java.util.Map;')

        if 'Set<' in ctx.code or 'HashSet' in ctx.code:
            imports.append('import java.util.HashSet;')
            imports.append('import java.util.Set;')

        if 'Queue<' in ctx.code or 'LinkedList' in ctx.code:
            imports.append('import java.util.LinkedList;')
            imports.append('import java.util.Queue;')

        if 'Stack<' in ctx.code:
            imports.append('import java.util.Stack;')

        if 'PriorityQueue<' in ctx.code:
            imports.append('import java.util.PriorityQueue;')

        return sorted(set(imports))

    def _generate_main_class(self, ctx: JavaFormatContext) -> str:
        """Generate the Main class with a TODO placeholder call.

        The full test suite runs via `dojo test`. We only emit a placeholder
        here so the user has a hook to edit when they want a quick local run.
        """
        lines = ['class Main {']
        lines.append('    public static void main(String[] args) {')
        lines.append(f'        {ctx.class_name} {ctx.instance_name} = new {ctx.class_name}();')
        lines.append('')
        lines.append('        // TODO: edit me, or run `dojo test` for the full suite')
        args = ', '.join(get_java_default(t) for _, t in ctx.param_info)
        if ctx.return_type != 'void':
            lines.append(f'        {ctx.return_type} result = {ctx.instance_name}.{ctx.method_name}({args});')
            lines.append(self._generate_print_statement('result', ctx.return_type))
        else:
            lines.append(f'        {ctx.instance_name}.{ctx.method_name}({args});')
        lines.append('    }')
        lines.append('}')
        return '\n'.join(lines)

    def _generate_print_statement(self, var_name: str, java_type: str) -> str:
        """Generate appropriate print statement for the type."""
        if '[]' in java_type and '[][]' not in java_type:
            return f'        System.out.println(Arrays.toString({var_name}));'
        elif '[][]' in java_type:
            return f'        System.out.println(Arrays.deepToString({var_name}));'
        else:
            return f'        System.out.println({var_name});'

    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================

    def _get_java_code(self, problem: Problem) -> str:
        """Extract and process Java code."""
        detail = problem.problem_detail
        self.logger.debug(f"Extracting Java code for problem #{detail.id}")

        code = problem.get_snippet(CodeLanguage.JAVA)
        if not code:
            self.logger.warning(f"No Java snippet found for problem #{detail.id}")
            return "// No Java template available"

        return code

    def _inject_default_return(self, code: str, return_type: str) -> str:
        """
        Inject a default return statement into an empty method body.

        Args:
            code: The Java code template
            return_type: The method's return type

        Returns:
            Code with default return statement injected
        """
        if return_type == 'void':
            return code

        default_value = get_java_default(return_type)

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
        """Convert HTML to Java comments."""
        self.logger.debug("Formatting problem description for Java")

        try:
            text = html_to_text(html_content)
            lines = text.strip().split('\n')
            return '\n'.join(f"// {line}" if line else "//" for line in lines)
        except Exception as e:
            self.logger.error(f"Error formatting description: {e}")
            return "// Error formatting description"
