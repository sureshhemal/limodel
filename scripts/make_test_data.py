"""Builds a hundred made-up runs in test_data/, with the answers they should give.

The real data cannot exercise the modelling: its settings were never varied together, so no
curve can be fitted and the search can only refuse. These runs are a full grid with small
noise, so the fitting has something to find and the happy path can be tested.

Every run is built BACKWARDS. A recovery and a permselectivity are chosen first, then the
concentrations that would produce them are worked out and written as the lab results. So
test_data/expected.csv is not a record of what the code did: it is what the code must say.

    uv run python scripts/make_test_data.py
"""

import csv
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "test_data"

LI_G_PER_MOL = 6.94
MG_G_PER_MOL = 24.305

AREA_CM2 = 6.0
CELL_PAIRS = 10
MINUTES = tuple(range(0, 241, 15))
SAMPLED_MINUTES = (0, 240)
LI_FEED_MG_L = 400.0

MEMBRANES = ("GO-10", "Pristine", "PDA/PEI/15CE/BT", "PDA-GO10/PEI/BT")
CURRENT_DENSITIES = (4.5, 7.5, 13.67, 20.0, 25.67)       # mA/cm2
FEED_MASS_RATIOS = (2.5, 5.0, 10.0, 20.0)                # mg of Mg per mg of Li

# How good each membrane is, as a multiplier on selectivity and on how much lithium moves.
MEMBRANE_STRENGTH = {"GO-10": 1.00, "Pristine": 0.42,
                     "PDA/PEI/15CE/BT": 0.78, "PDA-GO10/PEI/BT": 0.71}

# The stack resistance differs by membrane, which is what makes the voltage gate bite.
MEMBRANE_VOLTS_PER_MA = {"GO-10": 0.62, "Pristine": 0.55,
                         "PDA/PEI/15CE/BT": 0.74, "PDA-GO10/PEI/BT": 0.70}

# How far the books fail to close, which is what the balance gaps read. A real run loses
# metal into the sample bottles, which nothing accounts for, so most gaps are positive; a
# few come out negative, where the readings simply disagree. The dilute's end sample and the
# rinse feed nothing but the gaps, so pushing them about cannot disturb a promised answer.
BALANCE_GAPS_PCT = (2.0, 5.5, 9.0, 14.0, 22.0, 31.0, 44.0, -6.0, -17.0, -38.0)

RECOVERY_NOISE = 1.4      # percentage points, so repeats agree closely enough to fit through
PERM_NOISE = 0.07
VOLTS_NOISE = 0.25


# The best current density these made-up membranes have, and the feed they are happiest at.
# The truth is written as a hump in LOGGED current, because that is the shape the fitting
# looks for, so a correct search has to land close to these.
BEST_RECOVERY_AT_MA_CM2 = 16.0
BEST_PERM_AT_MA_CM2 = 12.0
EASIEST_FEED_RATIO = 0.714


def find_true_recovery(current_density, feed_ratio, membrane):
    """The recovery a run should come to: a hump in current, falling as magnesium rises."""
    off_peak = math.log(current_density / BEST_RECOVERY_AT_MA_CM2) ** 2
    crowding = math.log(feed_ratio / EASIEST_FEED_RATIO)

    return max(1.5, (56.0 - 16.0 * off_peak - 9.5 * crowding) * MEMBRANE_STRENGTH[membrane])


def find_true_permselectivity(current_density, feed_ratio, membrane):
    """The permselectivity a run should come to, on the same shape."""
    off_peak = math.log(current_density / BEST_PERM_AT_MA_CM2) ** 2
    crowding = math.log(feed_ratio / EASIEST_FEED_RATIO)

    return max(0.12, (3.35 - 0.9 * off_peak - 0.46 * crowding) * MEMBRANE_STRENGTH[membrane])


def find_true_volts(current_density, membrane):
    """The highest the supply reaches, which is what the voltage gate reads."""
    return 2.1 + MEMBRANE_VOLTS_PER_MA[membrane] * current_density * AREA_CM2 / 6.0


