"""Compares the data with the workbook it was built from."""

import typer

from limodel import workbook


class Verify:
    """Checks that every value in the data is the value in the cell it came from.

    Convert copies; this says whether the copy is faithful. A difference means either the
    CSV was edited by hand or the workbook has changed since it was converted.
    """

    def __init__(self, workbook_path, data_dir):
        self.workbook_path = workbook_path
        self.data_dir = data_dir

    def run(self):
        """Say how much was compared, then everything that does not match."""
        comparison = workbook.find_differences(self.workbook_path, self.data_dir)
        typer.echo(f"compared {comparison.values} values across {comparison.sheets} sheets")

        if not comparison.differences:
            typer.echo("Every value matches the workbook.")
            return

        typer.echo(f"{len(comparison.differences)} differences\n")
        for difference in comparison.differences:
            typer.echo(f"  {difference}")
