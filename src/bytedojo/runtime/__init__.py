"""
Universal language runners for ByteDojo.

Each language subpackage holds a runner + converter library that the
test pipeline copies into the build directory at test time. The files
are templates — they have zero bytedojo runtime dependencies so they
work as standalone scripts once dropped into a build dir alongside the
user's solution.
"""
