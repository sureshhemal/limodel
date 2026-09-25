"""Shape of samples.csv: the lab results, one row per sample."""

import pandera.pandas as pa
from pandera.typing import Series

from limodel.schema.tank_reading import TANKS


class Sample(pa.DataFrameModel):
    sample_id: Series[str] = pa.Field(unique=True)
    run_code: Series[str]
    minute: Series[int] = pa.Field(ge=0)
    tank: Series[str] = pa.Field(isin=TANKS)
    li_mg_l: Series[float] = pa.Field(ge=0, nullable=True)
    mg_mg_l: Series[float] = pa.Field(ge=0, nullable=True)
    na_mg_l: Series[float] = pa.Field(ge=0, nullable=True)
    k_mg_l: Series[float] = pa.Field(ge=0, nullable=True)
    ca_mg_l: Series[float] = pa.Field(ge=0, nullable=True)
    toc_ppm: Series[float] = pa.Field(ge=0, nullable=True)
    notes: Series[str] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = True
        unique = ["run_code", "minute", "tank"]
