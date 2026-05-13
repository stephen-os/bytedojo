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


#: Baseline imports preincluded in every fetched solution.java. The
#: single `java.util.*` import covers List, ArrayList, HashMap, HashSet,
#: LinkedList, Queue, Deque, ArrayDeque, Map, Set, Stack, PriorityQueue,
#: Collections, Arrays, Comparator, etc. — everything a typical
#: LeetCode Java solution reaches for.
_JAVA_BASELINE_IMPORTS: Tuple[str, ...] = (
    "import java.util.*;",
)


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
        """Extract the main class name from the snippet."""
        match = re.search(r'\bclass\s+(\w+)\s*[{<]', self.code)
        if match:
            class_name = match.group(1)
            self._logger.debug(f"Found class name: {class_name}")
            return class_name
        self._logger.warning("No class found, defaulting to 'Solution'")
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
        """Assemble the placed solution.java.

        Layout: file docstring -> PROBLEM DESCRIPTION -> imports ->
        SOLUTION -> TEST. Java's grammar allows imports anywhere before
        the first type declaration, so placing them between the
        description block and the class works cleanly.
        """
        detail = problem.problem_detail
        description = self._format_description(detail.description)
        main_class = self._generate_main_class(ctx)
        imports_section = self._compute_imports_section()

        return f'''/**
 * LeetCode Problem #{detail.id}: {detail.title}
 * Difficulty: {detail.difficulty}
 */

// ============================================================================
// PROBLEM DESCRIPTION
// ============================================================================
{description}

{imports_section}

// ============================================================================
// SOLUTION
// ============================================================================

{code_template}

// ============================================================================
// TEST
// ============================================================================

{main_class}
'''

    def _compute_imports_section(self) -> str:
        """Baseline `java.util.*` covers everything LeetCode-style needs.

        TreeNode / ListNode siblings live in the same default package, so
        no explicit imports are needed for those — they just resolve.
        """
        return "\n".join(_JAVA_BASELINE_IMPORTS)

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
        """Extract Java code, pulling embedded node classes out.

        LeetCode wraps `TreeNode` / `ListNode` definitions in JavaDoc on
        top of the starter snippet. We *remove* those blocks from the
        snippet (they become their own `ListNode.java` / `TreeNode.java`
        siblings via `extra_files()`). The user's `Solution.java` stays
        focused on Solution; node classes follow Java's one-public-class-
        per-file convention and `javac *.java` picks them up alongside.
        """
        detail = problem.problem_detail
        self.logger.debug(f"Extracting Java code for problem #{detail.id}")

        code = problem.get_snippet(CodeLanguage.JAVA)
        if not code:
            self.logger.warning(f"No Java snippet found for problem #{detail.id}")
            return "// No Java template available"

        stripped, _ = self._extract_node_classes(code)
        return stripped

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        """Emit one `<ClassName>.java` per node class found in the snippet."""
        snippet = problem.get_snippet(CodeLanguage.JAVA) or ""
        _, extracted = self._extract_node_classes(snippet)
        return {f"{name}.java": body for name, body in extracted.items()}

    def _extract_node_classes(self, code: str) -> Tuple[str, Dict[str, str]]:
        """Pull JavaDoc-wrapped node-class definitions out of the snippet.

        Returns (stripped_code, {class_name: body}). The `body` is a
        complete `public class X { ... }` declaration ready to drop into
        its own .java file. The stripped code has the JavaDoc block
        replaced by nothing — solution.java becomes Solution-only.
        """
        block_re = re.compile(r'/\*\*(.*?)\*/\s*\n?', re.DOTALL)
        extracted: Dict[str, str] = {}

        def replacer(match):
            body = match.group(1)
            class_match = re.search(
                r'^\s*\*\s*public\s+class\s+(\w+)\b', body, re.MULTILINE
            )
            if not class_match:
                # Plain JavaDoc — leave it alone.
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
                f"Extracted JavaDoc node-class block: {class_name} "
                f"({len(out_lines)} lines)"
            )
            # Empty replacement — the block is gone from the source entirely.
            return ''

        new_code = block_re.sub(replacer, code)
        return new_code, extracted

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
