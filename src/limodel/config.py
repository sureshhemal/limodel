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
