"""
C++ comment formatter
"""

from bytedojo.core.formatters.comments.base_comment_formatter import BaseCommentFormatter

class CppCommentFormatter(BaseCommentFormatter):
    def format_single_line(self, text: str) -> str:
        return "\n".join(f"// {line}" for line in text.splitlines())

    def format_multi_line(self, text: str) -> str:
        return f"/**\n{text}\n*/"
    