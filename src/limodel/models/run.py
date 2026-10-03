"""One experiment, with its readings and samples inside it."""

from datetime import date

from pydantic import BaseModel, Field, computed_field, field_validator

from limodel.models.stack_reading import StackReading
from limodel.models.tank_reading import TankReading

# The same membrane has been written more than one way: GO-10 and GO10 are one material. A
# name that squashes down to one of these is that membrane, whatever its hyphens and case.
# Anything else is kept exactly as written, so a membrane nobody has seen before is never
# quietly turned into one we have.
MEMBRANE_NAMES = {
    "go10": "GO-10",
    "pristine": "Pristine",
    "pdapei15cebt": "PDA/PEI/15CE/BT",
    "pdago10peibt": "PDA-GO10/PEI/BT",
}


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

    @field_validator("cem", mode="before")
    @classmethod
    def _find_the_membrane_meant(cls, written):
        """The one spelling of a membrane we know, so four parts of the app agree on it.

        Which runs are modelled, how they are grouped into fits, what counts as a repeat of
        what, and what the report prints are all decided by this name.
        """
        if not isinstance(written, str):
            return written

        squashed = "".join(letter for letter in written.lower() if letter.isalnum())

        return MEMBRANE_NAMES.get(squashed, written)

    @computed_field
    @property
    def id(self) -> str:
        """Identifies the run: its code is unique across the project."""
        return self.run_code

    stack_readings: list[StackReading] = Field(default_factory=list)
    tank_readings: list[TankReading] = Field(default_factory=list)
