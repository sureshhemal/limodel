"""Reports the modelling: what it could use, and what it found."""

import typer

from limodel.analyzer import Analyzer, Journal


class Analyze:
    """Prints the analysis, naming the runs it could not use before any result.

    The exclusions come first on purpose. A reader who sees only the answer should still
    know how many runs it came from.
    """

    def __init__(self, loader, journal: Journal):
        self.loader = loader
        self.journal = journal

    def run(self):
        """Run the modelling, print what it worked from, and hand the analysis back."""
        analysis = Analyzer(self.loader, self.journal).analyze()
        total = len(analysis.used) + len(analysis.waiting)

        for left_out in self.journal.dropped:
            typer.echo(f"  dropped  {left_out.run_code}   {left_out.reason}")

        typer.echo(f"using {total} runs, {len(analysis.used)} with lab results")

        if analysis.waiting:
            typer.echo(f"  skipped  {' '.join(analysis.waiting)}   no lab results yet")

        return analysis
