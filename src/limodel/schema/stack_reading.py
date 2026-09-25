"""Shape of stack_readings.csv: the power log, one row per run and minute."""

import pandera.pandas as pa
from pandera.typing import Series


class StackReading(pa.DataFrameModel):
    run_code: Series[str]
    minute: Series[int] = pa.Field(ge=0)
    supply_voltage_v: Series[float] = pa.Field(ge=0, nullable=True)
    supply_current_a: Series[float] = pa.Field(ge=0, nullable=True)
    meter_voltage_v: Series[float] = pa.Field(ge=0, nullable=True)
    meter_current_ma: Series[float] = pa.Field(ge=0, nullable=True)
    notes: Series[str] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = True
        unique = ["run_code", "minute"]
