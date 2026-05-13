"""
Java universal runner package.

BytedojoRunner.java.template is a single-file Java template with a
{{BYTEDOJO_SOLUTION}} marker. TestService substitutes the user's class
blocks (Solution + their TreeNode/ListNode if present) into the marker,
writes the assembled BytedojoRunner.java into the per-problem build dir
alongside cases.json, and invokes javac + java.

The runner uses reflection for TreeNode/ListNode operations so it
compiles cleanly even when the user's solution doesn't declare those
classes (primitive-only problems never resolve them).
"""

from pathlib import Path

#: Directory holding the template. TestService loads RUNTIME_DIR /
#: "BytedojoRunner.java.template" and renders it per test invocation.
RUNTIME_DIR = Path(__file__).resolve().parent

#: Filename of the template inside RUNTIME_DIR.
TEMPLATE_NAME = "BytedojoRunner.java.template"

#: Marker the template uses for user-class substitution.
SOLUTION_MARKER = "{{BYTEDOJO_SOLUTION}}"