def find_molar_feed_ratio(mass_ratio):
    """Magnesium per lithium in the feed, in mol/mol, which is the model's design column."""
    return (LI_FEED_MG_L * mass_ratio / MG_G_PER_MOL) / (LI_FEED_MG_L / LI_G_PER_MOL)


def find_litres_over_time(start_l, end_l):
    """A tank's litres at every minute, falling in a straight line between the two ends."""
    span = MINUTES[-1] - MINUTES[0]

    return {minute: start_l + (end_l - start_l) * (minute - MINUTES[0]) / span
            for minute in MINUTES}


class Run:
    """One made-up run: its setup, its readings, and the answers it must give."""

    def __init__(self, code, membrane, current_density, mass_ratio, dice):
        self.code = code
        self.membrane = membrane
        self.current_density = current_density
        self.mass_ratio = mass_ratio
        self.feed_ratio = find_molar_feed_ratio(mass_ratio)
        self.include = True
        self.faults = []

        self.recovery = find_true_recovery(current_density, self.feed_ratio, membrane) \
            + dice.gauss(0, RECOVERY_NOISE)
        self.permselectivity = max(0.1, find_true_permselectivity(
            current_density, self.feed_ratio, membrane) + dice.gauss(0, PERM_NOISE))
        self.volts = find_true_volts(current_density, membrane) + dice.gauss(0, VOLTS_NOISE)

        self.tare_conc_g = round(95.0 + dice.uniform(0, 30), 1)
        self.tare_dil_g = round(110.0 + dice.uniform(0, 30), 1)
        self.tare_rinse_g = round(42.0 + dice.uniform(0, 12), 1)

        self.conc_litres = find_litres_over_time(2.000, 1.978)
        self.dil_litres = find_litres_over_time(2.000, 1.931)
        self.rinse_litres = find_litres_over_time(4.000, 3.972)

        self._find_chemistry(dice)

    def _find_chemistry(self, dice):
        """The milligrams that must move for this run to give the answers it was given."""
        self.dil_li_start = LI_FEED_MG_L
        self.dil_mg_start = LI_FEED_MG_L * self.mass_ratio
        self.conc_li_start = round(60.0 + dice.uniform(0, 25), 2)
        self.conc_mg_start = round(dice.uniform(0.05, 0.4), 4)

        dil_li_start_mg = self.dil_li_start * self.dil_litres[0]
        dil_mg_start_mg = self.dil_mg_start * self.dil_litres[0]

        # Recovery is a share of what the feed held, so the lithium that crosses follows.
        li_crossed = self.recovery / 100 * dil_li_start_mg

        # Permselectivity fixes the charge ratio, and the charge ratio fixes the magnesium.
        measured_feed = (self.dil_li_start / LI_G_PER_MOL) / (self.dil_mg_start / MG_G_PER_MOL)
        charge_ratio = self.permselectivity * measured_feed
        mg_crossed = (li_crossed / LI_G_PER_MOL) * MG_G_PER_MOL / (2 * charge_ratio)

        # A little of each metal leaks into the rinse, which the gap does account for.
        li_leak = li_crossed * dice.uniform(0.01, 0.05)
        mg_leak = mg_crossed * dice.uniform(0.01, 0.05)

        # And some goes missing, which it does not. The share is chosen first and the dilute's
        # end is then written to produce exactly it, so the gap is a promise like any other.
        li_missing, self.li_gap_pct = self._find_missing(
            dice.choice(BALANCE_GAPS_PCT), li_crossed + li_leak, dil_li_start_mg)
        mg_missing, self.mg_gap_pct = self._find_missing(
            dice.choice(BALANCE_GAPS_PCT), mg_crossed + mg_leak, dil_mg_start_mg)

        self.conc_li_end = (self.conc_li_start * self.conc_litres[0] + li_crossed) \
            / self.conc_litres[240]
        self.conc_mg_end = (self.conc_mg_start * self.conc_litres[0] + mg_crossed) \
            / self.conc_litres[240]
        self.dil_li_end = (dil_li_start_mg - li_crossed - li_leak - li_missing) \
            / self.dil_litres[240]
        self.dil_mg_end = (dil_mg_start_mg - mg_crossed - mg_leak - mg_missing) \
            / self.dil_litres[240]
        self.rinse_li_start, self.rinse_mg_start = 2.0, 0.5
        self.rinse_li_end = (2.0 * self.rinse_litres[0] + li_leak) / self.rinse_litres[240]
        self.rinse_mg_end = (0.5 * self.rinse_litres[0] + mg_leak) / self.rinse_litres[240]

    @staticmethod
    def _find_missing(wanted_gap_pct, arrived_mg, started_mg):
        """The milligrams to lose for that gap, and the gap it really comes to.

        A tank cannot lose more than it holds, so a wide gap on a run that already recovered
        most of its lithium is cut back to what is left. The gap then written down is the one
        the readings will actually produce, not the one that was asked for.
        """
        gap = wanted_gap_pct / 100
        wanted = arrived_mg * gap / (1 - gap)
        room = (started_mg - arrived_mg) * 0.85       # leave the tank something to end with
        missing = min(wanted, room) if wanted > 0 else wanted

        return missing, 100 * missing / (arrived_mg + missing)

    @property
    def supply_current_a(self):
        """The current the supply holds all run, which is what the setting really means."""
        return self.current_density * AREA_CM2 / 1000.0

    def find_weight(self, tank, minute):
        """What the balance reads: the liquid plus the tank it sits in."""
        litres = {"conc": self.conc_litres, "dil": self.dil_litres,
                  "rinse": self.rinse_litres}[tank][minute]
        tare = {"conc": self.tare_conc_g, "dil": self.tare_dil_g,
                "rinse": self.tare_rinse_g}[tank]

        return round(litres * 1000 + tare, 1)

    def find_concentration(self, tank, metal, minute):
        """A tank's concentration, straight-lined between the two sampled minutes."""
        ends = {("conc", "li"): (self.conc_li_start, self.conc_li_end),
                ("conc", "mg"): (self.conc_mg_start, self.conc_mg_end),
                ("dil", "li"): (self.dil_li_start, self.dil_li_end),
                ("dil", "mg"): (self.dil_mg_start, self.dil_mg_end),
                ("rinse", "li"): (self.rinse_li_start, self.rinse_li_end),
                ("rinse", "mg"): (self.rinse_mg_start, self.rinse_mg_end)}[(tank, metal)]

        return ends[0] + (ends[1] - ends[0]) * minute / MINUTES[-1]


