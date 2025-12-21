"""
Python formatter for LeetCode problems with intelligent test generation.
"""

import re
from typing import Tuple, List, Optional, Dict
from html import unescape

from bytedojo.core.leetcode.models import Problem
from bytedojo.core.leetcode.formatters.base import BaseFormatter
from bytedojo.core.logger import get_logger


class PythonFormatter(BaseFormatter):
    """Formats LeetCode problems as Python files with smart test generation."""
    
    # Helper function templates
    LISTNODE_HELPERS = '''
    def list_to_listnode(arr):
        """Convert array to ListNode."""
        if not arr:
            return None
        head = ListNode(arr[0])
        current = head
        for val in arr[1:]:
            current.next = ListNode(val)
            current = current.next
        return head
    
    def listnode_to_list(node):
        """Convert ListNode to array."""
        result = []
        while node:
            result.append(node.val)
            node = node.next
        return result
'''

    TREENODE_HELPERS = '''
    def list_to_treenode(arr):
        """Convert array to TreeNode (level-order)."""
        if not arr or arr[0] is None:
            return None
        
        root = TreeNode(arr[0])
        queue = [root]
        i = 1
        
        while queue and i < len(arr):
            node = queue.pop(0)
            
            if i < len(arr) and arr[i] is not None:
                node.left = TreeNode(arr[i])
                queue.append(node.left)
            i += 1
            
            if i < len(arr) and arr[i] is not None:
                node.right = TreeNode(arr[i])
                queue.append(node.right)
            i += 1
        
        return root
    
    def treenode_to_list(root):
        """Convert TreeNode to array (level-order)."""
        if not root:
            return []
        
        result = []
        queue = [root]
        
        while queue:
            node = queue.pop(0)
            if node:
                result.append(node.val)
                queue.append(node.left)
                queue.append(node.right)
            else:
                result.append(None)
        
        # Remove trailing None values
        while result and result[-1] is None:
            result.pop()
        
        return result
'''

    def __init__(self):
        """Initialize the formatter with a logger."""
        self.logger = get_logger()

    def format(self, problem: Problem) -> str:
        """Generate complete Python file content."""
        self.logger.debug(f"Starting format for problem #{problem.id}: {problem.title}")
        
        try:
            code_template = self._get_python_code(problem)
            description = self._format_description(problem.description)
            test_cases = self._format_test_cases(problem, code_template)
            
            content = self._build_file_content(problem, description, code_template, test_cases)
            
            self.logger.debug(f"Successfully formatted problem #{problem.id}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error formatting problem #{problem.id}: {e}", exc_info=True)
            raise
    
    # ========================================================================
    # Main Content Building
    # ========================================================================
    
    def _build_file_content(self, problem: Problem, description: str, code_template: str, test_cases: str) -> str:
        """Build the complete file content from components."""
        return f'''"""
LeetCode Problem #{problem.id}: {problem.title}
Difficulty: {problem.difficulty}
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
# TESTS
# ============================================================================

def run_tests():
    """Run test cases for the problem."""
    solution = Solution()
{test_cases}


if __name__ == "__main__":
    run_tests()
'''
    
    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================
    
    def _get_python_code(self, problem: Problem) -> str:
        """Extract and process Python code."""
        self.logger.debug(f"Extracting Python code for problem #{problem.id}")
        
        code = problem.get_snippet('Python3')
        if not code:
            self.logger.warning(f"No Python3 snippet found for problem #{problem.id}")
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
        
        # HTML entity replacements
        entities = {
            '&nbsp;': ' ',
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
        }
        
        for entity, replacement in entities.items():
            text = text.replace(entity, replacement)
        
        return text
    
    # ========================================================================
    # Method Analysis
    # ========================================================================
    
    def _extract_method_name(self, code: str) -> str:
        """Extract the method name from the Solution class."""
        self.logger.debug("Extracting method name from Solution class")
        
        lines = code.split('\n')
        in_solution_class = False
        
        for line in lines:
            if 'class Solution' in line:
                in_solution_class = True
                continue
            
            if in_solution_class and line and not line[0].isspace() and 'class' in line:
                in_solution_class = False
            
            if in_solution_class:
                match = re.search(r'def\s+(\w+)\s*\(', line)
                if match:
                    method = match.group(1)
                    if not method.startswith('__'):
                        self.logger.debug(f"Found method name: {method}")
                        return method
        
        # Fallback: find any non-dunder method
        match = re.search(r'def\s+(?!__)(\w+)\s*\(', code)
        if match:
            method = match.group(1)
            self.logger.debug(f"Found fallback method name: {method}")
            return method
        
        self.logger.warning("Could not find method name, using default 'solve'")
        return 'solve'
    
    def _extract_parameter_info(self, code: str) -> List[Tuple[str, str]]:
        """Extract parameter names and types from method signature."""
        self.logger.debug("Extracting parameter information")
        
        lines = code.split('\n')
        in_solution = False
        
        for line in lines:
            if 'class Solution' in line:
                in_solution = True
                continue
            
            if in_solution and line.strip().startswith('class ') and 'Solution' not in line:
                in_solution = False
                continue
            
            if in_solution and 'def ' in line and '__' not in line:
                params = self._parse_method_signature(line)
                if params is not None:
                    self.logger.debug(f"Extracted parameters: {params}")
                    return params
        
        self.logger.warning("Could not extract parameter info")
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
    
    def _get_return_type(self, code: str) -> str:
        """Extract return type from method signature."""
        match = re.search(r'->\s*([^:]+):', code)
        if match:
            return_type = match.group(1).strip()
            self.logger.debug(f"Found return type: {return_type}")
            return return_type
        
        self.logger.debug("No return type found, using 'Any'")
        return 'Any'
    
    def _count_method_params(self, code: str) -> int:
        """Count the number of parameters in the method (excluding self)."""
        match = re.search(r'def\s+\w+\s*\(([^)]+)\)', code)
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
            return len([p for p in params if 'self' not in p.strip()])
        return 0
    
    # ========================================================================
    # Helper Detection
    # ========================================================================
    
    def _detect_helpers_needed(self, code: str) -> Dict[str, bool]:
        """Detect what helper functions are needed by analyzing the code."""
        helpers = {
            'listnode': 'ListNode' in code and 'class ListNode' in code,
            'treenode': 'TreeNode' in code and 'class TreeNode' in code,
        }
        
        self.logger.debug(f"Helpers needed: {[k for k, v in helpers.items() if v]}")
        return helpers
    
    def _needs_conversion(self, param_type: str) -> Optional[str]:
        """Check if parameter type needs conversion."""
        if 'ListNode' in param_type:
            return 'list_to_listnode'
        elif 'TreeNode' in param_type:
            return 'list_to_treenode'
        return None
    
    # ========================================================================
    # Example Parsing
    # ========================================================================
    
    def _extract_test_examples(self, description: str) -> List[Tuple[str, str, str]]:
        """Extract test examples from problem description."""
        self.logger.debug("Extracting test examples from description")
        
        try:
            description = unescape(description)
            text = re.sub(r'<[^>]+>', '\n', description)
            
            examples = []
            example_pattern = r'Example\s+\d+:(.*?)(?=Example\s+\d+:|Constraints:|$)'
            
            for match in re.finditer(example_pattern, text, re.DOTALL | re.IGNORECASE):
                example_text = match.group(1).strip()
                example_data = self._parse_example_text(example_text)
                
                if example_data:
                    examples.append(example_data)
            
            self.logger.debug(f"Extracted {len(examples)} examples")
            return examples
            
        except Exception as e:
            self.logger.error(f"Error extracting test examples: {e}")
            return []
    
    def _parse_example_text(self, example_text: str) -> Optional[Tuple[str, str, str]]:
        """Parse a single example text into (input, output, explanation)."""
        input_match = re.search(r'Input:\s*([^\n]+(?:\n(?!Output:)[^\n]+)*)', example_text)
        input_text = input_match.group(1).strip() if input_match else ""
        
        output_match = re.search(r'Output:\s*([^\n]+(?:\n(?!Explanation:)[^\n]+)*)', example_text)
        output_text = output_match.group(1).strip() if output_match else ""
        
        explanation_match = re.search(r'Explanation:\s*([^\n]+.*?)$', example_text, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        
        if input_text:
            return (input_text, output_text, explanation)
        
        return None
    
    def _parse_input_line(self, input_text: str) -> List[Tuple[str, str]]:
        """Parse input line to extract parameter names and values."""
        self.logger.debug(f"Parsing input line: {input_text[:100]}...")
        
        params = []
        current_part = ""
        in_quotes = False
        quote_char = None
        bracket_depth = 0
        
        for char in input_text + ',':
            if char in ('"', "'") and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current_part += char
            elif char in '[{(':
                bracket_depth += 1
                current_part += char
            elif char in ']})':
                bracket_depth -= 1
                current_part += char
            elif char == ',' and not in_quotes and bracket_depth == 0:
                if current_part.strip():
                    param = self._parse_input_parameter(current_part.strip())
                    if param:
                        params.append(param)
                current_part = ""
            else:
                current_part += char
        
        self.logger.debug(f"Parsed {len(params)} input parameters")
        return params
    
    def _parse_input_parameter(self, param_str: str) -> Optional[Tuple[str, str]]:
        """Parse a single input parameter string."""
        match = re.search(r'(\w+)\s*=\s*(.+)', param_str)
        if not match:
            return None
        
        name = match.group(1).strip()
        value = match.group(2).strip()
        
        # Normalize value
        value = value.replace('null', 'None')
        
        # Convert double quotes to single quotes
        if value.startswith('"') and value.endswith('"'):
            inner_value = value[1:-1].replace("'", "\\'")
            value = f"'{inner_value}'"
        
        return (name, value)
    
    def _parse_output_line(self, output_text: str) -> str:
        """Parse output line to extract just the return value."""
        output_text = output_text.strip()
        
        # Handle list output
        if output_text.startswith('['):
            return self._extract_list_value(output_text)
        
        # Handle dict/set output
        if output_text.startswith('{'):
            return self._extract_dict_value(output_text)
        
        # Handle comma-separated output (take first value)
        if ',' in output_text:
            return output_text.split(',')[0].strip()
        
        return output_text
    
    def _extract_list_value(self, text: str) -> str:
        """Extract a complete list value from text."""
        bracket_count = 0
        for i, char in enumerate(text):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    return text[:i+1]
        return text
    
    def _extract_dict_value(self, text: str) -> str:
        """Extract a complete dict/set value from text."""
        bracket_count = 0
        for i, char in enumerate(text):
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    return text[:i+1]
        return text
    
    # ========================================================================
    # Test Case Formatting
    # ========================================================================
    
    def _format_test_cases(self, problem: Problem, code: str) -> str:
        """Format test cases into runnable code with smart helper detection."""
        self.logger.debug("Formatting test cases")
        
        try:
            method_name = self._extract_method_name(code)
            helpers_needed = self._detect_helpers_needed(code)
            param_info = self._extract_parameter_info(code)
            return_type = self._get_return_type(code)
            
            examples = self._extract_test_examples(problem.description)
            
            if not examples:
                self.logger.debug("No examples found, using basic test case format")
                return self._format_basic_test_cases(problem.test_cases, code)
            
            return self._build_test_code(
                examples, method_name, helpers_needed, param_info, return_type
            )
            
        except Exception as e:
            self.logger.error(f"Error formatting test cases: {e}", exc_info=True)
            return '    # Error generating test cases\n    pass'
    
    def _build_test_code(self, examples: List[Tuple[str, str, str]], method_name: str, helpers_needed: Dict[str, bool], param_info: List[Tuple[str, str]], return_type: str) -> str:
        """Build the complete test code from examples."""
        test_code = []
        
        # Add helper functions
        if helpers_needed.get('listnode'): test_code.extend(self.LISTNODE_HELPERS.split('\n'))
        if helpers_needed.get('treenode'): test_code.extend(self.TREENODE_HELPERS.split('\n'))
        
        test_code.append('')
        
        # Generate test assertions
        for test_num, (input_text, output_text, explanation) in enumerate(examples, 1):
            assertion = self._build_test_assertion(input_text, output_text, method_name, param_info, return_type)
            
            if assertion:
                test_code.append(assertion)
                test_code.append('')
        
        return '\n'.join(test_code)
    
    def _build_test_assertion(self, input_text: str, output_text: str, method_name: str, param_info: List[Tuple[str, str]], return_type: str) -> Optional[str]:
        """Build a single test assertion."""
        try:
            input_params = self._parse_input_line(input_text)
            if not input_params:
                return None
            
            expected_return = self._parse_output_line(output_text)
            expected_return = self._normalize_value(expected_return)
            
            # Build function call
            call_params = self._build_call_parameters(input_params, param_info)
            params_str = ', '.join(call_params)
            call = f'solution.{method_name}({params_str})'
            
            # Apply return type conversion if needed
            call = self._apply_return_conversion(call, return_type)
            
            return f'    assert {expected_return} == {call}'
            
        except Exception as e:
            self.logger.error(f"Error building test assertion: {e}")
            return None
    
    def _build_call_parameters(self, input_params: List[Tuple[str, str]], param_info: List[Tuple[str, str]]) -> List[str]:
        """Build the list of function call parameters with conversions."""
        call_params = []
        
        for param_name, param_value in input_params:
            param_type = self._find_param_type(param_name, param_info)
            converter = self._needs_conversion(param_type) if param_type else None
            
            if converter:
                call_params.append(f'{converter}({param_value})')
                self.logger.debug(f"Applying {converter} to {param_name}")
            else:
                call_params.append(param_value)
        
        return call_params
    
    def _find_param_type(self, param_name: str, param_info: List[Tuple[str, str]]) -> Optional[str]:
        """Find the type for a given parameter name."""
        for info_name, info_type in param_info:
            if info_name == param_name:
                return info_type
        return None
    
    def _apply_return_conversion(self, call: str, return_type: str) -> str:
        """Apply conversion to return value if needed."""
        if 'ListNode' in return_type:
            self.logger.debug("Applying listnode_to_list to return value")
            return f'listnode_to_list({call})'
        elif 'TreeNode' in return_type:
            self.logger.debug("Applying treenode_to_list to return value")
            return f'treenode_to_list({call})'
        return call
    
    def _normalize_value(self, value: str) -> str:
        """Normalize a value string (convert true/false/null)."""
        value = value.replace('null', 'None')
        
        if value.lower() == 'true':
            return 'True'
        elif value.lower() == 'false':
            return 'False'
        
        return value
    
    def _format_basic_test_cases(self, test_cases: str, code: str) -> str:
        """Fallback: format basic test cases when examples can't be parsed."""
        self.logger.debug("Using basic test case format")
        
        if not test_cases: return '    # Add your test cases here\n    pass'
        
        method_name = self._extract_method_name(code)
        lines = test_cases.strip().split('\n')
        param_count = self._count_method_params(code)
        
        test_code = []
        test_code.append('    # NOTE: Expected outputs not available - add assertions manually')
        test_code.append('')
        
        if param_count > 0 and len(lines) % param_count == 0:
            for i in range(0, len(lines), param_count):
                test_num = (i // param_count) + 1
                inputs = lines[i:i + param_count]
                
                if len(inputs) == 1:
                    call = f'solution.{method_name}({inputs[0]})'
                else:
                    params_str = ', '.join(inputs)
                    call = f'solution.{method_name}({params_str})'
                
                test_code.append(f'result{test_num} = {call}')
                test_code.append(f'print(f"Test {test_num}: {{result{test_num}}}")')
                test_code.append('')
        
        return '\n'.join(test_code)