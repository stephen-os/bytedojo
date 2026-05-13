"""
C++ source assembly: render bytedojo_runner.cpp from template + bundle + user.

TestService calls `assemble(template, user_source, bundle)`. We:

  1. Extract `class Solution {...};` (plus optional `struct TreeNode`,
     `struct ListNode`) from the user's solution.cpp, dropping any
     top-level `int main()` (would conflict with the runner's main).
  2. Pull #include directives + `using` declarations out of the user
     source and merge them into the template's preamble.
  3. Generate a `run_case` function body from the bundle's signature —
     this is the per-problem piece that knows how to type the args and
     dispatch to the user's method.
  4. Substitute {{BYTEDOJO_SOLUTION}} and {{BYTEDOJO_RUN_CASE}} in the
     template.

Per-problem run_case generation exists because C++ has no runtime
reflection — every call site must be typed at compile time.
"""

from __future__ import annotations

import re
from typing import List, Optional

#: Markers the template uses for substitution.
SOLUTION_MARKER = "{{BYTEDOJO_SOLUTION}}"
RUN_CASE_MARKER = "{{BYTEDOJO_RUN_CASE}}"

#: Class declarations we lift from user source, in this order.
_USER_CLASS_NAMES = ("TreeNode", "ListNode", "Solution")

#: Canonical type → native C++ type. The native type drives both the
#: parse_value<T> specialization and the local-variable type in run_case.
CPP_TYPE = {
    "INT32":           "int",
    "INT64":           "long long",
    "FLOAT64":         "double",
    "BOOL":            "bool",
    "CHAR":            "char",
    "STRING":          "std::string",
    "VOID":            "void",
    "INT32_ARRAY":     "std::vector<int>",
    "INT64_ARRAY":     "std::vector<long long>",
    "FLOAT64_ARRAY":   "std::vector<double>",
    "BOOL_ARRAY":      "std::vector<bool>",
    "CHAR_ARRAY":      "std::vector<char>",
    "STRING_ARRAY":    "std::vector<std::string>",
    "INT32_MATRIX":    "std::vector<std::vector<int>>",
    "INT64_MATRIX":    "std::vector<std::vector<long long>>",
    "CHAR_MATRIX":     "std::vector<std::vector<char>>",
    "STRING_MATRIX":   "std::vector<std::vector<std::string>>",
    "TREE_NODE":       "TreeNode*",
    "LIST_NODE":       "ListNode*",
    "LIST_NODE_ARRAY": "std::vector<ListNode*>",
}


class AssemblyError(Exception):
    """Raised when the user's solution.cpp can't be merged into the template."""


# ----------------------------------------------------------------------------
# Top-level entry
# ----------------------------------------------------------------------------

def assemble(template: str, user_source: str, bundle: dict) -> str:
    """Produce the final bytedojo_runner.cpp source string."""
    if SOLUTION_MARKER not in template or RUN_CASE_MARKER not in template:
        raise AssemblyError(
            f"Template is missing {SOLUTION_MARKER} or {RUN_CASE_MARKER}."
        )

    # Extract user class blocks (drop their main() if any).
    blocks: List[str] = []
    for name in _USER_CLASS_NAMES:
        block = extract_class(user_source, name)
        if block is not None:
            blocks.append(block)

    if not any("class Solution" in b or "struct Solution" in b for b in blocks):
        raise AssemblyError(
            "Could not locate `class Solution` in user solution.cpp."
        )

    merged = template
    user_includes = extract_includes(user_source)
    user_usings = extract_usings(user_source)
    if user_includes:
        merged = _merge_lines_after_prefix(merged, user_includes, "#include")
    if user_usings:
        merged = _merge_lines_after_prefix(merged, user_usings, "using ")

    solution_block = "\n\n".join(blocks) + "\n"
    run_case_block = generate_run_case(bundle)

    merged = merged.replace(SOLUTION_MARKER, solution_block, 1)
    merged = merged.replace(RUN_CASE_MARKER, run_case_block, 1)
    return merged


# ----------------------------------------------------------------------------
# Source surgery
# ----------------------------------------------------------------------------

def extract_includes(source: str) -> List[str]:
    """All `#include ...` lines (unique, in source order)."""
    seen, out = set(), []
    for m in re.finditer(r'^\s*(#include\s+[<"][^>"]+[>"])', source, re.MULTILINE):
        stmt = m.group(1).strip()
        if stmt not in seen:
            seen.add(stmt)
            out.append(stmt)
    return out