# Faults planted on purpose, so the preprocessor has something to catch. Each names the run
# it lands on, the kind of damage, and the minute, which is never a sampled minute: a fault
# at minute 0 or 240 would change the answers the dataset promises.
FAULTS = (
    ("T007", "weight far from the median", 75),
    ("T013", "ph outside the plausible range", 90),
    ("T021", "ph moving too fast", 105),
    ("T029", "temperature outside the plausible range", 60),
    ("T034", "temperature moving too fast", 120),
    ("T042", "conductivity jump that comes back", 135),
    ("T048", "the two voltmeters disagree", 45),
    ("T055", "the two ammeters are out of proportion", 150),
    ("T061", "supply current far from the median", 165),
    ("T066", "weight far from the median", 30),
)

NOT_MARKED_FOR_USE = ("T003", "T019", "T044", "T072", "T088", "T095")
LAB_HAS_NOT_ANSWERED = ("T011", "T027", "T053", "T079", "T091")


def find_runs(dice):
    """A hundred runs: a full grid of eighty, then twenty repeats of settings already run."""
    runs = []
    grid = [(membrane, current, ratio)
            for membrane in MEMBRANES
            for current in CURRENT_DENSITIES
            for ratio in FEED_MASS_RATIOS]

    for at, (membrane, current, ratio) in enumerate(grid, start=1):
        runs.append(Run(f"T{at:03d}", membrane, current, ratio, dice))

    # Five repeats per membrane, so the fitting has a bench scatter to be judged against.
    repeated = [(membrane, current, FEED_MASS_RATIOS[0])
                for membrane in MEMBRANES for current in CURRENT_DENSITIES]

    for at, (membrane, current, ratio) in enumerate(repeated, start=len(grid) + 1):
        runs.append(Run(f"T{at:03d}", membrane, current, ratio, dice))

    by_code = {run.code: run for run in runs}

    for code in NOT_MARKED_FOR_USE:
        by_code[code].include = False
        by_code[code].faults.append("not marked for use")

    for code, kind, minute in FAULTS:
        by_code[code].faults.append(f"{kind} at minute {minute}")

    for code in LAB_HAS_NOT_ANSWERED:
        by_code[code].faults.append("no lab results at the end")

    return runs


