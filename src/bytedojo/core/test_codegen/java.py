"""
Java test runner codegen.

Generates a `BytedojoTestRunner.java` containing:
  - imports (merged: user's + handler-required)
  - the user's `class Solution` block (extracted from their solution.java)
  - `public class BytedojoTestRunner` with `main()` that runs every test
    case and prints a JSON array of results to stdout

The runner class is deliberately uniquely-named so it doesn't collide
with the user's `class Main` (which the formatter emits for local
debugging).

Handler coverage today: INT, INT_ARRAY. Add more handlers below as new
problem types appear.
"""

from typing import Any, List

from bytedojo.core.harness import parse_method_name
from bytedojo.core.models.canonical_type import CanonicalType
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.test_codegen import _extract
from bytedojo.core.test_codegen.base import (
    CodegenError,
    TypeHandler,
    case_fits_int32,
    resolve_handler,
)


# ----------------------------------------------------------------------------
# TypeHandlers
# ----------------------------------------------------------------------------

class JavaIntHandler(TypeHandler):
    canonical = CanonicalType.INT

    def declaration(self, var_name: str) -> str:
        return f"int {var_name}"

    def literal(self, value: Any) -> str:
        return str(int(value))

    def equals(self, lhs: str, rhs: str) -> str:
        return f"({lhs} == {rhs})"

    def to_string(self, expr: str) -> str:
        return f"String.valueOf({expr})"


class JavaIntArrayHandler(TypeHandler):
    canonical = CanonicalType.INT_ARRAY

    def declaration(self, var_name: str) -> str:
        return f"int[] {var_name}"

    def literal(self, value: Any) -> str:
        if value is None:
            return "null"
        items = ", ".join(str(int(v)) for v in value)
        return f"new int[]{{{items}}}"

    def equals(self, lhs: str, rhs: str) -> str:
        return f"java.util.Arrays.equals({lhs}, {rhs})"

    def to_string(self, expr: str) -> str:
        return f"java.util.Arrays.toString({expr})"

    @property
    def imports(self) -> List[str]:
        return ["java.util.Arrays"]


JAVA_HANDLERS = {
    CanonicalType.INT: JavaIntHandler(),
    CanonicalType.INT_ARRAY: JavaIntArrayHandler(),
}


# ----------------------------------------------------------------------------
# Runner generator
# ----------------------------------------------------------------------------

#: The fully-qualified name of the generated runner's entry class.
ENTRY_CLASS = "BytedojoTestRunner"


def generate_runner(problem: Problem) -> str:
    """
    Build the full BytedojoTestRunner.java source for `problem`.

    Reads the user's solution.java content via problem.get_snippet(JAVA)
    — but that's the *starter* snippet, not the user's edited file.
    For real code generation at test time, the caller should pass the
    user's actual solution content; until that's wired through, we use
    the starter snippet which still includes the Solution class shell.
    """
    if problem.types is None:
        raise CodegenError("Problem has no canonical types — run migrate_problem_types.py")

    starter = problem.get_snippet(CodeLanguage.JAVA) or ""
    method_name = parse_method_name(starter, "java")
    if not method_name:
        raise CodegenError("Could not parse method name from Java starter snippet")

    return generate_runner_for_source(problem, method_name, starter)


def generate_runner_for_source(
    problem: Problem,
    method_name: str,
    java_source: str,
) -> str:
    """
    Build the runner using `java_source` as the user code to embed.

    Splitting this from generate_runner() lets TestService pass the
    user's actual solution.java content, not the starter snippet.
    """
    types = problem.types
    if types is None:
        raise CodegenError("Problem has no canonical types")

    # Look up handlers up-front so we error fast if anything's missing.
    in_handlers = [
        (cp.name, resolve_handler(JAVA_HANDLERS, cp.type, language="java"))
        for cp in types.input_params
    ]
    out_handler = resolve_handler(JAVA_HANDLERS, types.output_type, language="java")

    # Extract the user's Solution class + their imports.
    solution_block = _extract.extract_java_class(java_source, "Solution")
    user_imports = _extract.extract_java_imports(java_source)

    # Imports needed by the runner itself + handlers.
    handler_imports = set()
    for _, h in in_handlers:
        handler_imports.update(h.imports)
    handler_imports.update(out_handler.imports)
    runner_imports = sorted(
        {"java.util.ArrayList", "java.util.List"} | handler_imports
    )
    # Avoid duplicates between user imports and our runner imports.
    user_imports_seen = {imp.replace(" ", "") for imp in user_imports}
    merged_imports = list(user_imports)
    for imp in runner_imports:
        stmt = f"import {imp};"
        if stmt.replace(" ", "") not in user_imports_seen:
            merged_imports.append(stmt)

    test_input = _build_test_input(problem, method_name)
    case_blocks = _render_case_blocks(test_input, in_handlers, out_handler, method_name)

    return _render_file(
        imports=merged_imports,
        solution_block=solution_block,
        case_blocks=case_blocks,
    )


