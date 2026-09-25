"""One experiment, with its readings and samples inside it."""

from datetime import date

from pydantic import BaseModel, Field, computed_field

from limodel.models.stack_reading import StackReading
from limodel.models.tank_reading import TankReading


class Run(BaseModel):
    """How a run was set up, and everything recorded during it."""

    run_code: str
    series: str
    run_date: date
    cem: str
    aem: str
    li_feed_mg_l: float
    mg_feed_mg_l: float
    licl_g_l: float | None = None
    mgcl2_6h2o_g_l: float | None = None
    conc_start_salt: str
    conc_start_g_l: float
    rinse_salt: str
    rinse_wt_pct: float
    set_current_ma: float | None = None
    flow_l_min: float
    area_cm2: float
    cell_pairs: int
    tare_conc_g: float
    tare_dil_g: float
    tare_rinse_g: float
    include: bool
    notes: str | None = None

    @computed_field
    @property
    def id(self) -> str:
        """Identifies the run: its code is unique across the project."""
        return self.run_code

    stack_readings: list[StackReading] = Field(default_factory=list)
    tank_readings: list[TankReading] = Field(default_factory=list)
