"""Settings turned into values a command can use, or a plain message and a non-zero exit.

A missing setting is the one kind of failure the terminal should explain rather than throw
a traceback at, so the commands ask for their settings here instead of reading config.
"""

import typer

from limodel import config


def the_workbook():
    """The workbook to read, once it is known to be set and to exist."""
    if not config.WORKBOOK:
        typer.echo("Set WORKBOOK in .env to the workbook to read, then run this again.")
        raise typer.Exit(code=1)

    if not config.WORKBOOK.exists():
        typer.echo(f"No workbook at {config.WORKBOOK}")
        raise typer.Exit(code=1)

    return config.WORKBOOK
