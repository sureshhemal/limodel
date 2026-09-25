"""Rebuilds the four data files from the workbook."""

import typer

from limodel import workbook

FILES = ("runs.csv", "stack_readings.csv", "tank_readings.csv", "samples.csv")


class Convert:
    """Copies every value out of the workbook into the four CSV files.

    Nothing is corrected on the way: a value that looks wrong is written as recorded and
    reported afterwards, so the files stay a faithful copy of what was written down.
    """

    def __init__(self, workbook_path, data_dir, force=False):
        self.workbook_path = workbook_path
        self.data_dir = data_dir
        self.force = force

    def run(self):
        """Write the four files, then say what was written and what looks wrong."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._confirm_replacing()

        conversion = workbook.convert(self.workbook_path, self.data_dir)

        self._report_files(conversion)
        self._report_warnings(conversion)

    def _confirm_replacing(self):
        """Files already written are about to be replaced, so ask first."""
        written = [name for name in FILES if (self.data_dir / name).exists()]

        if not written or self.force:
            return

        typer.echo(f"This replaces {len(written)} files in {self.data_dir}. "
                   "A value corrected in a CSV but not in the workbook will be lost.")
        typer.confirm("Continue?", abort=True)

    @staticmethod
    def _report_files(conversion):
        typer.echo(f"converted {len(conversion.runs)} runs: {' '.join(conversion.runs)}")
        for name, rows in conversion.files.items():
            typer.echo(f"  {name:20s} {rows:5d} rows")

    @staticmethod
    def _report_warnings(conversion):
        """What looks wrong in the sheets. None of it was corrected."""
        if not conversion.warnings:
            return

        typer.echo(f"\n{len(conversion.warnings)} warnings. "
                   "Nothing was corrected; fix these in the workbook and convert again.\n")
        for warning in conversion.warnings:
            typer.echo(f"  {warning}")
