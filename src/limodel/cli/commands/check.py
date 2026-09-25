"""Lists everything wrong with the data."""

import typer

from limodel.checks import find_problems


class Check:
    """Reports every problem in the data instead of refusing to work with it.

    This is the lenient way in: it reads the tables as stored, so it can describe a value
    the schema would reject. Nothing here raises, whatever the files hold.
    """

    HEADINGS = f"{'table':15s} {'where':22s} {'column':20s} {'value':14s} problem"

    def __init__(self, loader):
        self.loader = loader

    def run(self):
        """Say what is wrong with every table, or that nothing is."""
        problems = find_problems(self.loader.raw_tables())

        if not problems:
            typer.echo("No problems found.")
            return

        typer.echo(f"{len(problems)} problems found\n")
        typer.echo(self.HEADINGS)
        for problem in problems:
            typer.echo(str(problem))
