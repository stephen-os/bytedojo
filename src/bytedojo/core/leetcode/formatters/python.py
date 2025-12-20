import re
from textwrap import dedent
from typing import Tuple, List, Optional
from bytedojo.core.leetcode.models import Problem
from bytedojo.core.leetcode.formatters.base import BaseFormatter
from bytedojo.core.logger import get_logger


class PythonFormatter(BaseFormatter):
    """Formats LeetCode problems as Python files."""
    
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
    
    def _extract_test_examples(self, description: str) -> List[Tuple[str, str, str]]:
        """
        Extract test examples from problem description.
        
        Returns:
            List of (input_text, output_text, explanation) tuples
        """
        from html import unescape
        
        # Remove HTML tags but preserve structure
        text = re.sub(r'<[^>]+>', '\n', description)
        text = unescape(text)
        
        examples = []
        
        # Find all "Example N:" blocks
        example_pattern = r'Example\s+\d+:(.*?)(?=Example\s+\d+:|Constraints:|$)'
        
        for match in re.finditer(example_pattern, text, re.DOTALL | re.IGNORECASE):
            example_text = match.group(1).strip()
            
            # Extract Input
            input_match = re.search(r'Input:\s*([^\n]+(?:\n(?!Output:)[^\n]+)*)', example_text)
            input_text = input_match.group(1).strip() if input_match else ""
            
            # Extract Output
            output_match = re.search(r'Output:\s*([^\n]+(?:\n(?!Explanation:)[^\n]+)*)', example_text)
            output_text = output_match.group(1).strip() if output_match else ""
            
            # Extract Explanation
            explanation_match = re.search(r'Explanation:\s*([^\n]+.*?)$', example_text, re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else ""
            
            if input_text:
                examples.append((input_text, output_text, explanation))
        
        return examples
    
    def _parse_input_line(self, input_text: str) -> List[str]:
        """
        Parse input line to extract parameter values.
        
        Examples:
            "nums = [3,2,2,3], val = 3" -> ["[3,2,2,3]", "3"]
            "n = 5" -> ["5"]
        """
        params = []
        
        # Split by comma but not within brackets
        parts = re.split(r',\s*(?![^\[\]]*\])', input_text)
        
        for part in parts:
            # Extract value after = sign
            match = re.search(r'=\s*(.+)', part.strip())
            if match:
                value = match.group(1).strip()
                params.append(value)
        
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
                        # Found the closing bracket
                        return output_text[:i+1]
            # If we get here, return everything (malformed but try anyway)
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

    def _format_test_cases(self, problem: Problem, code: str) -> str:
        """Format test cases into runnable code."""
        method_name = self._extract_method_name(code)
        
        # Extract examples from description
        examples = self._extract_test_examples(problem.description)
        
        if not examples:
            return self._format_basic_test_cases(problem.test_cases, code)
        
        test_code = []
        test_code.append('    # Test cases from LeetCode')
        test_code.append('')
        
        for test_num, (input_text, output_text, explanation) in enumerate(examples, 1):
            # Parse inputs
            params = self._parse_input_line(input_text)
            
            if not params:
                continue
            
            # Parse output - just get the return value
            expected_return = self._parse_output_line(output_text)
            
            # Generate function call
            params_str = ', '.join(params)
            call = f'solution.{method_name}({params_str})'
            
            # Convert boolean strings
            if expected_return.lower() in ('true', 'false'):
                expected_return = expected_return.capitalize()
            
            # Simple assertion
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
        
        # Group by parameter count
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
    
    def _extract_return_type(self, code: str) -> Optional[str]:
        """Extract return type from method signature."""
        match = re.search(r'->\s*([^:]+):', code)
        if match:
            return match.group(1).strip()
        return None
    
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