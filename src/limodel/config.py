"""Settings, read once from the environment (and from .env if there is one)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# for csv data
DATA_SOURCE = os.getenv("DATA_SOURCE", "csv").strip().lower()
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# the source workbook the CSV files are built from and checked against
_workbook = os.getenv("WORKBOOK", "").strip()
WORKBOOK = Path(_workbook).expanduser() if _workbook else None

# the membranes the modelling is about; a run on any other is dropped in preprocessing
MEMBRANES_MODELLED = tuple(
    name.strip() for name in os.getenv("MEMBRANES_MODELLED", "GO-10").split(",") if name.strip()
)

# The limits any recommended setup has to clear. The floor is a judgement about what makes a
# run worth doing at all and may be revised; the ceiling is physical, the point above which
# the membranes fail.
RECOVERY_FLOOR_PCT = float(os.getenv("RECOVERY_FLOOR_PCT", "35.0"))
VOLTAGE_CEILING_V = float(os.getenv("VOLTAGE_CEILING_V", "20.0"))
