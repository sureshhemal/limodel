"""Draws the curve the search reads its recommendation off.

Works on whatever DATA_DIR points at, so it can show the made-up runs in test_data/ where
the search actually answers, as well as the real ones where it refuses.

    DATA_DIR=test_data MEMBRANES_MODELLED=GO-10 uv run python notebooks/plot_best_setup.py
"""

import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from limodel.analyzer.calculate.calculator import Calculator
from limodel.analyzer.journal import Journal
from limodel.analyzer.model.best_setup_under_the_gates import (HIGHEST_VOLTAGE, LI_RECOVERY,
                                                               PERMSELECTIVITY)
from limodel.analyzer.model.design_points import DesignPoints
from limodel.analyzer.model.surrogate import Surrogate
from limodel.analyzer.preprocess.preprocessor import Preprocessor
from limodel.data_loader import DataLoader

MEMBRANE = os.environ.get("MEMBRANE", "GO-10")
RECOVERY_FLOOR, VOLTAGE_CEILING = 35.0, 20.0

journal = Journal()
results = Calculator(journal).find_results(Preprocessor(journal).run(DataLoader().load()))
models = Surrogate(journal).find_models(results)

rows = [result for result in results if result.cem == MEMBRANE]
fits = models.fits[MEMBRANE]
points = DesignPoints(rows)
setup = models.best_setups.get(MEMBRANE)

currents = np.array([row.current_density_ma_cm2 for row in rows])
feeds = np.array([row.feed_mg_li_ratio for row in rows])


def find_predictions(field_name, current_grid, feed_grid):
    """What the fit says at each point of a grid, in real units."""
    fit = fits[field_name]
    drawn = np.empty_like(current_grid, dtype=float)

    for at, (current, feed) in enumerate(zip(current_grid.ravel(), feed_grid.ravel())):
        coded = points.find_coded_from_real([float(current), float(feed)])
        drawn.ravel()[at] = fit.find_prediction(coded)

    return drawn


settings = setup.find_settings() if setup else None
predicted = setup.find_best_predictions() if setup else None
best_current = settings[0] if settings else float(np.median(currents))
best_feed = settings[1] if settings else float(min(feeds))
best_perm = predicted[PERMSELECTIVITY] if predicted else None
line = np.linspace(currents.min(), currents.max(), 300)
feed_line = np.linspace(feeds.min(), feeds.max(), 300)

figure, panels = plt.subplots(1, 4, figsize=(21.5, 5.4))
headline = (f"{MEMBRANE}: the curve the recommendation is read off  "
            f"({len(rows)} runs, from {os.environ.get('DATA_DIR', 'data')}/)")

if settings:
    headline += (f"\nrun it at {best_current:.1f} mA/cm2 with a feed of {best_feed:.2f} mol/mol"
                 f"  ->  permselectivity {best_perm:.2f},"
                 f"  recovery {predicted[LI_RECOVERY]:.1f} % (floor {RECOVERY_FLOOR:.0f}),"
                 f"  {predicted[HIGHEST_VOLTAGE]:.1f} V (ceiling {VOLTAGE_CEILING:.0f})")
else:
    headline += f"\nno setup recommended: {models.best_setups[MEMBRANE].find_refusal()}"

figure.suptitle(headline, fontsize=11)

# --- the curve across current density, at the feed the search chose
near = np.isclose(feeds, best_feed, rtol=0.02)
panels[0].plot(line, find_predictions(PERMSELECTIVITY, line, np.full_like(line, best_feed)),
               color="#1f77b4", linewidth=2.5, label="the fitted curve")
panels[0].scatter(currents[near], [row.permselectivity for row, keep in zip(rows, near) if keep],
                  s=80, color="#1f77b4", edgecolor="white", zorder=3, label="runs at this feed")
panels[0].scatter(currents[~near], [row.permselectivity for row, keep in zip(rows, ~near) if keep],
                  s=30, color="#bbbbbb", zorder=2, label="runs at other feeds")
if settings:
    panels[0].axvline(best_current, color="#d62728", linestyle="--", linewidth=1.5)
    panels[0].scatter([best_current], [best_perm], marker="*", s=420,
                      color="#d62728", zorder=5, label=f"the peak, {best_current:.1f} mA/cm2")
panels[0].axhline(0.5, color="#999999", linewidth=1)
panels[0].set_title(f"across current density, at a feed of {best_feed:.2f} mol/mol\n"
                    "a real peak: the curve falls away on both sides", fontsize=9)
panels[0].set_xlabel("current density (mA/cm2)")
panels[0].set_ylabel("permselectivity")
panels[0].legend(fontsize=7.5)
panels[0].grid(alpha=0.25)

# --- the curve across the feed ratio, at the current the search chose
panels[1].plot(feed_line,
               find_predictions(PERMSELECTIVITY, np.full_like(feed_line, best_current), feed_line),
               color="#1f77b4", linewidth=2.5)
