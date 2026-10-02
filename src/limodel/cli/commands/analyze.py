"""Reports the modelling: what it could use, and what it found."""

import typer

from limodel.analyzer import Action, Analyzer, Journal


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

        for entry in self._find_entries_in_order(self.journal.entries):
            typer.echo(f"  {entry.action!s:<9}{self._find_type(entry):<9}"
                       f"{entry.id:<15}{entry.reason}")

        typer.echo(f"using {len(analysis.used)} of {self._find_runs_loaded(analysis)} runs")

        return analysis

    def _find_runs_loaded(self, analysis):
        """How many runs there were before any were dropped."""
        dropped = [entry for entry in self.journal.entries if entry.action is Action.DROP]

        return len(analysis.used) + len(dropped)

    @staticmethod
    def _find_type(entry):
        """A plain word for the kind of record the entry is about."""
        return "reading" if entry.model.endswith("Reading") else entry.model.lower()

    @staticmethod
    def _find_entries_in_order(entries):
        """The entries as a reader wants them: by run, then by the minute of the reading.

        A check hands back its worst offender first, which is what clearing wants and the
        opposite of what reading wants: it puts minute 225 above minute 95. A run left out
        whole has no minute, so it comes before its own readings.
        """
        def when(entry):
            parts = entry.id.split(":")
            minute = int(parts[-1]) if parts[-1].isdigit() else -1

            return parts[0], minute, entry.id

        return sorted(entries, key=when)
