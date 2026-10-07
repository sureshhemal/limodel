"""One run, as the modelling and the report read it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    """What one run turned out to be: the two settings it was run at, and what came of them.

    Nothing here is in the data files; every field was worked out from tank weights, lab
    results and the power log. The last three are diagnostics and may be None on a run that
    is otherwise sound.
    """

    run_code: str
    cem: str
    current_density_ma_cm2: float
    feed_mg_li_ratio: float

    # How hard the run was pushed: moles of charge per mole of lithium the feed offered. It
    # is a setting like the other two, because it is chosen when the run is stopped.
    charge_per_li_offered: float | None
    permselectivity: float
    li_recovery_pct: float
    highest_voltage_v: float | None
    charge_passed_mah_cm2: float | None
    energy_per_mol_li_wh: float | None
    li_balance_gap_pct: float | None
    mg_balance_gap_pct: float | None

    # Carried so a recommendation can be put in the terms the bench is set in: milliamps on
    # a dial, milligrams per litre in a bottle, and hours on a clock.
    area_cm2: float | None = None
    li_feed_mg_l: float | None = None
    li_offered_mmol: float | None = None
    cell_pairs: int | None = None

    @property
    def id(self) -> str:
        """Identifies the result, because the journal takes the id off whatever it is given."""
        return self.run_code