def find_tank_rows(run, dice):
    """Every tank reading of one run, with any planted fault already in it."""
    damage = {(kind, minute) for code, kind, minute in FAULTS if code == run.code}
    rows = []

    for tank in ("conc", "dil", "rinse"):
        for minute in MINUTES:
            weight = run.find_weight(tank, minute)
            conductivity = round(1200 + 48 * minute + dice.uniform(-20, 20), 1) if tank == "conc" \
                else round(19000 - 14 * minute + dice.uniform(-20, 20), 1)
            ph = round(5.9 - 0.0012 * minute + dice.uniform(-0.02, 0.02), 3)
            temp = round(21.0 + 0.0025 * minute + dice.uniform(-0.1, 0.1), 2)

            for kind, at in damage:
                if at != minute or tank != "conc":
                    continue
                if kind == "weight far from the median":
                    weight = round(weight * 0.12, 1)
                elif kind == "ph outside the plausible range":
                    ph = 0.4
                elif kind == "ph moving too fast":
                    ph = round(ph + 2.4, 3)
                elif kind == "temperature outside the plausible range":
                    temp = 58.0
                elif kind == "temperature moving too fast":
                    temp = round(temp + 4.5, 2)
                elif kind == "conductivity jump that comes back":
                    conductivity = round(conductivity * 4.5, 1)

            rows.append({"run_code": run.code, "minute": minute, "tank": tank,
                         "conductivity_us_cm": conductivity, "ph": ph, "temp_c": temp,
                         "weight_g": weight, "notes": ""})
    return rows


def find_stack_rows(run, dice):
    """The power log of one run, with any planted fault already in it."""
    damage = {(kind, minute) for code, kind, minute in FAULTS if code == run.code}
    rows = []

    for minute in MINUTES:
        # The supply holds its current exactly, as a real one nearly does. Two runs at the
        # same setting must read the same current, or nothing will see them as repeats.
        amps = round(run.supply_current_a, 4)
        volts = round(run.volts - 0.004 * minute + dice.uniform(-0.03, 0.03), 3)
        meter_volts = round(volts - dice.uniform(0.02, 0.07), 3)
        meter_ma = round(amps * 1000 * dice.uniform(0.97, 1.0), 2)

        for kind, at in damage:
            if at != minute:
                continue
            if kind == "the two voltmeters disagree":
                # Still a reading a meter could show, so the loader's schema lets it through
                # and the check gets its chance to reject it.
                meter_volts = round(max(0.3, volts - 11.0), 3)
            elif kind == "the two ammeters are out of proportion":
                meter_ma = round(amps * 1000 * 2.4, 2)
            elif kind == "supply current far from the median":
                amps = round(amps * 9, 4)

        rows.append({"run_code": run.code, "minute": minute, "supply_voltage_v": volts,
                     "supply_current_a": amps, "meter_voltage_v": meter_volts,
                     "meter_current_ma": meter_ma, "notes": ""})
    return rows


