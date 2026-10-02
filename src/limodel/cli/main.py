"""The terminal app: which commands it has, and what each one is given."""

import typer

from limodel import config
from limodel.analyzer import Journal
from limodel.cli.commands.analyze import Analyze
from limodel.cli.commands.check import Check
from limodel.cli.commands.convert import Convert
from limodel.cli.commands.verify import Verify
from limodel.cli.settings import the_workbook
from limodel.data_loader import DataLoader

app = typer.Typer(help="Find the best electrodialysis setup for Li selectivity over Mg.")


@app.callback()
def main():
    """Keeps the commands as subcommands, so `limodel check` works."""


@app.command()
def convert(force: bool = typer.Option(False, "--force", "-f",
                                       help="Rewrite the files without asking first.")):
    """Rebuild the four data files from the workbook, copying every value as recorded."""
    Convert(the_workbook(), config.DATA_DIR, force).run()


@app.command()
def check():
    """List everything wrong with the data. Fix these in the workbook, then run again."""
    Check(DataLoader()).run()


@app.command()
def analyze():
    """Calculate every run, fit the polynomials, and report the best setup."""
    Analyze(DataLoader(), Journal()).run()


@app.command()
def verify():
    """Compare every value in the data with the cell it came from in the workbook."""
    Verify(the_workbook(), config.DATA_DIR).run()


if __name__ == "__main__":
    app()
