import click

def echo(message: str):
    """Standard output."""
    click.echo(message)

def success(message: str):
    """Success message."""
    click.secho(message, fg="green")

def warn(message: str):
    """Warning message."""
    click.secho(f"Warning: {message}", fg="yellow")

def error(message: str):
    """Error message."""
    click.secho(f"Error: {message}", fg="red", bold=True)

def info(message: str):
    """Info/hint message."""
    click.secho(message, fg="cyan")

def header(message: str):
    """Section header."""
    click.secho(message, fg="bright_white", bold=True)