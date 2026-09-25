"""Loads the four CSV files in data/ into pandas tables."""

from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame

from limodel.schema import Run, Sample, StackReading, TankReading


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

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._tables = {}

    @pa.check_types
    def runs(self) -> DataFrame[Run]:
        return self._read("runs")

    @pa.check_types
    def stack_readings(self) -> DataFrame[StackReading]:
        return self._read("stack_readings")

    @pa.check_types
    def tank_readings(self) -> DataFrame[TankReading]:
        return self._read("tank_readings")

    @pa.check_types
    def samples(self) -> DataFrame[Sample]:
        return self._read("samples")

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