def extract_usings(source: str) -> List[str]:
    """All top-level `using ...;` declarations (unique, in source order)."""
    seen, out = set(), []
    for m in re.finditer(r'^\s*(using\s+[^;\n]+;)', source, re.MULTILINE):
        stmt = m.group(1).strip()
        if stmt not in seen:
            seen.add(stmt)
            out.append(stmt)
    return out


def extract_class(source: str, name: str) -> Optional[str]:
    """
    Return `class NAME { ... };` (or `struct NAME { ... };`), brace-matched,
    including the trailing semicolon. Returns None if absent.
    """
    pattern = rf'((?:class|struct)\s+{name}\b[^{{]*\{{)'
    m = re.search(pattern, source)
    if not m:
        return None
    body = _slice_to_brace_match(source, m.start(), m.end() - 1)
    # Include the trailing semicolon if present (class/struct declarations
    # need it; without it the file won't compile).
    end = m.start() + len(body)
    if end < len(source) and source[end] == ";":
        body += ";"
    return body


def _slice_to_brace_match(source: str, start: int, open_pos: int) -> str:
    depth = 1
    pos = open_pos + 1
    n = len(source)
    while pos < n and depth > 0:
        c = source[pos]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        pos += 1
    if depth != 0:
        raise AssemblyError("Unbalanced braces in user source")
    return source[start:pos]


def _merge_lines_after_prefix(template: str, new_lines: List[str], prefix: str) -> str:
    """Append `new_lines` after the last preamble line starting with `prefix`.

    "Preamble" is everything before the first top-level `namespace ... {`
    declaration in the template. Restricting to the preamble keeps us out
    of trouble with `'{'` / `'}'` char-literals inside the template's JSON
    parser — naive brace-depth tracking miscounts those.
    """
    lines = template.split("\n")
    preamble_end = len(lines)
    for i, line in enumerate(lines):
        if re.match(r"^\s*namespace\s+\w+\s*\{", line):
            preamble_end = i
            break

    preamble = lines[:preamble_end]
    existing = {ln.strip() for ln in preamble if ln.lstrip().startswith(prefix)}

    last_idx = -1
    for i, line in enumerate(preamble):
        if line.lstrip().startswith(prefix):
            last_idx = i

    to_insert = [stmt for stmt in new_lines if stmt not in existing]
    if not to_insert:
        return template

    if last_idx >= 0:
        lines[last_idx + 1:last_idx + 1] = to_insert
    else:
        # No prefix lines in the preamble — drop the new lines right
        # before the first namespace block.
        lines[preamble_end:preamble_end] = to_insert
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Per-problem run_case codegen
# ----------------------------------------------------------------------------

#: Canonical types that need special TreeNode/ListNode handling in run_case.
_TREE_TYPES = {"TREE_NODE"}
_LIST_TYPES = {"LIST_NODE", "LIST_NODE_ARRAY"}


def _parse_call(canonical: str, json_expr: str) -> str:
    """C++ expression that converts `json_expr` into the native type."""
    if canonical == "TREE_NODE":
        return f"bj::build_tree<TreeNode>({json_expr})"
    if canonical == "LIST_NODE":
        return f"bj::build_list<ListNode>({json_expr})"
    if canonical == "LIST_NODE_ARRAY":
        return (
            "[&]{{ std::vector<ListNode*> _v; "
            f"for (const auto& _e : ({json_expr}).as_arr()) "
            "_v.push_back(bj::build_list<ListNode>(_e)); return _v; }}()"
        )
    cpp_t = CPP_TYPE[canonical]
    return f"bj::parse_value<{cpp_t}>({json_expr})"


def _compare_call(canonical: str, comparison: str) -> str:
    """C++ boolean expression that compares actual and expected."""
    if canonical == "VOID":
        return "true"
    if canonical == "TREE_NODE":
        return 'bj::compare_tree(actual, expected, "exact")'
    if canonical == "LIST_NODE":
        return 'bj::compare_list(actual, expected, "exact")'
    if canonical == "LIST_NODE_ARRAY":
        # Compare element-wise via serialize_list.
        return (
            "[&]{{ if (actual.size() != expected.size()) return false; "
            "for (size_t _i = 0; _i < actual.size(); ++_i) "
            "if (!bj::compare_list(actual[_i], expected[_i], \"exact\")) return false; "
            "return true; }}()"
        )
    return f'bj::compare_value(actual, expected, "{comparison}")'


