"""Python formatter for Codeforces problems."""

import re
import html
from typing import Optional
from bytedojo.core.codeforces.models import Problem


class PythonFormatter:
    """Format Codeforces problems as Python files."""

    def format(self, problem: Problem) -> str:
        """
        Format a problem into a Python file.

        Args:
            problem: Problem object to format

        Returns:
            Formatted Python file content
        """
        sections = []

        # Header docstring
        sections.append(self._format_header(problem))

        # Problem description as comments
        sections.append(self._format_description(problem))

        # Solution section
        sections.append(self._format_solution())

        # Test section with sample cases
        sections.append(self._format_tests(problem))

        return '\n'.join(sections)

    def _format_header(self, problem: Problem) -> str:
        """Format the header docstring."""
        rating_str = f"{problem.rating}" if problem.rating else "Unrated"

        return f'''"""
Codeforces Problem {problem.problem_id}: {problem.name}
Difficulty: {problem.difficulty} ({rating_str})
URL: {problem.url}
Time Limit: {problem.time_limit}
Memory Limit: {problem.memory_limit}
Tags: {', '.join(problem.tags) if problem.tags else 'None'}
"""
'''

    def _format_description(self, problem: Problem) -> str:
        """Format the problem description as comments."""
        lines = ["# " + "=" * 76]
        lines.append("# PROBLEM DESCRIPTION")
        lines.append("# " + "=" * 76)

        # Convert HTML description to text
        desc_text = self._html_to_text(problem.description)
        for line in desc_text.split('\n'):
            lines.append(f"# {line}" if line.strip() else "#")

        # Input specification
        if problem.input_spec:
            lines.append("#")
            lines.append("# INPUT:")
            input_text = self._html_to_text(problem.input_spec)
            for line in input_text.split('\n'):
                if line.strip() and not line.strip().startswith('Input'):
                    lines.append(f"# {line}")

        # Output specification
        if problem.output_spec:
            lines.append("#")
            lines.append("# OUTPUT:")
            output_text = self._html_to_text(problem.output_spec)
            for line in output_text.split('\n'):
                if line.strip() and not line.strip().startswith('Output'):
                    lines.append(f"# {line}")

        # Sample tests in description
        if problem.sample_tests:
            lines.append("#")
            lines.append("# EXAMPLES:")
            for i, test in enumerate(problem.sample_tests, 1):
                lines.append(f"#   Example {i}:")
                lines.append(f"#     Input:")
                for inp_line in test['input'].split('\n'):
                    lines.append(f"#       {inp_line}")
                lines.append(f"#     Output:")
                for out_line in test['output'].split('\n'):
                    lines.append(f"#       {out_line}")

        # Note
        if problem.note:
            lines.append("#")
            lines.append("# NOTE:")
            note_text = self._html_to_text(problem.note)
            for line in note_text.split('\n'):
                if line.strip() and not line.strip().startswith('Note'):
                    lines.append(f"# {line}")

        lines.append("")
        return '\n'.join(lines)

    def _format_solution(self) -> str:
        """Format the solution section."""
        return '''# ============================================================================
# SOLUTION
# ============================================================================

def solve():
    """
    Solve the problem.

    Read input from stdin and print output to stdout.
    """
    # Read input
    # n = int(input())
    # data = list(map(int, input().split()))

    # Your solution here
    pass


if __name__ == "__main__":
    solve()
'''

    def _format_tests(self, problem: Problem) -> str:
        """Format the test section."""
        lines = ["\n# " + "=" * 76]
        lines.append("# TESTS")
        lines.append("# " + "=" * 76)
        lines.append("")
        lines.append("import io")
        lines.append("import sys")
        lines.append("")
        lines.append("")
        lines.append("def run_tests():")
        lines.append('    """Run sample test cases."""')

        if not problem.sample_tests:
            lines.append("    print('No sample tests available.')")
            lines.append("    print('Add your own test cases here.')")
        else:
            lines.append("    test_cases = [")
            for i, test in enumerate(problem.sample_tests):
                # Escape the strings properly
                inp = test['input'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                out = test['output'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                lines.append(f'        ("{inp}", "{out}"),')
            lines.append("    ]")
            lines.append("")
            lines.append("    passed = 0")
            lines.append("    failed = 0")
            lines.append("")
            lines.append("    for i, (test_input, expected) in enumerate(test_cases, 1):")
            lines.append("        # Capture stdin/stdout")
            lines.append("        old_stdin = sys.stdin")
            lines.append("        old_stdout = sys.stdout")
            lines.append('        sys.stdin = io.StringIO(test_input.replace("\\\\n", "\\n"))')
            lines.append("        sys.stdout = io.StringIO()")
            lines.append("")
            lines.append("        try:")
            lines.append("            solve()")
            lines.append("            actual = sys.stdout.getvalue().strip()")
            lines.append('            expected_clean = expected.replace("\\\\n", "\\n").strip()')
            lines.append("")
            lines.append("            if actual == expected_clean:")
            lines.append('                print(f"Test {i}: PASSED", file=sys.stderr)')
            lines.append("                passed += 1")
            lines.append("            else:")
            lines.append('                print(f"Test {i}: FAILED", file=sys.stderr)')
            lines.append('                print(f"  Input: {test_input}", file=sys.stderr)')
            lines.append('                print(f"  Expected: {expected_clean!r}", file=sys.stderr)')
            lines.append('                print(f"  Actual: {actual!r}", file=sys.stderr)')
            lines.append("                failed += 1")
            lines.append("        except Exception as e:")
            lines.append('            print(f"Test {i}: ERROR - {e}", file=sys.stderr)')
            lines.append("            failed += 1")
            lines.append("        finally:")
            lines.append("            sys.stdin = old_stdin")
            lines.append("            sys.stdout = old_stdout")
            lines.append("")
            lines.append('    print(f"\\nResults: {passed} passed, {failed} failed")')

        lines.append("")
        lines.append("")
        lines.append('if __name__ == "__main__":')
        lines.append('    import sys')
        lines.append('    if len(sys.argv) > 1 and sys.argv[1] == "test":')
        lines.append('        run_tests()')
        lines.append('    else:')
        lines.append('        solve()')
        lines.append("")

        return '\n'.join(lines)

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text."""
        if not html_content:
            return ""

        # Remove script and style elements
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        # Replace common block elements with newlines
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</(p|div|li|tr)>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<(p|div|li|tr)[^>]*>', '', text, flags=re.IGNORECASE)

        # Handle lists
        text = re.sub(r'<ul[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</ul>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<ol[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</ol>', '', text, flags=re.IGNORECASE)

        # Remove all remaining tags
        text = re.sub(r'<[^>]+>', '', text)

        # Unescape HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        lines = []
        for line in text.split('\n'):
            line = ' '.join(line.split())  # Normalize whitespace
            if line:
                lines.append(line)

        return '\n'.join(lines)
