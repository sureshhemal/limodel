"""Shape of tank_readings.csv: one row per run, minute and tank."""

import pandera.pandas as pa
from pandera.typing import Series

TANKS = ("conc", "dil", "rinse")


class TankReading(pa.DataFrameModel):
    run_code: Series[str]
    minute: Series[int] = pa.Field(ge=0)
    tank: Series[str] = pa.Field(isin=TANKS)
    conductivity_us_cm: Series[float] = pa.Field(ge=0, nullable=True)
    ph: Series[float] = pa.Field(ge=0, le=14, nullable=True)
    temp_c: Series[float] = pa.Field(nullable=True)
    weight_g: Series[float] = pa.Field(ge=0, nullable=True)
    notes: Series[str] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = True
        unique = ["run_code", "minute", "tank"]
