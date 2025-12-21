"""
Python formatter for LeetCode problems with intelligent test generation.
"""

import re
from typing import Tuple, List, Optional, Dict
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

    def format(self, problem: Problem) -> str:
        """Generate complete Python file content."""
        code_template = self._get_python_code(problem)
        description = self._format_description(problem.description)
        test_cases = self._format_test_cases(problem, code_template)
        
        content = f'''"""
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
        return content
    
    def _get_python_code(self, problem: Problem) -> str:
        """Extract and process Python code."""
        code = problem.get_snippet('Python3')
        if not code:
            return "# No Python template available"
        
        code = self._uncomment_class_definitions(code)
        imports = self._extract_imports(code)
        code = self._ensure_pass_in_methods(code)
        
        if imports:
            code = imports + '\n\n' + code
        
        return code
    
    def _format_description(self, html_content: str) -> str:
        """Convert HTML to commented text."""
        text = re.sub(r'<[^>]+>', '', html_content)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        
        lines = text.strip().split('\n')
        return '\n'.join(f"# {line}" if line else "#" for line in lines)
    
    def _detect_helpers_needed(self, code: str) -> Dict[str, bool]:
        """
        Detect what helper functions are needed by analyzing the code.
        
        Args:
            code: Python code template
            
        Returns:
            Dictionary of helper types needed
        """
        return {
            'listnode': 'ListNode' in code and 'class ListNode' in code,
            'treenode': 'TreeNode' in code and 'class TreeNode' in code,
        }
    
    def _extract_parameter_info(self, code: str) -> List[Tuple[str, str]]:
        """
        Extract parameter names and types from method signature.
        
        Returns:
            List of (param_name, param_type) tuples
        """
        # Find the Solution class method specifically
        lines = code.split('\n')
        in_solution = False
        
        for line in lines:
            # Enter Solution class
            if 'class Solution' in line:
                in_solution = True
                continue
            
            # Exit Solution class when we hit another class
            if in_solution and line.strip().startswith('class ') and 'Solution' not in line:
                in_solution = False
                continue
            
            # Found a method in Solution class (skip __init__ and other dunder methods)
            if in_solution and 'def ' in line and not '__' in line:
                # Extract parameters between (self, ...) and ):
                match = re.search(r'def\s+\w+\s*\(\s*self\s*(?:,\s*([^)]+))?\)', line)
                
                if not match or not match.group(1):
                    # No parameters besides self
                    return []
                
                params_str = match.group(1)
                params = []
                
                # Split by comma, but respect brackets
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
                        # End of parameter
                        if current_param.strip():
                            # Remove default values (e.g., "val=0" -> "val")
                            param_clean = current_param.split('=')[0].strip()
                            
                            if ':' in param_clean:
                                name, type_hint = param_clean.split(':', 1)
                                params.append((name.strip(), type_hint.strip()))
                            else:
                                params.append((param_clean, 'Any'))
                        current_param = ""
                    else:
                        current_param += char
                
                return params
        
        return []
    
    def _get_return_type(self, code: str) -> str:
        """Extract return type from method signature."""
        match = re.search(r'->\s*([^:]+):', code)
        if match:
            return match.group(1).strip()
        return 'Any'
    
    def _extract_test_examples(self, description: str) -> List[Tuple[str, str, str]]:
        """
        Extract test examples from problem description.
        
        Returns:
            List of (input_text, output_text, explanation) tuples
        """
        from html import unescape
        
        # First, unescape HTML entities BEFORE removing tags
        description = unescape(description)
        
        # Then remove HTML tags
        text = re.sub(r'<[^>]+>', '\n', description)
        
        examples = []
        example_pattern = r'Example\s+\d+:(.*?)(?=Example\s+\d+:|Constraints:|$)'
        
        for match in re.finditer(example_pattern, text, re.DOTALL | re.IGNORECASE):
            example_text = match.group(1).strip()
            
            input_match = re.search(r'Input:\s*([^\n]+(?:\n(?!Output:)[^\n]+)*)', example_text)
            input_text = input_match.group(1).strip() if input_match else ""
            
            output_match = re.search(r'Output:\s*([^\n]+(?:\n(?!Explanation:)[^\n]+)*)', example_text)
            output_text = output_match.group(1).strip() if output_match else ""
            
            explanation_match = re.search(r'Explanation:\s*([^\n]+.*?)$', example_text, re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else ""
            
            if input_text:
                examples.append((input_text, output_text, explanation))
        
        return examples
    
    def _parse_input_line(self, input_text: str) -> List[Tuple[str, str]]:
        """
        Parse input line to extract parameter names and values.
        
        Handles strings with commas correctly.
        """
        params = []
        
        # More sophisticated parsing - track if we're inside quotes
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
                # End of parameter
                if current_part.strip():
                    match = re.search(r'(\w+)\s*=\s*(.+)', current_part.strip())
                    if match:
                        name = match.group(1).strip()
                        value = match.group(2).strip()
                        
                        # Replace null with None
                        value = value.replace('null', 'None')
                        
                        # If value has double quotes, convert to single quotes
                        if value.startswith('"') and value.endswith('"'):
                            inner_value = value[1:-1]
                            # Escape any single quotes in the string
                            inner_value = inner_value.replace("'", "\\'")
                            value = f"'{inner_value}'"
                        
                        params.append((name, value))
                current_part = ""
            else:
                current_part += char
        
        return params
    
    def _parse_output_line(self, output_text: str) -> str:
        """
        Parse output line to extract just the return value.
        
        Examples:
            "[0,1]" -> "[0,1]"
            "2, nums = [2,2,_,_]" -> "2"
            "[7,0,8]" -> "[7,0,8]"
            "true" -> "true"
        
        Returns:
            Just the return value (handles lists/arrays properly)
        """
        output_text = output_text.strip()
        
        # If output starts with '[', it's a list - find the matching ']'
        if output_text.startswith('['):
            bracket_count = 0
            for i, char in enumerate(output_text):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return output_text[:i+1]
            return output_text
        
        # If output starts with '{', it's a dict/set - find matching '}'
        if output_text.startswith('{'):
            bracket_count = 0
            for i, char in enumerate(output_text):
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return output_text[:i+1]
            return output_text
        
        # Otherwise, take everything before the first comma (if exists)
        if ',' in output_text:
            return output_text.split(',')[0].strip()
        
        return output_text
    
    def _needs_conversion(self, param_type: str) -> Optional[str]:
        """
        Check if parameter type needs conversion.
        
        Returns:
            Conversion function name or None
        """
        if 'ListNode' in param_type:
            return 'list_to_listnode'
        elif 'TreeNode' in param_type:
            return 'list_to_treenode'
        return None
    
    def _format_test_cases(self, problem: Problem, code: str) -> str:
        """Format test cases into runnable code with smart helper detection."""
        method_name = self._extract_method_name(code)
        helpers_needed = self._detect_helpers_needed(code)
        param_info = self._extract_parameter_info(code)
        return_type = self._get_return_type(code)
        

        logger = get_logger()
        logger.debug(f"Method name: {method_name}")
        logger.debug(f"Param info: {param_info}")
        logger.debug(f"Return type: {return_type}")

        # Extract examples from description
        examples = self._extract_test_examples(problem.description)
        
        if not examples:
            return self._format_basic_test_cases(problem.test_cases, code)
        
        test_code = []
        
        # Add helper functions if needed
        if helpers_needed.get('listnode'):
            test_code.extend(self.LISTNODE_HELPERS.split('\n'))
        
        if helpers_needed.get('treenode'):
            test_code.extend(self.TREENODE_HELPERS.split('\n'))
        
        test_code.append('    # Test cases from LeetCode')
        test_code.append('')
        
        for test_num, (input_text, output_text, explanation) in enumerate(examples, 1):
            # Parse inputs with names
            input_params = self._parse_input_line(input_text)
            
            if not input_params:
                continue
            
            # Parse expected output
            expected_return = self._parse_output_line(output_text)
            
            # Convert boolean strings
            if expected_return.lower() in ('true', 'false'):
                expected_return = expected_return.capitalize()
            
            # Build function call with conversions
            call_params = []
            
            for param_name, param_value in input_params:
                # Find matching parameter type
                param_type = None
                for info_name, info_type in param_info:
                    if info_name == param_name:
                        param_type = info_type
                        break
                
                # Check if conversion needed
                converter = self._needs_conversion(param_type) if param_type else None
                
                if converter:
                    call_params.append(f'{converter}({param_value})')
                else:
                    call_params.append(param_value)
            
            # Build the call
            params_str = ', '.join(call_params)
            call = f'solution.{method_name}({params_str})'
            
            # Check if return type needs conversion
            return_converter = None
            if 'ListNode' in return_type:
                return_converter = 'listnode_to_list'
            elif 'TreeNode' in return_type:
                return_converter = 'treenode_to_list'
            
            if return_converter:
                call = f'{return_converter}({call})'
            
            expected_return = expected_return.replace('null', 'None')

            # Generate assertion
            test_code.append(f'    assert {expected_return} == {call}')
            test_code.append('')
        
        test_code.append('    print("All tests passed!")')
        
        return '\n'.join(test_code)
    
    def _format_basic_test_cases(self, test_cases: str, code: str) -> str:
        """Fallback: format basic test cases when examples can't be parsed."""
        if not test_cases:
            return '    # Add your test cases here\n    pass'
        
        method_name = self._extract_method_name(code)
        lines = test_cases.strip().split('\n')
        param_count = self._count_method_params(code)
        
        test_code = []
        test_code.append('    # Test cases from LeetCode')
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
                
                test_code.append(f'    result{test_num} = {call}')
                test_code.append(f'    print(f"Test {test_num}: {{result{test_num}}}")')
                test_code.append('')
        
        return '\n'.join(test_code)
    
    def _extract_method_name(self, code: str) -> str:
        """Extract the method name from the Solution class."""
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
                        return method
        
        match = re.search(r'def\s+(?!__)(\w+)\s*\(', code)
        if match:
            return match.group(1)
        
        return 'solve'
    
    def _count_method_params(self, code: str) -> int:
        """Count the number of parameters in the method (excluding self)."""
        match = re.search(r'def\s+\w+\s*\(([^)]+)\)', code)
        if match:
            params = match.group(1).split(',')
            return len([p for p in params if 'self' not in p.strip()])
        return 0
    
    def _uncomment_class_definitions(self, code: str) -> str:
        """Uncomment ListNode, TreeNode, etc."""
        lines = code.split('\n')
        result = []
        in_comment_block = False
        comment_block = []
        base_indent = 0
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('# class ') and ':' in stripped:
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
        imports = set()
        
        if 'List[' in code:
            imports.add('List')
        if 'Optional[' in code:
            imports.add('Optional')
        if 'Dict[' in code or 'Dictionary[' in code:
            imports.add('Dict')
        if 'Set[' in code:
            imports.add('Set')
        if 'Tuple[' in code:
            imports.add('Tuple')
        if 'Union[' in code:
            imports.add('Union')
        if 'Deque[' in code or 'deque' in code:
            imports.add('Deque')
        
        if imports:
            typing_imports = sorted(imports)
            return f"from typing import {', '.join(typing_imports)}"
        
        return ""
    
    def _ensure_pass_in_methods(self, code: str) -> str:
        """Add pass to empty methods."""
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
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_stripped = next_line.strip()
                    
                    if next_stripped.startswith('#'):
                        i += 1
                        continue
                    
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else current_indent
                    
                    if next_indent <= current_indent or not next_line.strip():
                        result.append(' ' * (current_indent + 4) + 'pass')
                else:
                    current_indent = len(line) - len(line.lstrip())
                    result.append(' ' * (current_indent + 4) + 'pass')
            
            i += 1
        
        return '\n'.join(result)