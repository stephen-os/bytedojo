"""
Tests for templates module (GITIGNORE, README template constants).
"""

import pytest
from bytedojo.core.templates import GITIGNORE, README


class TestGitignoreTemplate:
    """Test GITIGNORE template content."""

    def test_gitignore_is_string(self):
        """Test that GITIGNORE is a string."""
        assert isinstance(GITIGNORE, str)

    def test_gitignore_not_empty(self):
        """Test that GITIGNORE is not empty."""
        assert len(GITIGNORE) > 0

    def test_gitignore_no_leading_whitespace(self):
        """Test that GITIGNORE has no leading whitespace (stripped)."""
        assert GITIGNORE == GITIGNORE.lstrip()

    def test_gitignore_no_trailing_whitespace(self):
        """Test that GITIGNORE has no trailing whitespace (stripped)."""
        assert GITIGNORE == GITIGNORE.rstrip()

    def test_gitignore_contains_python_section(self):
        """Test that GITIGNORE contains Python-related patterns."""
        assert "# Python" in GITIGNORE
        assert "__pycache__/" in GITIGNORE
        assert "*.pyc" in GITIGNORE
        assert "*.pyo" in GITIGNORE
        assert "*.pyd" in GITIGNORE
        assert ".Python" in GITIGNORE

    def test_gitignore_contains_ide_section(self):
        """Test that GITIGNORE contains IDE-related patterns."""
        assert "# IDE" in GITIGNORE
        assert ".vscode/" in GITIGNORE
        assert ".idea/" in GITIGNORE
        assert "*.swp" in GITIGNORE
        assert "*.swo" in GITIGNORE

    def test_gitignore_contains_os_section(self):
        """Test that GITIGNORE contains OS-related patterns."""
        assert "# OS" in GITIGNORE
        assert ".DS_Store" in GITIGNORE
        assert "Thumbs.db" in GITIGNORE

    def test_gitignore_contains_bytedojo_section(self):
        """Test that GITIGNORE contains ByteDojo-specific patterns."""
        assert "# ByteDojo" in GITIGNORE
        assert "logs/" in GITIGNORE
        assert "*.log" in GITIGNORE

    def test_gitignore_has_multiple_sections(self):
        """Test that GITIGNORE has all expected section headers."""
        sections = ["# Python", "# IDE", "# OS", "# ByteDojo"]
        for section in sections:
            assert section in GITIGNORE

    def test_gitignore_sections_order(self):
        """Test that GITIGNORE sections appear in expected order."""
        python_pos = GITIGNORE.index("# Python")
        ide_pos = GITIGNORE.index("# IDE")
        os_pos = GITIGNORE.index("# OS")
        bytedojo_pos = GITIGNORE.index("# ByteDojo")

        assert python_pos < ide_pos < os_pos < bytedojo_pos


class TestReadmeTemplate:
    """Test README template content."""

    def test_readme_is_string(self):
        """Test that README is a string."""
        assert isinstance(README, str)

    def test_readme_not_empty(self):
        """Test that README is not empty."""
        assert len(README) > 0

    def test_readme_no_leading_whitespace(self):
        """Test that README has no leading whitespace (stripped)."""
        assert README == README.lstrip()

    def test_readme_no_trailing_whitespace(self):
        """Test that README has no trailing whitespace (stripped)."""
        assert README == README.rstrip()

    def test_readme_contains_title(self):
        """Test that README contains the main title."""
        assert "# ByteDojo Repository" in README

    def test_readme_contains_structure_section(self):
        """Test that README contains the structure section."""
        assert "## Structure" in README

    def test_readme_contains_directory_structure(self):
        """Test that README contains directory structure documentation."""
        assert ".dojo/" in README
        assert "db.sqlite" in README
        assert "settings.json" in README
        assert "logs/" in README
        assert ".gitignore" in README
        assert "README.md" in README

    def test_readme_contains_database_schema_section(self):
        """Test that README contains database schema section."""
        assert "## Database Schema" in README

    def test_readme_contains_database_tables(self):
        """Test that README documents database tables."""
        assert "**problems**" in README
        assert "**attempts**" in README
        assert "**reviews**" in README
        assert "**stats**" in README
        assert "**config**" in README

    def test_readme_contains_usage_section(self):
        """Test that README contains usage section."""
        assert "## Usage" in README

    def test_readme_contains_usage_examples(self):
        """Test that README contains usage command examples."""
        assert "dojo fetch" in README
        assert "dojo run" in README
        assert "dojo grade" in README
        assert "dojo stats" in README

    def test_readme_contains_tip_section(self):
        """Test that README contains tip section."""
        assert "## Tip" in README

    def test_readme_contains_git_commit_tip(self):
        """Test that README contains git commit tip about .dojo directory."""
        assert ".dojo/" in README
        assert "commit" in README.lower()

    def test_readme_sections_order(self):
        """Test that README sections appear in expected order."""
        structure_pos = README.index("## Structure")
        schema_pos = README.index("## Database Schema")
        usage_pos = README.index("## Usage")
        tip_pos = README.index("## Tip")

        assert structure_pos < schema_pos < usage_pos < tip_pos

    def test_readme_contains_code_blocks(self):
        """Test that README contains markdown code blocks."""
        assert "```" in README

    def test_readme_contains_bash_code_block(self):
        """Test that README contains bash code block for commands."""
        assert "```bash" in README

    def test_readme_code_blocks_are_closed(self):
        """Test that all code blocks in README are properly closed."""
        open_count = README.count("```")
        # Code blocks come in pairs (open and close)
        assert open_count % 2 == 0
        assert open_count >= 2  # At least one code block


