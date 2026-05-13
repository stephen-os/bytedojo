"""
Java universal runner package.

BytedojoRunner.java.template is a standalone Java file — no substitution
at test time. TestService copies it into the per-problem build dir
alongside the user's solution.java and any sibling node-class files
(TreeNode.java / ListNode.java), then compiles all of them with
`javac` and launches `java BytedojoRunner`.

The runner uses reflection for Solution / TreeNode / ListNode access,
so primitive-only problems work even when those node classes aren't
present in the build dir.
"""

from pathlib import Path

#: Directory holding the template.
RUNTIME_DIR = Path(__file__).resolve().parent

#: Filename of the template inside RUNTIME_DIR. We keep the .template
#: suffix purely for cross-language consistency with the C++ side (which
#: still has substitution markers); the Java template is now a complete
#: standalone .java file.
TEMPLATE_NAME = "BytedojoRunner.java.template"
