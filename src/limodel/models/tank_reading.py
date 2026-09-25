"""One tank at one minute of a run."""

from pydantic import BaseModel, computed_field

from limodel.models.sample import Sample


class TankReading(BaseModel):
    """What was measured on the concentrate, diluate or rinse.

    A sample is drawn from a tank at a moment, so it hangs off the reading taken at
    that moment. Most readings have none: she logs the tanks far more often than she
    fills a sample bottle.
    """

    run_code: str
    minute: int
    tank: str
    conductivity_us_cm: float | None = None
    ph: float | None = None
    temp_c: float | None = None
    weight_g: float | None = None
    notes: str | None = None
    sample: Sample | None = None

    @computed_field
    @property
    def id(self) -> str:
        """Identifies the reading: one per run, tank and minute."""
        return f"{self.run_code}:{self.tank}:{self.minute}"

    @computed_field
    @property
    def run_id(self) -> str:
        """The run this reading belongs to."""
        return self.run_code
