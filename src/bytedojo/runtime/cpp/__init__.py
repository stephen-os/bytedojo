"""
C++ universal runner package.

bytedojo_runner.cpp.template is a single-file C++17 template with two
substitution markers. TestService:

  - splices the user's class blocks (Solution + their TreeNode/ListNode
    if present, dropping the fetcher's main()) into {{BYTEDOJO_SOLUTION}};
  - emits a per-problem run_case() body from the bundle's signature
    into {{BYTEDOJO_RUN_CASE}};
  - writes the assembled bytedojo_runner.cpp into the build dir
    alongside cases.json, then compiles via the existing C++ toolchain
    (g++ / clang++ / MSVC) and runs the resulting binary.

Per-problem run_case codegen exists because C++ has no runtime
reflection: every call site has to be typed at compile time. The
template provides templated parse_value<T> / compare<T> / display<T>
helpers; run_case just stitches them together for this problem's
signature.
"""

from pathlib import Path

#: Directory holding the template.
RUNTIME_DIR = Path(__file__).resolve().parent

#: Filename of the template inside RUNTIME_DIR.
TEMPLATE_NAME = "bytedojo_runner.cpp.template"

#: Marker for substituting the user's class blocks.
SOLUTION_MARKER = "{{BYTEDOJO_SOLUTION}}"

#: Marker for substituting the per-problem run_case body.
RUN_CASE_MARKER = "{{BYTEDOJO_RUN_CASE}}"