# ----------------------------------------------------------------------------
# Internal pieces
# ----------------------------------------------------------------------------

def _build_test_input(problem: Problem, method_name: str) -> dict:
    """Reuse the existing harness parser to turn case strings into values."""
    from bytedojo.core.harness import prepare_test_input
    return prepare_test_input(method_name, problem.test_cases, "java")


def _render_case_blocks(
    test_input: dict,
    in_handlers: list,
    out_handler: TypeHandler,
    method_name: str,
) -> List[str]:
    blocks: List[str] = []
    for case in test_input["cases"]:
        # Skip cases whose values overflow int32 — these don't fit the
        # problem's declared int/int[] types and would fail compilation.
        if not case_fits_int32(case, in_handlers, out_handler):
            continue
        case_num = case["case"] if "case" in case else len(blocks) + 1
        # Per-case scoped block so variable names don't collide across cases.
        lines = ["        {"]
        # Declare and assign each input arg.
        arg_names = []
        for name, handler in in_handlers:
            value = case["args"].get(name)
            literal = handler.literal(value)
            lines.append(f"            {handler.declaration(name)} = {literal};")
            arg_names.append(name)

        expected_literal = out_handler.literal(case.get("expected"))
        lines.append(f"            {out_handler.declaration('_expected')} = {expected_literal};")

        # Call the user's method inside a try/catch — any exception becomes a
        # failed case with the message captured as the error.
        call_args = ", ".join(arg_names)
        lines.append(f"            String _expectedStr = {out_handler.to_string('_expected')};")
        lines.append(f"            boolean _passed = false;")
        lines.append(f"            String _actualStr = \"\";")
        lines.append(f"            String _error = null;")
        lines.append(f"            try {{")
        lines.append(f"                {out_handler.declaration('_result')} = _sol.{method_name}({call_args});")
        lines.append(f"                _passed = {out_handler.equals('_result', '_expected')};")
        lines.append(f"                _actualStr = {out_handler.to_string('_result')};")
        lines.append(f"            }} catch (Throwable _t) {{")
        lines.append(f"                _error = _t.getClass().getSimpleName() + \": \" + _t.getMessage();")
        lines.append(f"            }}")
        lines.append(f"            _results.add(_renderCase({len(blocks) + 1}, _passed, _expectedStr, _actualStr, _error));")
        lines.append("        }")
        blocks.append("\n".join(lines))
    return blocks


def _render_file(*, imports: List[str], solution_block: str, case_blocks: List[str]) -> str:
    imports_section = "\n".join(imports)

    cases_section = "\n".join(case_blocks)

    return f'''// Generated by ByteDojo — do not edit by hand. Re-fetch the problem to regenerate.
{imports_section}

{solution_block}

public class {ENTRY_CLASS} {{
    public static void main(String[] args) {{
        Solution _sol = new Solution();
        List<String> _results = new ArrayList<>();

{cases_section}

        StringBuilder _out = new StringBuilder("[");
        for (int _i = 0; _i < _results.size(); _i++) {{
            if (_i > 0) _out.append(",");
            _out.append(_results.get(_i));
        }}
        _out.append("]");
        System.out.println(_out.toString());
    }}

    private static String _renderCase(int caseNum, boolean passed, String expected, String actual, String error) {{
        StringBuilder b = new StringBuilder("{{");
        b.append("\\"case\\":").append(caseNum);
        b.append(",\\"passed\\":").append(passed);
        b.append(",\\"expected\\":\\"").append(_escape(expected)).append("\\"");
        b.append(",\\"actual\\":\\"").append(_escape(actual)).append("\\"");
        if (error != null) {{
            b.append(",\\"error\\":\\"").append(_escape(error)).append("\\"");
        }} else {{
            b.append(",\\"error\\":null");
        }}
        b.append("}}");
        return b.toString();
    }}

    private static String _escape(String s) {{
        if (s == null) return "";
        StringBuilder out = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {{
            char c = s.charAt(i);
            switch (c) {{
                case '\\\\': out.append("\\\\\\\\"); break;
                case '\\"':  out.append("\\\\\\""); break;
                case '\\n': out.append("\\\\n"); break;
                case '\\r': out.append("\\\\r"); break;
                case '\\t': out.append("\\\\t"); break;
                default:    out.append(c);
            }}
        }}
        return out.toString();
    }}
}}
'''
