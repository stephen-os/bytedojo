"""
C++ test runner codegen.

Generates a single .cpp file containing:
  - #include directives (merged: user's + handler-required)
  - any user `using` declarations (typically `using namespace std;`)
  - the user's `class Solution { ... };` block
  - `int main()` that runs every test case and prints a JSON array of
    results to stdout

The user's example `int main()` from solution.cpp is NOT embedded — only
their `class Solution` block. We avoid two `int main()` in the same
translation unit that way.

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

class CppIntHandler(TypeHandler):
    canonical = CanonicalType.INT

    def declaration(self, var_name: str) -> str:
        return f"int {var_name}"

    def literal(self, value: Any) -> str:
        return str(int(value))

    def equals(self, lhs: str, rhs: str) -> str:
        return f"({lhs} == {rhs})"

    def to_string(self, expr: str) -> str:
        return f"std::to_string({expr})"


class CppIntArrayHandler(TypeHandler):
    canonical = CanonicalType.INT_ARRAY

    def declaration(self, var_name: str) -> str:
        # std::vector<int> works regardless of whether the user's method
        # signature takes `vector<int>&` or `vector<int>` — C++ binds
        # reference-vs-copy at the call site automatically.
        return f"std::vector<int> {var_name}"

    def literal(self, value: Any) -> str:
        if value is None:
            return "std::vector<int>{}"
        items = ", ".join(str(int(v)) for v in value)
        return f"std::vector<int>{{{items}}}"

    def equals(self, lhs: str, rhs: str) -> str:
        return f"({lhs} == {rhs})"

    def to_string(self, expr: str) -> str:
        return f"_bytedojo_vec_to_string({expr})"

    @property
    def imports(self) -> List[str]:
        return ["#include <vector>", "#include <string>"]

    @property
    def helpers(self) -> str:
        return _VECTOR_INT_TO_STRING_HELPER


CPP_HANDLERS = {
    CanonicalType.INT: CppIntHandler(),
    CanonicalType.INT_ARRAY: CppIntArrayHandler(),
}


_VECTOR_INT_TO_STRING_HELPER = '''
static std::string _bytedojo_vec_to_string(const std::vector<int>& v) {
    std::string out = "[";
    for (size_t i = 0; i < v.size(); ++i) {
        if (i > 0) out += ", ";
        out += std::to_string(v[i]);
    }
    out += "]";
    return out;
}
'''


# ----------------------------------------------------------------------------
# Runner generator
# ----------------------------------------------------------------------------

def generate_runner(problem: Problem) -> str:
    """Build the test runner .cpp source for `problem` using the starter snippet."""
    if problem.types is None:
        raise CodegenError("Problem has no canonical types — run migrate_problem_types.py")

    starter = problem.get_snippet(CodeLanguage.CPP) or ""
    method_name = parse_method_name(starter, "cpp")
    if not method_name:
        raise CodegenError("Could not parse method name from C++ starter snippet")

    return generate_runner_for_source(problem, method_name, starter)


def generate_runner_for_source(
    problem: Problem,
    method_name: str,
    cpp_source: str,
) -> str:
    """Build using `cpp_source` as the user code to embed."""
    types = problem.types
    if types is None:
        raise CodegenError("Problem has no canonical types")

    in_handlers = [
        (cp.name, resolve_handler(CPP_HANDLERS, cp.type, language="cpp"))
        for cp in types.input_params
    ]
    out_handler = resolve_handler(CPP_HANDLERS, types.output_type, language="cpp")

    solution_block = _extract.extract_cpp_class(cpp_source, "Solution")
    user_includes = _extract.extract_cpp_includes(cpp_source)
    user_usings = _extract.extract_cpp_using_declarations(cpp_source)

    # Handler-required includes (deduplicate with user's).
    handler_includes = set()
    for _, h in in_handlers:
        handler_includes.update(h.imports)
    handler_includes.update(out_handler.imports)
    runner_includes = sorted({"#include <iostream>", "#include <string>"} | handler_includes)

    seen_includes = {inc.replace(" ", "") for inc in user_includes}
    merged_includes = list(user_includes)
    for inc in runner_includes:
        if inc.replace(" ", "") not in seen_includes:
            merged_includes.append(inc)

    # Helpers from all handlers in play (dedupe by exact string content).
    helpers_set = set()
    for _, h in in_handlers:
        if h.helpers:
            helpers_set.add(h.helpers)
    if out_handler.helpers:
        helpers_set.add(out_handler.helpers)
    helpers_section = "\n".join(sorted(helpers_set))

    test_input = _build_test_input(problem, method_name)
    case_blocks = _render_case_blocks(test_input, in_handlers, out_handler, method_name)

    return _render_file(
        includes=merged_includes,
        usings=user_usings,
        helpers=helpers_section,
        solution_block=solution_block,
        case_blocks=case_blocks,
    )


# ----------------------------------------------------------------------------
# Internal pieces
# ----------------------------------------------------------------------------

def _build_test_input(problem: Problem, method_name: str) -> dict:
    from bytedojo.core.harness import prepare_test_input
    return prepare_test_input(method_name, problem.test_cases, "cpp")


def _render_case_blocks(
    test_input: dict,
    in_handlers: list,
    out_handler: TypeHandler,
    method_name: str,
) -> List[str]:
    blocks: List[str] = []
    for case in test_input["cases"]:
        if not case_fits_int32(case, in_handlers, out_handler):
            continue
        case_num = len(blocks) + 1
        lines = ["    {"]
        arg_names = []
        for name, handler in in_handlers:
            value = case["args"].get(name)
            literal = handler.literal(value)
            lines.append(f"        {handler.declaration(name)} = {literal};")
            arg_names.append(name)

        expected_literal = out_handler.literal(case.get("expected"))
        lines.append(f"        {out_handler.declaration('_expected')} = {expected_literal};")

        call_args = ", ".join(arg_names)
        lines.append(f"        std::string _expectedStr = {out_handler.to_string('_expected')};")
        lines.append(f"        bool _passed = false;")
        lines.append(f"        std::string _actualStr = \"\";")
        lines.append(f"        std::string _error = \"\";")
        lines.append(f"        try {{")
        lines.append(f"            {out_handler.declaration('_result')} = _sol.{method_name}({call_args});")
        lines.append(f"            _passed = {out_handler.equals('_result', '_expected')};")
        lines.append(f"            _actualStr = {out_handler.to_string('_result')};")
        lines.append(f"        }} catch (const std::exception& _e) {{")
        lines.append(f"            _error = _e.what();")
        lines.append(f"        }} catch (...) {{")
        lines.append(f"            _error = \"unknown exception\";")
        lines.append(f"        }}")
        lines.append(f"        _results.push_back(_bytedojo_render_case({case_num}, _passed, _expectedStr, _actualStr, _error));")
        lines.append("    }")
        blocks.append("\n".join(lines))
    return blocks


def _render_file(
    *,
    includes: List[str],
    usings: List[str],
    helpers: str,
    solution_block: str,
    case_blocks: List[str],
) -> str:
    includes_section = "\n".join(includes)
    usings_section = "\n".join(usings)
    cases_section = "\n".join(case_blocks)

    return f'''// Generated by ByteDojo - do not edit by hand. Re-fetch the problem to regenerate.
{includes_section}
{usings_section}

{helpers}

static std::string _bytedojo_escape(const std::string& s) {{
    std::string out;
    out.reserve(s.size());
    for (char c : s) {{
        switch (c) {{
            case '\\\\': out += "\\\\\\\\"; break;
            case '"':  out += "\\\\\\""; break;
            case '\\n': out += "\\\\n"; break;
            case '\\r': out += "\\\\r"; break;
            case '\\t': out += "\\\\t"; break;
            default:   out += c;
        }}
    }}
    return out;
}}

static std::string _bytedojo_render_case(int caseNum, bool passed,
                                         const std::string& expected,
                                         const std::string& actual,
                                         const std::string& error) {{
    std::string b = "{{";
    b += "\\"case\\":" + std::to_string(caseNum);
    b += ",\\"passed\\":" + std::string(passed ? "true" : "false");
    b += ",\\"expected\\":\\"" + _bytedojo_escape(expected) + "\\"";
    b += ",\\"actual\\":\\""   + _bytedojo_escape(actual)   + "\\"";
    if (!error.empty()) {{
        b += ",\\"error\\":\\"" + _bytedojo_escape(error) + "\\"";
    }} else {{
        b += ",\\"error\\":null";
    }}
    b += "}}";
    return b;
}}

{solution_block}

int main() {{
    Solution _sol;
    std::vector<std::string> _results;

{cases_section}

    std::string _out = "[";
    for (size_t i = 0; i < _results.size(); ++i) {{
        if (i > 0) _out += ",";
        _out += _results[i];
    }}
    _out += "]";
    std::cout << _out << std::endl;
    return 0;
}}
'''