def find_sample_rows(run):
    """Two samples per tank, at the first minute and the last, as the lab reports them."""
    rows = []

    for tank in ("conc", "dil", "rinse"):
        for minute in SAMPLED_MINUTES:
            withheld = run.code in LAB_HAS_NOT_ANSWERED and minute == SAMPLED_MINUTES[-1]
            rows.append({
                "sample_id": f"{run.code}-{tank}-{minute}",
                "run_code": run.code, "minute": minute, "tank": tank,
                "li_mg_l": "" if withheld else round(run.find_concentration(tank, "li", minute), 4),
                "mg_mg_l": "" if withheld else round(run.find_concentration(tank, "mg", minute), 4),
                "na_mg_l": "", "k_mg_l": "", "ca_mg_l": "", "toc_ppm": "",
                "notes": "lab has not answered" if withheld else ""})
    return rows


def find_run_row(run):
    """One line of runs.csv, in the columns the loader's schema asks for."""
    return {"run_code": run.code, "series": "made_up", "run_date": "2026-10-03",
            "cem": run.membrane, "aem": "AR 204",
            "li_feed_mg_l": LI_FEED_MG_L, "mg_feed_mg_l": LI_FEED_MG_L * run.mass_ratio,
            "licl_g_l": 2.44, "mgcl2_6h2o_g_l": "",
            "conc_start_salt": "LiCl", "conc_start_g_l": 0.5,
            "rinse_salt": "Na2SO4", "rinse_wt_pct": 2, "set_current_ma": "",
            "flow_l_min": 0.2, "area_cm2": AREA_CM2, "cell_pairs": CELL_PAIRS,
            "tare_conc_g": run.tare_conc_g, "tare_dil_g": run.tare_dil_g,
            "tare_rinse_g": run.tare_rinse_g,
            "include": "true" if run.include else "false",
            "notes": "; ".join(run.faults)}


def find_expected_row(run):
    """What the analyzer must say about this run, or why it will say nothing."""
    unusable = (not run.include) or run.code in LAB_HAS_NOT_ANSWERED

    return {"run_code": run.code, "cem": run.membrane,
            "current_density_ma_cm2": round(run.current_density, 4),
            "feed_mg_li_ratio": round(run.feed_ratio, 6),
            "reaches_the_model": "false" if unusable else "true",
            "permselectivity": "" if unusable else round(run.permselectivity, 6),
            "li_recovery_pct": "" if unusable else round(run.recovery, 6),
            "highest_voltage_v": "" if unusable else round(run.highest_volts, 4),
            "li_balance_gap_pct": "" if unusable else round(run.li_gap_pct, 4),
            "mg_balance_gap_pct": "" if unusable else round(run.mg_gap_pct, 4),
            "left_out_because": "; ".join(run.faults) if unusable else ""}


def write(name, rows):
    """One CSV, with the columns taken from the first row."""
    path = HERE / name
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {name:22} {len(rows):6} rows")


def main():
    HERE.mkdir(exist_ok=True)
    dice = random.Random(20261003)      # fixed, so the same hundred runs come out every time
    runs = find_runs(dice)

    tank_rows = [row for run in runs for row in find_tank_rows(run, dice)]
    stack_rows = {run.code: find_stack_rows(run, dice) for run in runs}

    # The highest voltage is the largest reading actually written, not the level it was drawn
    # around, so the promise is read off the rows rather than guessed from them.
    for run in runs:
        run.highest_volts = max(row["supply_voltage_v"] for row in stack_rows[run.code])

    print(f"test_data/ from {len(runs)} runs")
    write("runs.csv", [find_run_row(run) for run in runs])
    write("tank_readings.csv", tank_rows)
    write("stack_readings.csv", [row for code in stack_rows for row in stack_rows[code]])
    write("samples.csv", [row for run in runs for row in find_sample_rows(run)])
    write("expected.csv", [find_expected_row(run) for run in runs])


if __name__ == "__main__":
    main()
