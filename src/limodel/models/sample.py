"""One sample sent to the lab."""

from pydantic import BaseModel, computed_field


class Sample(BaseModel):
    """Lab results for liquid drawn from one tank at one minute."""

    sample_id: str
    run_code: str
    minute: int
    tank: str
    li_mg_l: float | None = None
    mg_mg_l: float | None = None
    na_mg_l: float | None = None
    k_mg_l: float | None = None
    ca_mg_l: float | None = None
    toc_ppm: float | None = None
    notes: str | None = None

    @computed_field
    @property
    def id(self) -> str:
        """The lab's label, which is unique across every run."""
        return self.sample_id

    @computed_field
    @property
    def run_id(self) -> str:
        """The run this sample came from."""
        return self.run_code

    @computed_field
    @property
    def tank_id(self) -> str:
        """The tank reading this sample was drawn from."""
        return f"{self.run_code}:{self.tank}:{self.minute}"
