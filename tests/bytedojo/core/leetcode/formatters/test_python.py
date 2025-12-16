import re
from textwrap import dedent
from bytedojo.core.leetcode.models import Problem
from bytedojo.core.leetcode.formatters.base import BaseFormatter


class PythonFormatter(BaseFormatter):
    """Formats LeetCode problems as Python files."""
    
    def format(self, problem: Problem) -> str:
        """Generate complete Python file content."""
        code_template = self._get_python_code(problem)
        description = self._format_description(problem.description)
        test_cases = self._format_test_cases(problem.test_cases, code_template)
        
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
        
        # Process code (uncomment classes, add imports, etc.)
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
    
    def _format_test_cases(self, test_cases: str, code: str) -> str:
        """Format test cases into runnable code."""
        if not test_cases:
            return '    # Add your test cases here\n    pass'
        
        method_name = self._extract_method_name(code)
        lines = test_cases.strip().split('\n')
        test_code = []
        
        test_code.append('    # Test cases from LeetCode')
        test_code.append('')
        
        # Count parameters to determine grouping
        param_count = self._count_method_params(code)
        
        # Try to parse test cases intelligently
        test_groups = self._parse_test_groups(lines, param_count)
        
        if test_groups:
            for test_num, (inputs, expected) in enumerate(test_groups, 1):
                # Generate the function call
                if len(inputs) == 1:
                    call = f'solution.{method_name}({inputs[0]})'
                else:
                    params_str = ', '.join(inputs)
                    call = f'solution.{method_name}({params_str})'
                
                test_code.append(f'    result{test_num} = {call}')
                
                # Show expected vs actual
                if expected:
                    test_code.append(f'    expected{test_num} = {expected}')
                    test_code.append(f'    print(f"Test {test_num}: Expected {{expected{test_num}}}, Got {{result{test_num}}}")')
                else:
                    test_code.append(f'    print(f"Test {test_num}: {{result{test_num}}}")')
                
                test_code.append('')
        else:
            # Fallback to commented format
            test_code.append('    # Inputs:')
            for line in lines:
                test_code.append(f'    # {line}')
            test_code.append('')
            test_code.append(f'    # result = solution.{method_name}(...)')
            test_code.append('    # print(f"Result: {result}")')
            test_code.append('')
            test_code.append('    pass')
        
        return '\n'.join(test_code)


    def _parse_test_groups(self, lines: list, param_count: int) -> list:
        """Parse test case lines into groups of (inputs, expected_output)."""
        if param_count == 0:
            return []
        
        # Try pattern: param_count inputs + 1 expected output
        group_size = param_count + 1
        
        if len(lines) % group_size == 0:
            test_groups = []
            for i in range(0, len(lines), group_size):
                inputs = lines[i:i + param_count]
                expected = lines[i + param_count]
                test_groups.append((inputs, expected))
            return test_groups
        
        # Try pattern: just inputs (no expected outputs)
        if len(lines) % param_count == 0:
            test_groups = []
            for i in range(0, len(lines), param_count):
                inputs = lines[i:i + param_count]
                test_groups.append((inputs, None))
            return test_groups
        
        return []


    def _extract_method_name(self, code: str) -> str:
        """Extract the method name from the Solution class."""
        lines = code.split('\n')
        in_solution_class = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check if we're entering the Solution class
            if 'class Solution' in line:
                in_solution_class = True
                continue
            
            # Check if we've left the Solution class
            if in_solution_class and line and not line[0].isspace() and 'class' in line:
                in_solution_class = False
            
            # Look for method definitions in Solution class
            if in_solution_class:
                match = re.search(r'def\s+(\w+)\s*\(', line)
                if match:
                    method = match.group(1)
                    # Skip dunder methods
                    if not method.startswith('__'):
                        return method
        
        # Fallback: find any non-dunder method
        match = re.search(r'def\s+(?!__)(\w+)\s*\(', code)
        if match:
            return match.group(1)
        
        return 'solve'


    def _count_method_params(self, code: str) -> int:
        """Count the number of parameters in the method (excluding self)."""
        match = re.search(r'def\s+\w+\s*\(([^)]+)\)', code)
        if match:
            params = match.group(1).split(',')
            # Exclude 'self' parameter
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
            
            # Check if this is a commented class definition
            if stripped.startswith('# class ') and ':' in stripped:
                in_comment_block = True
                base_indent = len(line) - len(line.lstrip())
                uncommented = line[base_indent:].lstrip('#').lstrip()
                comment_block = [uncommented]
            elif in_comment_block and stripped.startswith('#'):
                # Continue collecting the commented class
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
                # End of comment block
                result.extend(comment_block)
                result.append('')
                in_comment_block = False
                comment_block = []
                result.append(line)
            else:
                result.append(line)
        
        # Handle case where comment block is at the end
        if comment_block:
            result.extend(comment_block)
            result.append('')
        
        return '\n'.join(result)


    def _extract_imports(self, code: str) -> str:
        """Extract required typing imports."""
        imports = set()
        
        # Check for common type hints that need imports
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
        
        # Generate import statement
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
            
            # Skip if this line is a comment
            stripped = line.strip()
            if stripped.startswith('#'):
                i += 1
                continue
            
            # Check if this is a method definition
            if 'def ' in line and line.strip().endswith(':'):
                # Check if next line is another def, class, or end of code
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_stripped = next_line.strip()
                    
                    # Skip if next line is a comment
                    if next_stripped.startswith('#'):
                        i += 1
                        continue
                    
                    # If next line is not indented more than current, method is empty
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else current_indent
                    
                    if next_indent <= current_indent or not next_line.strip():
                        # Empty method body, add pass
                        result.append(' ' * (current_indent + 4) + 'pass')
                else:
                    # Last line is a method def, add pass
                    current_indent = len(line) - len(line.lstrip())
                    result.append(' ' * (current_indent + 4) + 'pass')
            
            i += 1
        
        return '\n'.join(result)