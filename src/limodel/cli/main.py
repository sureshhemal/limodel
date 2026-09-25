"""Terminal commands."""

import typer

from limodel.checks import find_problems
from limodel.data_loader import DataLoader

app = typer.Typer(help="Find the best electrodialysis setup for Li selectivity over Mg.")


@app.callback()
def main():
    """Keeps the commands as subcommands, so `limodel check` works."""


@app.command()
def check():
    """List everything wrong with the data. Fix these in the workbook, then run again."""
    problems = find_problems(DataLoader().raw_tables())

    if not problems:
        typer.echo("No problems found.")
        return

    typer.echo(f"{len(problems)} problems found\n")
    typer.echo(f"{'table':15s} {'where':22s} {'column':20s} {'value':14s} problem")
    for problem in problems:
        typer.echo(str(problem))


if __name__ == "__main__":
    app()
