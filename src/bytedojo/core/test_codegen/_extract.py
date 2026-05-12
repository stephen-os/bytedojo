"""
Source extraction utilities for codegen.

Pulls the Solution class (and any other class definitions besides the
user's example `Main` / `int main()`) out of the user's solution file so
the generated test runner can embed it. Single-file compilation keeps
the toolchain integration simple — no multi-file invocations, no
classpath gymnastics.

These extractors are deliberately minimal: regex + brace matching, no
real parser. They handle the LeetCode-style starter code shape we
generate via the formatters; if the user pastes in something exotic the
extraction may fail and we'd surface a clear CodegenError.
"""

import re
from typing import List


def extract_java_imports(source: str) -> List[str]:
    """All top-level `import ...;` statements (unique, in source order)."""
    seen = set()
    out = []
    for m in re.finditer(r'^\s*(import\s+[\w.*]+\s*;)', source, re.MULTILINE):
        stmt = m.group(1).strip()
        if stmt not in seen:
            seen.add(stmt)
            out.append(stmt)
    return out


def extract_java_class(source: str, class_name: str = "Solution") -> str:
    """
    Extract a Java class block (declaration + body), including modifiers.

    Returns the substring from `(public )? class Foo {` through the
    matching `}`. Raises ValueError if the class isn't found or the
    braces don't balance.
    """
    pattern = rf'((?:public\s+)?class\s+{class_name}\b[^{{]*\{{)'
    m = re.search(pattern, source)
    if not m:
        raise ValueError(f"No `class {class_name}` found in Java source")
    return _slice_until_brace_match(source, start=m.start(), open_brace_pos=m.end() - 1)


def extract_cpp_includes(source: str) -> List[str]:
    """All `#include ...` directives (unique, in source order)."""
    seen = set()
    out = []
    for m in re.finditer(r'^\s*(#include\s+[<"][^>"]+[>"])', source, re.MULTILINE):
        stmt = m.group(1).strip()
        if stmt not in seen:
            seen.add(stmt)
            out.append(stmt)
    return out


def extract_cpp_using_declarations(source: str) -> List[str]:
    """All top-level `using` declarations (e.g. `using namespace std;`)."""
    seen = set()
    out = []
    for m in re.finditer(r'^\s*(using\s+[^\n;]+;)', source, re.MULTILINE):
        stmt = m.group(1).strip()
        if stmt not in seen:
            seen.add(stmt)
            out.append(stmt)
    return out


def extract_cpp_class(source: str, class_name: str = "Solution") -> str:
    """
    Extract a C++ class block including the trailing `;`.

    E.g. ``class Solution { ... };`` start-to-finish.
    """
    pattern = rf'(class\s+{class_name}\b[^{{]*\{{)'
    m = re.search(pattern, source)
    if not m:
        raise ValueError(f"No `class {class_name}` found in C++ source")
    sliced = _slice_until_brace_match(source, start=m.start(), open_brace_pos=m.end() - 1)
    # Include the trailing semicolon if present
    tail = source[m.start() + len(sliced):m.start() + len(sliced) + 1]
    if tail == ";":
        return sliced + ";"
    return sliced


# ----------------------------------------------------------------------------
# Internals
# ----------------------------------------------------------------------------

def _slice_until_brace_match(source: str, *, start: int, open_brace_pos: int) -> str:
    """
    Return source[start:end] where end is the position just after the
    `}` that matches `source[open_brace_pos]` (which must be `{`).
    """
    if source[open_brace_pos] != "{":
        raise ValueError("open_brace_pos must point at a `{`")

    depth = 1
    pos = open_brace_pos + 1
    while pos < len(source) and depth > 0:
        c = source[pos]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        pos += 1
    if depth != 0:
        raise ValueError("Unbalanced braces while extracting class body")
    return source[start:pos]
