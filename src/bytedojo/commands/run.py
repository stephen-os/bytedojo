"""
Run command - Execute problem solutions for testing.
"""

import click
import subprocess
import os
from pathlib import Path
from typing import Optional

from bytedojo.core.logger import get_logger
from bytedojo.core.database import DatabaseManager
from bytedojo.core.search import find_problems, select_problem
from bytedojo.commands.utils import get_initialized_repo, LANGUAGE_COLORS


# Default timeout for subprocess execution (5 minutes)
DEFAULT_TIMEOUT_SECONDS = 300


def _display_run_header(problem: dict):
    """Display problem details before running."""
    problem_id = problem['problem_id']
    title = problem['title']
    language = problem.get('language', 'python')
    file_path = problem.get('file_path', '')

    click.echo("")
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo(click.style("  RUN PROBLEM", fg='cyan', bold=True))
    click.echo(click.style("=" * 60, fg='bright_black'))
    click.echo("")
    click.echo(f"  {problem_id}: {click.style(title, bold=True)}")
    click.echo(f"  Language: {click.style(language.upper(), fg=LANGUAGE_COLORS.get(language, 'white'))}")
    click.echo(f"  File: {file_path}")
    click.echo("")
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo(click.style("  OUTPUT", fg='cyan'))
    click.echo(click.style("-" * 60, fg='bright_black'))
    click.echo("")


def _run_python(file_path: Path) -> int:
    """Run a Python file and return exit code."""
    try:
        result = subprocess.run(
            ['python', str(file_path)],
            cwd=file_path.parent,
            timeout=DEFAULT_TIMEOUT_SECONDS
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        click.echo(click.style(f"Execution timed out after {DEFAULT_TIMEOUT_SECONDS} seconds", fg='red'))
        return 1


def _run_java(file_path: Path, build_dir: Path) -> int:
    """Compile and run a Java file, return exit code."""
    logger = get_logger()

    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)

    # Compile to build directory
    logger.debug(f"Compiling {file_path.name} to {build_dir}...")
    compile_result = subprocess.run(
        ['javac', '-d', str(build_dir), str(file_path)],
        capture_output=True,
        text=True
    )

    if compile_result.returncode != 0:
        click.echo(click.style("Compilation failed:", fg='red', bold=True))
        click.echo(compile_result.stderr)
        return compile_result.returncode

    # Run from build directory
    try:
        run_result = subprocess.run(
            ['java', 'Main'],
            cwd=build_dir,
            timeout=DEFAULT_TIMEOUT_SECONDS
        )
        return run_result.returncode
    except subprocess.TimeoutExpired:
        click.echo(click.style(f"Execution timed out after {DEFAULT_TIMEOUT_SECONDS} seconds", fg='red'))
        return 1


def _run_cpp(file_path: Path, build_dir: Path) -> int:
    """Compile and run a C++ file, return exit code."""
    logger = get_logger()

    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)

    # Determine output name
    stem = file_path.stem
    if os.name == 'nt':  # Windows
        output_name = f"{stem}.exe"
    else:
        output_name = stem

    output_path = build_dir / output_name

    # Compile to build directory
    logger.debug(f"Compiling {file_path.name} to {output_path}...")
    compile_result = subprocess.run(
        ['g++', '-o', str(output_path), str(file_path)],
        capture_output=True,
        text=True
    )

    if compile_result.returncode != 0:
        click.echo(click.style("Compilation failed:", fg='red', bold=True))
        click.echo(compile_result.stderr)
        return compile_result.returncode

    # Run
    try:
        run_result = subprocess.run(
            [str(output_path)],
            cwd=build_dir,
            timeout=DEFAULT_TIMEOUT_SECONDS
        )
        return run_result.returncode
    except subprocess.TimeoutExpired:
        click.echo(click.style(f"Execution timed out after {DEFAULT_TIMEOUT_SECONDS} seconds", fg='red'))
        return 1


def _run_problem(problem: dict, repo: DojoRepository) -> int:
    """Run a problem and return exit code."""
    logger = get_logger()
    language = problem.get('language', 'python')
    file_path_str = problem.get('file_path')
    problem_id = problem.get('problem_id', 'unknown')

    if not file_path_str:
        raise click.ClickException("Problem has no associated file path")

    # Resolve relative path from current directory
    file_path = Path(file_path_str)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    if not file_path.exists():
        raise click.ClickException(f"File not found: {file_path}")

    _display_run_header(problem)

    # Get build directory for compiled languages
    build_dir = repo.get_build_path(problem_id)

    # Run based on language
    if language == 'python':
        return _run_python(file_path)
    elif language == 'java':
        return _run_java(file_path, build_dir)
    elif language == 'cpp':
        return _run_cpp(file_path, build_dir)
    else:
        raise click.ClickException(f"Unsupported language: {language}")


def _display_result(exit_code: int):
    """Display execution result."""
    click.echo("")
    if exit_code == 0:
        click.echo(click.style("  Execution completed successfully", fg='green'))
    else:
        click.echo(click.style(f"  Execution failed (exit code: {exit_code})", fg='red'))


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.command()
@click.argument('identifier', required=False)
@click.option('--name', '-n', 'name_search', help='Search by problem name')
@click.option('--desc', '-d', 'desc_search', help='Search by description keywords')
@click.option('--python', 'language', flag_value='python', default=True, help='Run Python version (default)')
@click.option('--java', 'language', flag_value='java', help='Run Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Run C++ version')
@click.option('--last', is_flag=True, help='Run most recently fetched problem')
def run(identifier: Optional[str], name_search: Optional[str], desc_search: Optional[str], language: str, last: bool):
    """
    Run a problem solution.

    Examples:
      dojo run 1                    # Run problem #1 (Python)
      dojo run 1 --java             # Run Java version
      dojo run 1 --cpp              # Run C++ version
      dojo run --name "Two Sum"     # Search by name
      dojo run --last               # Run last fetched problem
    """
    repo = get_initialized_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        # Handle --last flag
        if last:
            problems = db.list_problems(language=language, limit=1)
            if not problems:
                raise click.ClickException(
                    f"No {language} problems found. "
                    f"Fetch one first with: dojo fetch <id> --{language}"
                )
            problem_data = problems[0]
        else:
            # Require either identifier, name, or desc
            if not identifier and not name_search and not desc_search:
                raise click.ClickException(
                    "Please specify a problem ID, --name, --desc, or --last\n"
                    "Examples:\n"
                    "  dojo run 1\n"
                    "  dojo run --name 'Two Sum'\n"
                    "  dojo run --last"
                )

            # Find matching problems
            matches = find_problems(
                db,
                identifier=identifier,
                name=name_search,
                desc=desc_search,
                language=language
            )

            if not matches:
                criteria = []
                if identifier:
                    criteria.append(f"ID '{identifier}'")
                if name_search:
                    criteria.append(f"name '{name_search}'")
                if desc_search:
                    criteria.append(f"description '{desc_search}'")

                criteria_str = ", ".join(criteria) if criteria else "given criteria"
                raise click.ClickException(
                    f"No {language} problems found matching {criteria_str}. "
                    f"Fetch one first with: dojo fetch <id> --{language}"
                )

            # Select problem (interactive if multiple)
            problem_data = select_problem(matches)
            if not problem_data:
                raise click.Abort()

    exit_code = _run_problem(problem_data, repo)
    _display_result(exit_code)