def _display_call(canonical: str, value_expr: str) -> str:
    """C++ string expression rendering `value_expr` for the result envelope."""
    if canonical == "VOID":
        return '"None"'
    if canonical == "TREE_NODE":
        return f"bj::display_tree<TreeNode>({value_expr})"
    if canonical == "LIST_NODE":
        return f"bj::display_list<ListNode>({value_expr})"
    if canonical == "LIST_NODE_ARRAY":
        return (
            "[&]{{ std::ostringstream _s; _s << \"[\"; "
            f"for (size_t _i = 0; _i < ({value_expr}).size(); ++_i) "
            "{{ if (_i) _s << \", \"; "
            f"_s << bj::display_list<ListNode>(({value_expr})[_i]); }} "
            "_s << \"]\"; return _s.str(); }}()"
        )
    cpp_t = CPP_TYPE[canonical]
    return f"bj::display<{cpp_t}>({value_expr})"


def generate_run_case(bundle: dict) -> str:
    """Emit the per-problem run_case() function body as C++ source."""
    sig = bundle["signature"]
    method = bundle["method"]
    params = sig["params"]
    returns = sig["returns"]
    comparison = bundle.get("comparison", "exact")

    # Validate every type appears in CPP_TYPE so we get a Python-side
    # error rather than a C++ compile error if something's wrong.
    for p in params:
        if p["type"] not in CPP_TYPE:
            raise AssemblyError(f"No C++ mapping for canonical type {p['type']}")
    if returns not in CPP_TYPE:
        raise AssemblyError(f"No C++ mapping for canonical return type {returns}")

    param_names_init = "{" + ", ".join(f'"{p["name"]}"' for p in params) + "}"

    lines: List[str] = []
    lines.append(
        "static bj::CaseResult run_case(int64_t case_id, "
        "const bj::Json& input, const bj::Json& expected_raw) {"
    )
    lines.append("    bj::CaseResult r;")
    lines.append("    r.case_id = case_id;")
    lines.append(f"    static const std::vector<std::string> _names = {param_names_init};")
    lines.append("    r.input_str = bj::format_input(input, _names);")
    lines.append("    try {")

    # Materialize each param into a local of the appropriate native type.
    for p in params:
        cpp_t = CPP_TYPE[p["type"]]
        # Need a typed name to satisfy non-const reference parameters
        # (e.g. `vector<int>&` on LeetCode's `twoSum`). Using `auto`
        # would also work here but explicit types are easier to debug.
        lines.append(
            f'        {cpp_t} {p["name"]} = {_parse_call(p["type"], f"input.at(\"{p["name"]}\")")};'
        )

    # Build the call expression and capture actual when non-void.
    arg_list = ", ".join(p["name"] for p in params)
    if returns == "VOID":
        lines.append("        Solution _sol;")
        lines.append(f"        _sol.{method}({arg_list});")
        lines.append("        r.passed = true;")
        lines.append('        r.expected_str = "None";')
        lines.append('        r.actual_str = "None";')
    else:
        cpp_ret = CPP_TYPE[returns]
        # parse_value/build_tree/build_list for expected
        lines.append(
            f"        {cpp_ret} expected = {_parse_call(returns, 'expected_raw')};"
        )
        lines.append("        Solution _sol;")
        lines.append(f"        {cpp_ret} actual = _sol.{method}({arg_list});")
        lines.append(f"        r.passed = {_compare_call(returns, comparison)};")
        lines.append(f"        r.expected_str = {_display_call(returns, 'expected')};")
        lines.append(f"        r.actual_str = {_display_call(returns, 'actual')};")

    lines.append("    } catch (const std::exception& e) {")
    lines.append("        r.passed = false;")
    lines.append('        r.actual_str = "";')
    lines.append(
        '        r.error = std::string(typeid(e).name()) + ": " + e.what();'
    )
    if returns != "VOID":
        # Best-effort expected_str in the error path: render from raw JSON.
        lines.append("        try { r.expected_str = bj::format_json_value(expected_raw); }")
        lines.append("        catch (...) { r.expected_str = \"\"; }")
    else:
        lines.append('        r.expected_str = "None";')

    lines.append("    }")
    lines.append("    return r;")
    lines.append("}")
    return "\n".join(lines) + "\n"
