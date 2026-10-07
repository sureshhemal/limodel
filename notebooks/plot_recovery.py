"""Plots lithium recovery against every setting and outcome, with the fitted curves on top.

The curves come from the fitted model itself, not from a second fit, so what is drawn is
what `limodel analyze` reports.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from limodel.analyzer.calculate.calculator import Calculator
from limodel.analyzer.journal import Journal
from limodel.analyzer.model.design_points import DesignPoints
from limodel.analyzer.model.surrogate import Surrogate
from limodel.analyzer.preprocess.preprocessor import Preprocessor
from limodel.data_loader import DataLoader

RECOVERY_FLOOR = 35.0
COLOURS = {"GO-10": "#1f77b4", "Pristine": "#d62728",
           "PDA/PEI/15CE/BT": "#2ca02c", "PDA-GO10/PEI/BT": "#9467bd"}

journal = Journal()
runs = Preprocessor(journal).run(DataLoader().load())
results = Calculator(journal).find_results(runs)
models = Surrogate(journal).find_models(results)


def find_colour(cem):
    return COLOURS.get(cem, "#7f7f7f")


def draw_points(axes, xs, ys, cems, codes):
    """One dot per run, coloured by membrane and labelled with its run code."""
    for x, y, cem, code in zip(xs, ys, cems, codes):
        if x is None or y is None:
            continue
        axes.scatter(x, y, color=find_colour(cem), s=55, zorder=3,
                     edgecolor="white", linewidth=0.8)
        axes.annotate(code, (x, y), fontsize=6.5, color="#333333",
                      xytext=(4, 4), textcoords="offset points")


def find_column(field_name):
    return [getattr(result, field_name) for result in results]


cems = find_column("cem")
codes = find_column("run_code")
recovery = find_column("li_recovery_pct")

# ---- figure one: recovery against everything else -------------------------------------

PANELS = (
    ("current_density_ma_cm2", "current density (mA/cm2)", True),
    ("feed_mg_li_ratio", "feed Mg/Li (mol/mol)", True),
    ("highest_voltage_v", "highest voltage (V)", False),
    ("charge_passed_mah_cm2", "charge passed (mA.h/cm2)", False),
    ("permselectivity", "permselectivity", False),
)

figure, panels = plt.subplots(2, 3, figsize=(15, 8.5))
figure.suptitle("Lithium recovery against every other attribute, 16 runs", fontsize=13)

for axes, (field_name, label, logx) in zip(panels.flat, PANELS):
    draw_points(axes, find_column(field_name), recovery, cems, codes)
    axes.axhline(RECOVERY_FLOOR, color="#999999", linestyle="--", linewidth=1)
    axes.set_xlabel(label)
    axes.set_ylabel("Li recovery (%)")
    if logx:
        axes.set_xscale("log")
    axes.grid(alpha=0.25)

# The last panel is the membranes side by side, which no x axis above can show.
last = panels.flat[5]
for at, cem in enumerate(sorted(set(cems))):
    ys = [y for y, c in zip(recovery, cems) if c == cem]
    last.scatter([at] * len(ys), ys, color=find_colour(cem), s=55,
                 edgecolor="white", linewidth=0.8)
last.axhline(RECOVERY_FLOOR, color="#999999", linestyle="--", linewidth=1)
last.set_xticks(range(len(set(cems))))
last.set_xticklabels([c[:12] for c in sorted(set(cems))], rotation=20, fontsize=8)
last.set_ylabel("Li recovery (%)")
last.set_xlabel("membrane")
last.grid(alpha=0.25)

figure.text(0.5, 0.012, f"dashed line: the {RECOVERY_FLOOR:.0f}% recovery floor the search gates on",
            ha="center", fontsize=9, color="#555555")
figure.tight_layout(rect=(0, 0.03, 1, 0.96))
figure.savefig("output/recovery-vs-attributes.png", dpi=150)

# ---- figure two: the fitted polynomial over the readings -----------------------------

def draw_fit(axes, cem, field_name, setting, label, ylabel):
    """The fitted curve across one setting, with that membrane's own runs under it."""
    rows = [result for result in results if result.cem == cem]
    fit = models.fits.get(cem, {}).get(field_name)
    points = DesignPoints(rows)
    at = DesignPoints.SETTING_NAMES.index(setting)
    other = 1 - at

    xs = [getattr(row, setting) for row in rows]
    ys = [getattr(row, field_name) for row in rows]
    draw_points(axes, xs, ys, [cem] * len(rows), [row.run_code for row in rows])

    if fit is not None:
        held = np.median([getattr(row, DesignPoints.SETTING_NAMES[other]) for row in rows])
        grid = np.linspace(min(xs), max(xs), 120)
        drawn = []
        for value in grid:
            real = [0.0, 0.0]
            real[at], real[other] = value, held
            coded = points.find_coded_from_real(real)
            drawn.append(fit.find_prediction(coded) if coded else None)
        axes.plot(grid, drawn, color=find_colour(cem), linewidth=2, alpha=0.85)

        terms = ", ".join(f"{name} {value:+.3g}"
                          for name, value in fit.find_terms_and_coefficients())
        spread = fit.replicate_spread[0] if fit.replicate_spread else float("nan")
        beaten = "beats the bench" if fit.leave_one_out_rmse < spread else "WORSE than the bench"
        axes.set_title(f"{cem} - {label}\n{terms}\n"
                       f"off by {fit.leave_one_out_rmse:.3g}, bench scatter {spread:.3g} ({beaten})",
                       fontsize=8.5)
    else:
        axes.set_title(f"{cem} - {label}\nnot fitted: {models.not_fitted.get(cem, 'no fit')}",
                       fontsize=8.5)

    axes.set_xlabel(label)
    axes.set_ylabel(ylabel)
    axes.set_xscale("log")
    axes.grid(alpha=0.25)


FITS = (
    ("GO-10", "feed_mg_li_ratio", "feed Mg/Li (mol/mol)"),
    ("GO-10", "current_density_ma_cm2", "current density (mA/cm2)"),
    ("Pristine", "current_density_ma_cm2", "current density (mA/cm2)"),
)

figure, panels = plt.subplots(2, 3, figsize=(15, 9))
figure.suptitle("The fitted polynomial over the readings it was fitted to", fontsize=13)

for column, (cem, setting, label) in enumerate(FITS):
    draw_fit(panels[0][column], cem, "li_recovery_pct", setting, label, "Li recovery (%)")
    panels[0][column].axhline(RECOVERY_FLOOR, color="#999999", linestyle="--", linewidth=1)
    draw_fit(panels[1][column], cem, "permselectivity", setting, label, "permselectivity")
    panels[1][column].axhline(0.5, color="#999999", linestyle="--", linewidth=1)

figure.text(0.5, 0.012,
            "top row dashed: the 35% recovery floor.  bottom row dashed: permselectivity 0.5, "
            "which is no preference between Li and Mg",
            ha="center", fontsize=9, color="#555555")
figure.tight_layout(rect=(0, 0.03, 1, 0.95))
figure.savefig("output/recovery-polynomial.png", dpi=150)

print("wrote output/recovery-vs-attributes.png and output/recovery-polynomial.png")
