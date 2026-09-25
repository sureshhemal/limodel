"""The front door to the data: the only part of the app that knows where it comes from."""

import pandas as pd

from limodel import config
from limodel.models import Run
from limodel.sources.csv_source import CsvSource


class DataLoader:
    """Loads the runs, each with its readings inside it, and each sample on its reading.

    The rest of the program depends on this class alone. Which source it uses comes
    from config.DATA_SOURCE, so changing where the data lives is a configuration change
    rather than a code change.
    """

    def __init__(self):
        self._source = self._source_from_config()

    def load(self) -> list[Run]:
        """Every run, in file order, with its readings attached."""
        stack = self._source.stack_readings().sort_values(['run_code', 'minute']).groupby(by="run_code", sort=False)
        tanks = self._source.tank_readings().sort_values(['run_code', 'tank', 'minute']).groupby(by="run_code", sort=False)
        samples = self._source.samples().sort_values(['run_code', 'tank', 'minute']).groupby(by="run_code", sort=False)

        runs = []
        for run in self._source.runs().to_dict("records"):
            run_code = run["run_code"]

            runs.append(Run.model_validate({
                **self._without_missing(run),
                "stack_readings": self._rows_for(stack, run_code),
                "tank_readings": self._with_samples(self._rows_for(tanks, run_code),
                                                    self._rows_for(samples, run_code)),
            }))

        return runs

    def raw_tables(self):
        """Every table as stored, unchecked, for the checks to report on.

        load() refuses data that breaks the schema, which is right for calculating but
        useless for saying what to fix. This is the way in for that.
        """
        return self._source.raw_tables()

    @staticmethod
    def _with_samples(tank_readings, samples):
        """The same readings, each carrying the sample drawn from that tank at that minute."""
        grouped_samples_by_tank_and_minute = {(sample["tank"], sample["minute"]): sample for sample in samples}

        return [
            reading | {"sample": grouped_samples_by_tank_and_minute.get((reading["tank"], reading["minute"]))}
            for reading in tank_readings
        ]

    @classmethod
    def _rows_for(cls, groups, run_code):
        """One run's rows as dicts. A run whose rows have not arrived gets an empty list."""
        if run_code not in groups.groups:
            return []

        return [cls._without_missing(row)
                for row in groups.get_group(run_code).to_dict("records")]

    @staticmethod
    def _without_missing(row):
        """pandas writes a blank as NaN; the models want None."""
        return {column: None if pd.isna(value) else value for column, value in row.items()}

    @staticmethod
    def _source_from_config():
        if config.DATA_SOURCE == "csv":
            return CsvSource(config.DATA_DIR)

        raise ValueError(f"DATA_SOURCE={config.DATA_SOURCE!r} is not a source; use 'csv'")
