"""The front door to the data: the only part of the app that knows where it comes from."""

from limodel import config
from limodel.sources.csv_source import CsvSource


class DataLoader:
    """Hands out the four tables, whatever they are stored in.

    The rest of the program depends on this class alone. Which source it uses comes
    from config.DATA_SOURCE, so changing where the data lives is a configuration change
    rather than a code change.
    """

    def __init__(self):
        self.source = self._source_from_config()

    def runs(self):
        """One row per experiment, keyed by run_code."""
        return self.source.runs()

    def stack_readings(self):
        """The power log: one row per run and minute."""
        return self.source.stack_readings()

    def tank_readings(self):
        """One row per run, minute and tank."""
        return self.source.tank_readings()

    def samples(self):
        """Lab results, one row per sample."""
        return self.source.samples()

    def raw_tables(self):
        """Every table as stored, unchecked. A missing table comes back as None."""
        return self.source.raw_tables()

    @staticmethod
    def _source_from_config():
        if config.DATA_SOURCE == "csv":
            return CsvSource(config.DATA_DIR)

        raise ValueError(f"DATA_SOURCE={config.DATA_SOURCE!r} is not a source; use 'csv'")
