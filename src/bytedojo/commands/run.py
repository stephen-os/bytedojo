"""
Run command - Execute problem solutions for testing.
"""

import click
import subprocess
import os
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


# Language display colors
LANGUAGE_COLORS = {
    'python': 'blue',
    'java': 'red',
    'cpp': 'cyan',
}


def _get_repo():
    """Get repository or raise error if not initialized."""
    logger = get_logger()
    repo = DojoRepository()

    if not repo.is_initialized():
        logger.error("No .dojo repository found. Run 'dojo init' first.")
        raise click.ClickException("Repository not initialized")

    return repo


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
    result = subprocess.run(
        ['python', str(file_path)],
        cwd=file_path.parent
    )
    return result.returncode


def _run_java(file_path: Path, clean: bool) -> int:
    """Compile and run a Java file, return exit code."""
    logger = get_logger()
    directory = file_path.parent

    # Compile
    logger.debug(f"Compiling {file_path.name}...")
    compile_result = subprocess.run(
        ['javac', file_path.name],
        cwd=directory,
        capture_output=True,
        text=True
    )

    if compile_result.returncode != 0:
        click.echo(click.style("Compilation failed:", fg='red', bold=True))
        click.echo(compile_result.stderr)
        return compile_result.returncode

    # Run
    run_result = subprocess.run(
        ['java', 'Main'],
        cwd=directory
    )

    # Clean up if requested
    if clean:
        _clean_java_artifacts(directory)

    return run_result.returncode


def _run_cpp(file_path: Path, clean: bool) -> int:
    """Compile and run a C++ file, return exit code."""
    logger = get_logger()
    directory = file_path.parent

    # Determine output name
    stem = file_path.stem
    if os.name == 'nt':  # Windows
        output_name = f"{stem}.exe"
    else:
        output_name = stem

    output_path = directory / output_name

    # Compile
    logger.debug(f"Compiling {file_path.name}...")
    compile_result = subprocess.run(
        ['g++', '-o', output_name, file_path.name],
        cwd=directory,
        capture_output=True,
        text=True
    )

    if compile_result.returncode != 0:
        click.echo(click.style("Compilation failed:", fg='red', bold=True))
        click.echo(compile_result.stderr)
        return compile_result.returncode

    # Run
    run_result = subprocess.run(
        [str(output_path)],
        cwd=directory
    )

    # Clean up if requested
    if clean:
        _clean_cpp_artifacts(output_path)

    return run_result.returncode


def _clean_java_artifacts(directory: Path):
    """Remove .class files from directory."""
    logger = get_logger()
    for class_file in directory.glob('*.class'):
        class_file.unlink()
        logger.debug(f"Removed {class_file.name}")


def _clean_cpp_artifacts(output_path: Path):
    """Remove compiled binary."""
    logger = get_logger()
    if output_path.exists():
        output_path.unlink()
        logger.debug(f"Removed {output_path.name}")


def _run_problem(problem: dict, clean: bool) -> int:
    """Run a problem and return exit code."""
    logger = get_logger()
    language = problem.get('language', 'python')
    file_path_str = problem.get('file_path')

    if not file_path_str:
        raise click.ClickException("Problem has no associated file path")

    # Resolve relative path from current directory
    file_path = Path(file_path_str)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    if not file_path.exists():
        raise click.ClickException(f"File not found: {file_path}")

    _display_run_header(problem)

    # Run based on language
    if language == 'python':
        return _run_python(file_path)
    elif language == 'java':
        return _run_java(file_path, clean)
    elif language == 'cpp':
        return _run_cpp(file_path, clean)
    else:
        raise click.ClickException(f"Unsupported language: {language}")


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.group(invoke_without_command=True)
@click.pass_context
def run(ctx):
    """
    Run problem solutions for testing.

    Execute your solution code to see the output.

    Examples:
      dojo run problem 1              # Run problem #1 (Python)
      dojo run problem 1 --java       # Run Java version
      dojo run problem 1 --cpp --clean  # Run C++, clean up after
      dojo run last                   # Run last fetched problem
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@run.command()
@click.argument('problem_id', type=str)
@click.option('--python', 'language', flag_value='python', default=True, help='Run Python version (default)')
@click.option('--java', 'language', flag_value='java', help='Run Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Run C++ version')
@click.option('--clean', is_flag=True, help='Remove compiled artifacts after execution')
def problem(problem_id: str, language: str, clean: bool):
    """
    Run a specific problem by ID.

    Examples:
      dojo run problem 1             # Run Python version
      dojo run problem 1 --java      # Run Java version
      dojo run problem 1 --cpp --clean  # Run C++, clean after
    """
    logger = get_logger()
    repo = _get_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        problem_data = db.get_problem('leetcode', problem_id, language)

        if not problem_data:
            raise click.ClickException(
                f"Problem '{problem_id}' ({language}) not found in database. "
                f"Fetch it first with: dojo leetcode fetch {problem_id} --{language}"
            )

    exit_code = _run_problem(problem_data, clean)

    click.echo("")
    if exit_code == 0:
        click.echo(click.style("  Execution completed successfully", fg='green'))
    else:
        click.echo(click.style(f"  Execution failed (exit code: {exit_code})", fg='red'))


@run.command()
@click.option('--python', 'language', flag_value='python', default=True, help='Run Python version (default)')
@click.option('--java', 'language', flag_value='java', help='Run Java version')
@click.option('--cpp', 'language', flag_value='cpp', help='Run C++ version')
@click.option('--clean', is_flag=True, help='Remove compiled artifacts after execution')
def last(language: str, clean: bool):
    """
    Run the most recently fetched problem.

    Examples:
      dojo run last              # Run last fetched (Python)
      dojo run last --java       # Run last fetched Java
      dojo run last --cpp --clean  # Run last C++, clean after
    """
    logger = get_logger()
    repo = _get_repo()

    with DatabaseManager(repo.get_db_path()) as db:
        # Get the most recently fetched problem for this language
        problems = db.list_problems(language=language, limit=1)

        if not problems:
            raise click.ClickException(
                f"No {language} problems found. "
                f"Fetch one first with: dojo leetcode fetch <id> --{language}"
            )

        problem_data = problems[0]

    exit_code = _run_problem(problem_data, clean)

    click.echo("")
    if exit_code == 0:
        click.echo(click.style("  Execution completed successfully", fg='green'))
    else:
        click.echo(click.style(f"  Execution failed (exit code: {exit_code})", fg='red'))
