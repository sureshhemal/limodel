"""Loads the four CSV files in data/ into pandas tables."""

from pathlib import Path

import pandas as pd

from limodel.schema import Run, Sample, StackReading, TankReading
from limodel.sources.rows_the_schema_accepts import RowsTheSchemaAccepts


class CsvSource:
    """Reads runs, stack readings, tank readings and samples from a data directory.

    Each table is read once and kept, so repeated calls are free. Types and rules come
    from the schema models, which every table is validated against as it is handed out.
    A blank cell is missing (NaN): it means "not measured", never 0.
    """

    FILES = {
        "runs": "runs.csv",
        "stack_readings": "stack_readings.csv",
        "tank_readings": "tank_readings.csv",
        "samples": "samples.csv",
    }

    # Each table, the schema it answers to, what its rows become, and the column that names
    # a row so a refused one can be pointed at.
    CHECKED = {
        "runs": (Run, "Run", "run_code"),
        "stack_readings": (StackReading, "StackReading", "run_code"),
        "tank_readings": (TankReading, "TankReading", "run_code"),
        "samples": (Sample, "Sample", "sample_id"),
    }

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._tables = {}
        self._kept = {}
        self._refused = []

    def runs(self):
        return self._find_accepted("runs")

    def stack_readings(self):
        return self._find_accepted("stack_readings")

    def tank_readings(self):
        return self._find_accepted("tank_readings")

    def samples(self):
        return self._find_accepted("samples")

    def find_refused_rows(self):
        """Every row a schema would not take, across the tables read so far."""
        return tuple(self._refused)

    def _find_accepted(self, name):
        """One table, down to the rows its schema takes. The rest are kept, not raised."""
        if name not in self._kept:
            schema, model, key_column = self.CHECKED[name]
            kept, refused = RowsTheSchemaAccepts(schema, model, key_column) \
                .find_kept_and_refused(self._read(name))
            self._kept[name] = kept
            self._refused.extend(refused)

        return self._kept[name]

    def raw_tables(self):
        """Every table as it is stored, without checking it against the schema.

        Used by the checks, which must be able to report what is wrong with a file
        rather than refuse to open it.
        """
        tables = {}
        for name in self.FILES:
            try:
                tables[name] = self._read(name)
            except FileNotFoundError:
                tables[name] = None

        return tables

    def _read(self, name):
        if name not in self._tables:
            self._tables[name] = pd.read_csv(self._file_path(name))

        return self._tables[name]

    def _file_path(self, name) -> Path:
        path = self.data_dir / self.FILES[name]

        if not path.exists():
            raise FileNotFoundError(f"{path} not found; run scripts/convert_workbook.py")

        return path
