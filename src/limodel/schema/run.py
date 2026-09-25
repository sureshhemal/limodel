"""Shape of runs.csv: one row per experiment."""

import pandera.pandas as pa
from pandera.typing import Series


class Run(pa.DataFrameModel):
    run_code: Series[str] = pa.Field(unique=True)
    series: Series[str]
    run_date: Series[pa.DateTime]
    cem: Series[str]
    aem: Series[str]
    li_feed_mg_l: Series[float] = pa.Field(gt=0)
    mg_feed_mg_l: Series[float] = pa.Field(gt=0)
    licl_g_l: Series[float] = pa.Field(gt=0, nullable=True)
    mgcl2_6h2o_g_l: Series[float] = pa.Field(gt=0, nullable=True)
    conc_start_salt: Series[str]
    conc_start_g_l: Series[float] = pa.Field(ge=0)
    rinse_salt: Series[str]
    rinse_wt_pct: Series[float] = pa.Field(gt=0)
    set_current_ma: Series[float] = pa.Field(gt=0, nullable=True)
    flow_l_min: Series[float] = pa.Field(gt=0)
    area_cm2: Series[float] = pa.Field(gt=0)
    cell_pairs: Series[int] = pa.Field(gt=0)
    tare_conc_g: Series[float] = pa.Field(ge=0)
    tare_dil_g: Series[float] = pa.Field(ge=0)
    tare_rinse_g: Series[float] = pa.Field(ge=0)
    include: Series[bool]
    notes: Series[str] = pa.Field(nullable=True)

    class Config:
        coerce = True   # convert values to the declared type on load
        strict = True   # the columns must be exactly these — no more, no fewer