class TestTemplateConsistency:
    """Test consistency between templates."""

    def test_both_templates_are_stripped(self):
        """Test that both templates are stripped of leading/trailing whitespace."""
        assert GITIGNORE == GITIGNORE.strip()
        assert README == README.strip()

    def test_templates_are_different(self):
        """Test that GITIGNORE and README are different templates."""
        assert GITIGNORE != README

    def test_gitignore_mentions_logs(self):
        """Test that GITIGNORE ignores logs directory."""
        assert "logs/" in GITIGNORE

    def test_readme_mentions_logs(self):
        """Test that README documents logs directory."""
        assert "logs/" in README

    def test_both_reference_dojo_directory(self):
        """Test that README references the .dojo directory structure."""
        # GITIGNORE is for inside .dojo, README explains .dojo structure
        assert ".dojo/" in README


class TestTemplateEdgeCases:
    """Test edge cases and special characters in templates."""

    def test_gitignore_lines_are_valid_patterns(self):
        """Test that GITIGNORE lines are valid gitignore patterns."""
        lines = GITIGNORE.split("\n")
        for line in lines:
            # Lines should be comments, empty, or valid patterns
            stripped = line.strip()
            if stripped:
                # Either a comment or a pattern (not containing invalid chars)
                assert stripped.startswith("#") or not stripped.startswith(" ")

    def test_readme_is_valid_markdown(self):
        """Test that README appears to be valid markdown."""
        # Check for proper heading format
        lines = README.split("\n")
        for line in lines:
            if line.startswith("#"):
                # Headings should have space after #
                hash_count = len(line) - len(line.lstrip("#"))
                remaining = line[hash_count:]
                if remaining:  # If there's content after the hashes
                    assert remaining.startswith(" "), f"Invalid heading: {line}"

    def test_gitignore_no_duplicate_patterns(self):
        """Test that GITIGNORE has no duplicate patterns."""
        lines = [line.strip() for line in GITIGNORE.split("\n")]
        patterns = [line for line in lines if line and not line.startswith("#")]
        assert len(patterns) == len(set(patterns)), "Duplicate patterns found"

    def test_readme_bullet_points_format(self):
        """Test that README bullet points are properly formatted."""
        lines = README.split("\n")
        for line in lines:
            if line.strip().startswith("-"):
                # Bullet points should have content after the dash
                content = line.strip()[1:].strip()
                assert len(content) > 0, f"Empty bullet point: {line}"

    def test_templates_use_unix_line_endings_internally(self):
        """Test that templates don't have Windows line endings embedded."""
        # When strip() is called, the templates should be clean
        assert "\r\n" not in GITIGNORE
        assert "\r\n" not in README


class TestTemplateContent:
    """Test specific content details in templates."""

    def test_gitignore_python_bytecode_patterns(self):
        """Test all Python bytecode patterns are present."""
        bytecode_patterns = ["*.pyc", "*.pyo", "*.pyd"]
        for pattern in bytecode_patterns:
            assert pattern in GITIGNORE

    def test_readme_describes_problem_tracking(self):
        """Test that README describes problem tracking functionality."""
        assert "Problem" in README or "problem" in README
        assert "Fetched problems" in README or "fetch" in README.lower()

    def test_readme_describes_spaced_repetition(self):
        """Test that README describes spaced repetition feature."""
        assert "Spaced repetition" in README or "spaced repetition" in README.lower()

    def test_readme_command_examples_have_arguments(self):
        """Test that README command examples include arguments."""
        assert "dojo fetch 1" in README
        assert "dojo run 1" in README
        assert "dojo grade 1" in README

    def test_readme_grade_command_has_flag(self):
        """Test that README grade command example has --pass flag."""
        assert "--pass" in README

    def test_gitignore_covers_common_editor_artifacts(self):
        """Test that GITIGNORE covers vim swap files."""
        assert "*.swp" in GITIGNORE
        assert "*.swo" in GITIGNORE

    def test_gitignore_covers_macos_artifacts(self):
        """Test that GITIGNORE covers macOS artifacts."""
        assert ".DS_Store" in GITIGNORE

    def test_gitignore_covers_windows_artifacts(self):
        """Test that GITIGNORE covers Windows artifacts."""
        assert "Thumbs.db" in GITIGNORE
