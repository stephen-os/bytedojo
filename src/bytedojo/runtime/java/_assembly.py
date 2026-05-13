"""
Java source assembly: merge a user's solution.java with the runner template.

TestService loads `BytedojoRunner.java.template`, calls `assemble(...)`
with the user's solution source, and writes the result to the build
dir as `BytedojoRunner.java`. Compilation produces all the necessary
.class files in one shot.

Substitution does three things:
  1. Extract the user's import statements; merge into the template's
     import block (deduped).
  2. Extract their class blocks (Solution + optional TreeNode /
     ListNode), skip their Main class (it would conflict with the
     runner's `main`).
  3. Substitute the extracted class blocks for the {{BYTEDOJO_SOLUTION}}
     marker at the end of the template.
"""

import re
from typing import List, Optional

#: Marker the template uses for user-class substitution.
SOLUTION_MARKER = "{{BYTEDOJO_SOLUTION}}"

#: Class names we want to lift from the user's source, in this order
#: (Solution last so its imports / order match the template's flow).
_USER_CLASS_NAMES = ("TreeNode", "ListNode", "Solution")

#: Class blocks we DROP from the user's source — their `main()` would
#: collide with the runner's entry point.
_DROP_CLASS_NAMES = ("Main",)


class AssemblyError(Exception):
    """Raised when the user's solution.java can't be merged into the template."""


def assemble(template: str, user_source: str) -> str:
    """
    Render the final BytedojoRunner.java by splicing user blocks into template.

    Raises AssemblyError if the template is missing the marker or the user's
    source has no parseable Solution class.
    """
    if SOLUTION_MARKER not in template:
        raise AssemblyError(
            f"Template is missing the {SOLUTION_MARKER} marker."
        )

    blocks: List[str] = []
    for name in _USER_CLASS_NAMES:
        block = extract_class(user_source, name)
        if block is not None:
            blocks.append(block)

    if not any("class Solution" in b for b in blocks):
        raise AssemblyError(
            "Could not locate `class Solution` in user solution.java."
        )

    merged = template

    # Merge user imports into the template's existing import block (deduped).
    user_imports = extract_imports(user_source)
    if user_imports:
        merged = _merge_imports(merged, user_imports)

    # Substitute the class blocks for the marker.
    substitution = "\n\n".join(blocks) + "\n"
    return merged.replace(SOLUTION_MARKER, substitution, 1)


def extract_imports(source: str) -> List[str]:
    """All `import ...;` lines from a Java source, in order, deduped."""
    seen = set()
    out: List[str] = []
    for m in re.finditer(r"^\s*(import\s+[\w.*]+\s*;)", source, re.MULTILINE):
        stmt = m.group(1).strip()
        if stmt not in seen:
            seen.add(stmt)
            out.append(stmt)
    return out


def extract_class(source: str, class_name: str) -> Optional[str]:
    """
    Return the full text of `class NAME { ... }` (including modifiers) or None.

    Uses brace matching from the opening `{` to the matching close. Modifiers
    like `public`, `final`, `abstract` are preserved.
    """
    pattern = rf"((?:public\s+|final\s+|abstract\s+|static\s+)*class\s+{class_name}\b[^{{]*\{{)"
    m = re.search(pattern, source)
    if not m:
        return None
    return _slice_to_brace_match(source, start=m.start(), open_brace_pos=m.end() - 1)


def _slice_to_brace_match(source: str, *, start: int, open_brace_pos: int) -> str:
    """Return source[start:end] where end is just past the matching `}`."""
    depth = 1
    pos = open_brace_pos + 1
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


def _merge_imports(template: str, user_imports: List[str]) -> str:
    """Append new user imports after the template's last import line, deduped."""
    lines = template.split("\n")
    existing = {ln.strip() for ln in lines if ln.lstrip().startswith("import ")}
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.lstrip().startswith("import "):
            last_import_idx = i

    to_insert = [imp for imp in user_imports if imp not in existing]
    if not to_insert:
        return template

    if last_import_idx >= 0:
        lines[last_import_idx + 1:last_import_idx + 1] = to_insert
    else:
        lines = to_insert + lines

    return "\n".join(lines)
