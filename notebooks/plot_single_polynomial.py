"""One polynomial over every run, as docs/polynomial.md writes it, and where its maximum sits."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from limodel.analyzer.calculate.calculator import Calculator
from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.preprocessor import Preprocessor
from limodel.data_loader import DataLoader

COLOURS = {"GO-10": "#1f77b4", "Pristine": "#d62728",
           "PDA/PEI/15CE/BT": "#2ca02c", "PDA-GO10/PEI/BT": "#9467bd"}

journal = Journal()
results = Calculator(journal).find_results(Preprocessor(journal).run(DataLoader().load()))
J = np.array([r.current_density_ma_cm2 for r in results])
R = np.array([r.feed_mg_li_ratio for r in results])
y = np.array([r.li_recovery_pct for r in results])
codes = [r.run_code for r in results]
cems = [r.cem for r in results]

X = np.column_stack([np.ones_like(J), J, R, J**2, R**2])
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
fitted = X @ beta
r2 = 1 - ((y - fitted)**2).sum() / ((y - y.mean())**2).sum()

loo = []
for at in range(len(y)):
    keep = np.arange(len(y)) != at
    without, *_ = np.linalg.lstsq(X[keep], y[keep], rcond=None)
    loo.append(y[at] - X[at] @ without)
loo_rmse = float(np.sqrt(np.mean(np.square(loo))))

grid_j, grid_r = np.linspace(J.min(), J.max(), 300), np.linspace(R.min(), R.max(), 300)
mesh_j, mesh_r = np.meshgrid(grid_j, grid_r)
surface = beta[0] + beta[1]*mesh_j + beta[2]*mesh_r + beta[3]*mesh_j**2 + beta[4]*mesh_r**2
peak = np.unravel_index(np.argmax(surface), surface.shape)

figure, panels = plt.subplots(1, 3, figsize=(17, 5.4))
equation = (f"recovery = {beta[0]:+.4g} {beta[1]:+.4g}J {beta[2]:+.4g}R "
            f"{beta[3]:+.4g}J² {beta[4]:+.4g}R²")
figure.suptitle(f"{equation}\nR² = {r2:.3f}   leave-one-out rmse = {loo_rmse:.2f}   "
                f"spread of the runs themselves = {y.std(ddof=1):.2f}", fontsize=11)

shading = panels[0].contourf(mesh_j, mesh_r, surface, levels=24, cmap="viridis")
figure.colorbar(shading, ax=panels[0], label="predicted recovery (%)")
panels[0].contour(mesh_j, mesh_r, surface, levels=[35], colors="white", linewidths=2)
for x, r, cem, code in zip(J, R, cems, codes):
    panels[0].scatter(x, r, color=COLOURS.get(cem, "#777"), s=70, edgecolor="white", zorder=3)
    panels[0].annotate(code, (x, r), fontsize=7, color="white",
                       xytext=(5, 4), textcoords="offset points")
panels[0].scatter(mesh_j[peak], mesh_r[peak], marker="*", s=420, color="white",
                  edgecolor="black", zorder=4)
panels[0].set_title(f"the surface, peak {surface[peak]:.1f}% at J={mesh_j[peak]:.1f}, R={mesh_r[peak]:.2f}",
                    fontsize=9.5)
panels[0].set_xlabel("current density (mA/cm2)")
panels[0].set_ylabel("feed Mg/Li (mol/mol)")

for x, value, cem, code in zip(fitted, y, cems, codes):
    panels[1].scatter(x, value, color=COLOURS.get(cem, "#777"), s=70, edgecolor="white", zorder=3)
    panels[1].annotate(code, (x, value), fontsize=7, xytext=(4, 4), textcoords="offset points")
limits = [0, max(y.max(), fitted.max()) * 1.1]
panels[1].plot(limits, limits, color="#888888", linestyle="--")
panels[1].set_xlim(limits)
panels[1].set_ylim(limits)
panels[1].set_title("what it predicts against what was measured", fontsize=9.5)
panels[1].set_xlabel("predicted recovery (%)")
panels[1].set_ylabel("measured recovery (%)")
panels[1].grid(alpha=0.25)

order = np.argsort(R)
for at in order:
    panels[2].scatter(R[at], y[at] - fitted[at], color=COLOURS.get(cems[at], "#777"),
                      s=70, edgecolor="white", zorder=3)
    panels[2].annotate(codes[at], (R[at], y[at] - fitted[at]), fontsize=7,
                       xytext=(4, 4), textcoords="offset points")
panels[2].axhline(0, color="#888888", linestyle="--")
panels[2].set_xscale("log")
panels[2].set_title("what it misses by, against the feed ratio", fontsize=9.5)
panels[2].set_xlabel("feed Mg/Li (mol/mol)")
panels[2].set_ylabel("measured minus predicted (%)")
panels[2].grid(alpha=0.25)

handles = [plt.Line2D([], [], marker="o", linestyle="", color=colour, label=cem)
           for cem, colour in COLOURS.items()]
panels[2].legend(handles=handles, fontsize=7.5, loc="lower left")

figure.tight_layout(rect=(0, 0, 1, 0.9))
figure.savefig("output/single-polynomial.png", dpi=150)
print("wrote output/single-polynomial.png")
