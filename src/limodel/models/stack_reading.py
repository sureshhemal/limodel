"""The power log at one minute of a run."""

from pydantic import BaseModel, computed_field


class StackReading(BaseModel):
    """What the supply and the multimeter showed."""

    run_code: str
    minute: int
    supply_voltage_v: float | None = None
    supply_current_a: float | None = None
    meter_voltage_v: float | None = None
    meter_current_ma: float | None = None
    notes: str | None = None

    @computed_field
    @property
    def id(self) -> str:
        """Identifies the reading: one per run and minute."""
        return f"{self.run_code}:{self.minute}"

    @computed_field
    @property
    def run_id(self) -> str:
        """The run this reading belongs to."""
        return self.run_code