panels[1].scatter(feeds, [row.permselectivity for row in rows], s=50, color="#aaaaaa",
                  edgecolor="white", zorder=3)
if settings:
    panels[1].scatter([best_feed], [best_perm], marker="*", s=420, color="#d62728",
                      zorder=5)
panels[1].axvline(feeds.min(), color="#d62728", linestyle=":", linewidth=1.5)
panels[1].axhline(0.5, color="#999999", linewidth=1)
panels[1].set_xscale("log")
panels[1].set_title("across the feed ratio, at that current\n"
                    "still rising where the runs stop: a wall, not a peak", fontsize=9)
panels[1].set_xlabel("feed Mg/Li (mol/mol)")
panels[1].set_ylabel("permselectivity")
panels[1].grid(alpha=0.25)

# --- the whole surface, with the gates taken out of it
mesh_j, mesh_r = np.meshgrid(line, feed_line)
surface = find_predictions(PERMSELECTIVITY, mesh_j, mesh_r)
recovery = find_predictions(LI_RECOVERY, mesh_j, mesh_r)
volts = find_predictions(HIGHEST_VOLTAGE, mesh_j, mesh_r)
refused = (recovery < RECOVERY_FLOOR) | (volts > VOLTAGE_CEILING)

shading = panels[2].contourf(mesh_j, mesh_r, np.where(refused, np.nan, surface),
                             levels=22, cmap="viridis")
figure.colorbar(shading, ax=panels[2], label="predicted permselectivity")
panels[2].contourf(mesh_j, mesh_r, refused.astype(float), levels=[0.5, 1.5], colors=["#dddddd"])
panels[2].scatter(currents, feeds, s=55, color="white", edgecolor="black", zorder=3)
if settings:
    panels[2].scatter([best_current], [best_feed], marker="*", s=460, color="#d62728",
                      edgecolor="white", zorder=5)
panels[2].set_yscale("log")
panels[2].set_title("the whole surface, grey where a gate refuses it\n"
                    "white dots are the runs; the star is the recommendation", fontsize=9)
panels[2].set_xlabel("current density (mA/cm2)")
panels[2].set_ylabel("feed Mg/Li (mol/mol)")

# --- what the two gated outcomes come to along the same curve, so the headroom shows
held = np.full_like(line, best_feed)
for field_name, limit, colour, label, side in (
        (LI_RECOVERY, RECOVERY_FLOOR, "#2ca02c", "recovery %", "floor"),
        (HIGHEST_VOLTAGE, VOLTAGE_CEILING, "#ff7f0e", "volts", "ceiling")):
    drawn = find_predictions(field_name, line, held)
    panels[3].plot(line, drawn, color=colour, linewidth=2.5, label=label)
    panels[3].axhline(limit, color=colour, linestyle="--", linewidth=1.2)
    panels[3].annotate(f"{label} {side} {limit:.0f}", (line[2], limit), fontsize=7.5,
                       color=colour, xytext=(0, 4), textcoords="offset points")

if settings:
    panels[3].axvline(best_current, color="#d62728", linestyle="--", linewidth=1.5)
    for field_name, colour in ((LI_RECOVERY, "#2ca02c"), (HIGHEST_VOLTAGE, "#ff7f0e")):
        panels[3].scatter([best_current], [predicted[field_name]], marker="*", s=300,
                          color=colour, edgecolor="white", zorder=5)
        panels[3].annotate(f"{predicted[field_name]:.1f}", (best_current, predicted[field_name]),
                           fontsize=9, color=colour, fontweight="bold",
                           xytext=(8, -4), textcoords="offset points")

panels[3].scatter(currents[near], [row.li_recovery_pct for row, keep in zip(rows, near) if keep],
                  s=45, color="#2ca02c", alpha=0.45, zorder=3)
panels[3].scatter(currents[near], [row.highest_voltage_v for row, keep in zip(rows, near) if keep],
                  s=45, color="#ff7f0e", alpha=0.45, zorder=3)
panels[3].set_title("what the two gates read along that same curve\n"
                    "the recommendation has to clear both", fontsize=9)
panels[3].set_xlabel("current density (mA/cm2)")
panels[3].set_ylabel("recovery (%) and volts")
panels[3].legend(fontsize=7.5, loc="upper left")
panels[3].grid(alpha=0.25)

figure.tight_layout(rect=(0, 0, 1, 0.90))
figure.savefig("output/best-setup-curve.png", dpi=150)
print("wrote output/best-setup-curve.png")
if settings:
    print(f"  star at {best_current:.2f} mA/cm2, feed {best_feed:.3f} mol/mol, "
          f"permselectivity {best_perm:.3f}")
else:
    print(f"  no star: {models.best_setups[MEMBRANE].find_refusal()}")
