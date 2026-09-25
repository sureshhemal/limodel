"""Terminal commands."""

import typer

from limodel import config, workbook
from limodel.checks import find_problems
from limodel.data_loader import DataLoader

FILES = ("runs.csv", "stack_readings.csv", "tank_readings.csv", "samples.csv")

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


@app.command()
def convert(force: bool = typer.Option(False, "--force", "-f",
                                       help="Rewrite the files without asking first.")):
    """Rebuild the four data files from her workbook, copying every value as recorded."""
    path = _the_workbook()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    written = [name for name in FILES if (config.DATA_DIR / name).exists()]
    if written and not force:
        typer.echo(f"This replaces {len(written)} files in {config.DATA_DIR}. "
                   "A value corrected in a CSV but not in the workbook will be lost.")
        typer.confirm("Continue?", abort=True)

    conversion = workbook.convert(path, config.DATA_DIR)
    typer.echo(f"converted {len(conversion.runs)} runs: {' '.join(conversion.runs)}")
    for name, rows in conversion.files.items():
        typer.echo(f"  {name:20s} {rows:5d} rows")

    if not conversion.warnings:
        return

    typer.echo(f"\n{len(conversion.warnings)} warnings. "
               "Nothing was corrected; fix these in the workbook and convert again.\n")
    for warning in conversion.warnings:
        typer.echo(f"  {warning}")


@app.command()
def verify():
    """Compare every value in the data with the cell it came from in her workbook."""
    comparison = workbook.find_differences(_the_workbook(), config.DATA_DIR)
    typer.echo(f"compared {comparison.values} values across {comparison.sheets} sheets")

    if not comparison.differences:
        typer.echo("Every value matches the workbook.")
        return

    typer.echo(f"{len(comparison.differences)} differences\n")
    for difference in comparison.differences:
        typer.echo(f"  {difference}")


def _the_workbook():
    """Her workbook, or a plain message and a non-zero exit."""
    if not config.WORKBOOK:
        typer.echo("Set WORKBOOK in .env to her workbook, then run this again.")
        raise typer.Exit(code=1)

    if not config.WORKBOOK.exists():
        typer.echo(f"No workbook at {config.WORKBOOK}")
        raise typer.Exit(code=1)

    return config.WORKBOOK


if __name__ == "__main__":
    app()
