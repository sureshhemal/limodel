"""Make the figures of the made-up examples in docs/plan-for-building-the-model.md.

Ten made-up runs, generated from known equations plus random noise, are put through every step
of the plan. The figures are written into docs/figures/plan (or the folder given as the first
argument), and the numbers the plan's example tables quote are printed as JSON. Nothing here is
real data.

XGBoost (Step 7) is not a project dependency yet, so run it with:

    uv run --with xgboost python scripts/make_plan_example_figures.py
"""

import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from xgboost import XGBRegressor

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "docs" / "figures" / "plan"
OUT.mkdir(parents=True, exist_ok=True)

# --- palette (reference instance, light surface) -------------------------------------------
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
BAND = "#cde2fb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "lines.linewidth": 2, "lines.markersize": 8, "legend.frameon": False,
})


def save(fig, name):
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


# --- the made-up truth, and the made-up runs ------------------------------------------------
def true_p(i, r):
    return 6.0 - 1.6 * math.log(i / 5) ** 2 - 0.9 * math.log(r / 5)


def true_recovery(i, r):
    return (22 + 13 * math.log2(i / 3)) * (r / 5) ** -0.15


def true_voltage(i, r):
    return 5 + 0.62 * i - 0.9 * math.log(r / 5)


TRUE = {"P": true_p, "recovery": true_recovery, "voltage": true_voltage}
NOISE = {"P": 0.25, "recovery": 1.5, "voltage": 0.3}

rng = np.random.default_rng(11)
DESIGN = [("M1", 3, 5), ("M2", 6, 5), ("M3", 6, 5), ("M4", 12, 5), ("M5", 12, 5),
          ("M6", 12, 5), ("M7", 24, 5), ("M8", 12, 10), ("M9", 12, 20), ("M10", 12, 40)]
runs = []
for code, i, r in DESIGN:
    row = {"run": code, "i": i, "R": r}
    for name, f in TRUE.items():
        row[name] = round(f(i, r) + rng.normal(0, NOISE[name]), 2 if name == "P" else 1)
    runs.append(row)

numbers = {"runs": runs}


# --- Step 3: pure error ---------------------------------------------------------------------
def groups_of(rows):
    found = {}
    for row in rows:
        found.setdefault((row["i"], row["R"]), []).append(row)
    return {k: v for k, v in found.items() if len(v) > 1}


def pure_error(rows, name):
    ss, nu = 0.0, 0
    for members in groups_of(rows).values():
        ys = [m[name] for m in members]
        mean = sum(ys) / len(ys)
        ss += sum((y - mean) ** 2 for y in ys)
        nu += len(ys) - 1
    return ss, nu


pe = {}
for name in TRUE:
    ss, nu = pure_error(runs, name)
    s = math.sqrt(ss / nu)
    lo = s * math.sqrt(nu / stats.chi2.ppf(0.975, nu))
    hi = s * math.sqrt(nu / stats.chi2.ppf(0.025, nu))
    mean_all = np.mean([m[name] for g in groups_of(runs).values() for m in g])
    pe[name] = {"ss": ss, "nu": nu, "s": s, "lo": lo, "hi": hi, "relative": s / mean_all}
numbers["pure_error"] = pe
numbers["groups_P"] = {f"{k[0]} mA/cm2, ratio {k[1]}": [(m["run"], m["P"]) for m in v]
                       for k, v in groups_of(runs).items()}


# --- Step 4: coding --------------------------------------------------------------------------
def coder(values):
    lo, hi = min(values), max(values)
    mid, half = (hi + lo) / 2, (hi - lo) / 2
    return mid, half


i_all = np.array([r["i"] for r in runs], float)
lnr_all = np.log(np.array([r["R"] for r in runs], float))
corr_raw = np.corrcoef(i_all, i_all ** 2)[0, 1]
mid_i, half_i = coder(i_all)
xi = (i_all - mid_i) / half_i
corr_coded = np.corrcoef(xi, xi ** 2)[0, 1]
mid_lni, half_lni = coder(np.log(i_all))
mid_lnr, half_lnr = coder(lnr_all)
numbers["coding"] = {"i": [mid_i, half_i], "ln_i": [mid_lni, half_lni], "ln_R": [mid_lnr, half_lnr],
                     "corr_raw": corr_raw, "corr_coded": corr_coded}


def coded(i, r, scale):
    v1 = math.log(i) if scale == "ln i" else i
    m1, h1 = (mid_lni, half_lni) if scale == "ln i" else (mid_i, half_i)
    return (v1 - m1) / h1, (math.log(r) - mid_lnr) / half_lnr


TERMS = {"M0": [], "M1": ["x1"], "M2": ["x1", "x2"], "M3": ["x1", "x2", "x1^2"],
         "M4": ["x1", "x2", "x1^2", "x2^2"]}


def matrix(rows, terms, scale):
    out = []
    for row in rows:
        x1, x2 = coded(row["i"], row["R"], scale)
        cols = {"x1": x1, "x2": x2, "x1^2": x1 ** 2, "x2^2": x2 ** 2}
        out.append([1.0] + [cols[t] for t in terms])
    return np.array(out)


def fit(rows, name, terms, scale):
    X = matrix(rows, terms, scale)
    y = np.array([r[name] for r in rows])
    n, p = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    ss_res = float(e @ e)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    s2 = ss_res / (n - p)
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    loo = e / (1 - h)
    out = {"terms": terms, "scale": scale, "n": n, "p": p, "b": b, "XtX_inv": XtX_inv, "s2": s2,
           "ss_res": ss_res, "e": e, "h": h, "y": y, "loo_pred": y - loo,
           "rmse_loo": float(np.sqrt((loo ** 2).mean())), "mae_loo": float(np.abs(loo).mean()),
           "r2": 1 - ss_res / ss_tot, "r2_adj": 1 - (ss_res / ss_tot) * (n - 1) / (n - p)}
    if p > 1:
        F = ((ss_tot - ss_res) / (p - 1)) / s2
        out["F"], out["F_p"] = F, float(stats.f.sf(F, p - 1, n - p))
    se = np.sqrt(np.diag(XtX_inv) * s2)
    out["se"] = se
    out["t_p"] = [float(2 * stats.t.sf(abs(bj / sj), n - p)) for bj, sj in zip(b, se)]
    ss_pe, nu_pe = pure_error(rows, name)
    n_set = len({(r["i"], r["R"]) for r in rows})
    if n_set - p > 0:
        f_lof = ((ss_res - ss_pe) / (n_set - p)) / (ss_pe / nu_pe)
        out["lof_F"], out["lof_p"] = f_lof, float(stats.f.sf(f_lof, n_set - p, nu_pe))
    out["cook"] = (e ** 2 / (p * s2)) * h / (1 - h) ** 2
    return out


def ladder(rows, name, scale):
    fits, prev = {}, None
    for label, terms in TERMS.items():
        f = fit(rows, name, terms, scale)
        if prev is not None:
            Fp = ((prev["ss_res"] - f["ss_res"]) / (f["p"] - prev["p"])) / (f["ss_res"] / (f["n"] - f["p"]))
            f["partial_F"], f["partial_p"] = Fp, float(stats.f.sf(Fp, f["p"] - prev["p"], f["n"] - f["p"]))
        fits[label], prev = f, f
    return fits


def choose(fits, s_pe):
    ok = [k for k, f in fits.items()
          if all(pv < 0.05 for pv in f["t_p"][1:]) and f.get("lof_p", 1) >= 0.05 and f["p"] <= f["n"] - 2]
    if not ok:
        return "M0"
    best = min(ok, key=lambda k: fits[k]["rmse_loo"])
    close = [k for k in ok if fits[k]["rmse_loo"] - fits[best]["rmse_loo"] <= s_pe]
    return min(close, key=lambda k: fits[k]["p"])


chosen, all_ladders = {}, {}
for name in TRUE:
    best = None
    for scale in ("i", "ln i"):
        fits = ladder(runs, name, scale)
        all_ladders[(name, scale)] = fits
        label = choose(fits, pe[name]["s"])
        cand = fits[label]
        if best is None or cand["rmse_loo"] < best[2]["rmse_loo"]:
            best = (scale, label, cand)
    chosen[name] = best

numbers["chosen"] = {n: {"scale": s, "model": m, "b": [round(v, 3) for v in f["b"]],
                         "se": [round(v, 3) for v in f["se"]], "p": [round(v, 4) for v in f["t_p"]],
                         "rmse_loo": f["rmse_loo"], "mae_loo": f["mae_loo"]}
                     for n, (s, m, f) in chosen.items()}
p_scale = chosen["P"][0]
numbers["ladder_P"] = {k: {"p": f["p"], "R2": f["r2"], "R2_adj": f["r2_adj"], "F": f.get("F"),
                           "F_p": f.get("F_p"), "partial_F": f.get("partial_F"),
                           "partial_p": f.get("partial_p"), "rmse_loo": f["rmse_loo"],
                           "mae_loo": f["mae_loo"], "lof_F": f.get("lof_F"), "lof_p": f.get("lof_p"),
                           "t_p": f["t_p"]}
                       for k, f in all_ladders[("P", p_scale)].items()}
numbers["ladder_P_other_scale_best_rmse"] = min(
    f["rmse_loo"] for f in all_ladders[("P", "i" if p_scale == "ln i" else "ln i")].values())


def predict(name, i, r):
    scale, _, f = chosen[name]
    x0 = matrix([{"i": i, "R": r}], f["terms"], scale)[0]
    y0 = float(x0 @ f["b"])
    half = stats.t.ppf(0.975, f["n"] - f["p"]) * math.sqrt(f["s2"] * (1 + x0 @ f["XtX_inv"] @ x0))
    return y0, half


# --- Step 6: diagnostics of the chosen P model ------------------------------------------------
fP = chosen["P"][2]
numbers["diagnostics_P"] = {"leverage_limit": 2 * fP["p"] / fP["n"], "cook_limit": 4 / fP["n"],
                            "rows": [(r["run"], round(float(h), 3), round(float(c), 3))
                                     for r, h, c in zip(runs, fP["h"], fP["cook"])]}
std_res = fP["e"] / np.sqrt(fP["s2"] * (1 - fP["h"]))
order = np.argsort(std_res)
ranks = np.empty(len(runs), int); ranks[order] = np.arange(1, len(runs) + 1)
z_expected = stats.norm.ppf((ranks - 0.5) / len(runs))
numbers["diagnostics_P"]["std_res"] = [(r["run"], round(float(v), 2), int(k), round(float(z), 2))
                                       for r, v, k, z in zip(runs, std_res, ranks, z_expected)]
numbers["diagnostics_P"]["shapiro_p"] = float(stats.shapiro(fP["e"]).pvalue)
refits = {}
for drop in ("M1", "M7", "M10"):
    kept = [r for r in runs if r["run"] != drop]
    X = matrix(kept, fP["terms"], p_scale)
    y = np.array([r["P"] for r in kept])
    b_wo = np.linalg.lstsq(X, y, rcond=None)[0]
    refits[drop] = {"b_without": [round(float(v), 3) for v in b_wo],
                    "shift_in_se": [round(float((bb - bw) / se), 2) for bb, bw, se in zip(fP["b"], b_wo, fP["se"])]}
numbers["diagnostics_P"]["refits"] = refits

# --- Step 7: flexible model, leave-one-out ---------------------------------------------------
Xraw = np.array([[r["i"], r["R"]] for r in runs], float)
yP = np.array([r["P"] for r in runs])


def trees():
    return XGBRegressor(n_estimators=100, max_depth=2, random_state=0)


tree_pred = []
for k in range(len(runs)):
    keep = [j for j in range(len(runs)) if j != k]
    tree_pred.append(float(trees().fit(Xraw[keep], yP[keep]).predict(Xraw[[k]])[0]))
tree_pred = np.array(tree_pred)
ss_tot_P = float(((yP - yP.mean()) ** 2).sum())
poly_loo = fP["y"] - fP["loo_pred"]
numbers["flexible_P"] = {"rmse_loo": float(np.sqrt(((yP - tree_pred) ** 2).mean())),
                         "mae_loo": float(np.abs(yP - tree_pred).mean()),
                         "q2": 1 - float(((yP - tree_pred) ** 2).sum()) / ss_tot_P,
                         "poly_q2": 1 - float((poly_loo ** 2).sum()) / ss_tot_P,
                         "loo": [(r["run"], round(float(t), 2), round(float(q), 2), r["P"])
                                 for r, t, q in zip(runs, tree_pred, fP["loo_pred"])]}
tree_all = trees().fit(Xraw, yP)
step7_i = np.round(np.arange(2.0, 30.0001, 0.1), 1)
step7_tree = tree_all.predict(np.column_stack([step7_i, np.full_like(step7_i, 5.0)]))

# --- Step 8: best setting under the gates ------------------------------------------------------
grid = np.round(np.arange(3.0, 24.0001, 0.1), 1)
recommend = {}
curves = {}
for r in (5, 10, 20, 40):
    pts = []
    for i in grid:
        P, Ph = predict("P", i, r)
        rec, rech = predict("recovery", i, r)
        U, Uh = predict("voltage", i, r)
        pts.append((i, P, Ph, rec, rech, U, Uh))
    curves[r] = pts
    point = [p for p in pts if p[3] >= 35 and p[5] <= 20]
    cautious = [p for p in pts if p[3] - p[4] >= 35 and p[5] + p[6] <= 20]
    best_point = max(point, key=lambda p: p[1]) if point else None
    best_caut = max(cautious, key=lambda p: p[1]) if cautious else None
    recommend[r] = {"point": best_point and [round(v, 2) for v in best_point],
                    "cautious": best_caut and [round(v, 2) for v in best_caut]}
numbers["recommend"] = recommend
near_best = {}
for r, pts in curves.items():
    passing = [p for p in pts if p[3] >= 35 and p[5] <= 20]
    if passing:
        top = max(q[1] for q in passing)
        close = [q[0] for q in passing if q[1] >= top - pe["P"]["s"]]
        near_best[r] = (min(close), max(close))
numbers["near_best"] = near_best
fP_t = stats.t.ppf(0.975, fP["n"] - fP["p"])
numbers["interval_parts_P"] = {"t": fP_t, "s": math.sqrt(fP["s2"]), "n": fP["n"], "p": fP["p"]}

# --- Step 9: runs predicted before their results -----------------------------------------------
NEW = [("N1", 12, 5), ("N2", 8, 10), ("N3", 6, 20), ("N4", 12, 60)]
new_rows = []
for code, i, r in NEW:
    P, Ph = predict("P", i, r)
    measured = round(true_p(i, r) + rng.normal(0, NOISE["P"]), 2)
    new_rows.append({"run": code, "i": i, "R": r, "pred": round(P, 2), "half": round(Ph, 2),
                     "measured": measured, "inside": abs(measured - P) <= Ph,
                     "outside_range": not (5 <= r <= 40)})
numbers["new_runs"] = new_rows
inside_range = [r for r in new_rows if not r["outside_range"]]
numbers["new_rmse_in_range"] = math.sqrt(sum((r["measured"] - r["pred"]) ** 2 for r in inside_range) / len(inside_range))
numbers["binomial_misses"] = {n_new: [float(stats.binom.sf(n_miss - 1, n_new, 0.05)) for n_miss in range(n_new + 1)]
                              for n_new in (1, 3, 4, 10)}

# ================================ figures ==================================================
# Step 2a: the design
fig, ax = plt.subplots(figsize=(5.6, 3.8))
counts = {}
for r in runs:
    counts[(r["i"], r["R"])] = counts.get((r["i"], r["R"]), 0) + 1
for (i, r), c in counts.items():
    ax.scatter(i, r, s=60 + 50 * (c - 1), color=BLUE, zorder=3, edgecolor=SURFACE, linewidth=2)
    if c > 1:
        ax.annotate(f"×{c}", (i, r), textcoords="offset points", xytext=(9, 6), color=INK_2)
ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
ax.set_xticks([3, 6, 12, 24]); ax.set_xticklabels(["3", "6", "12", "24"])
ax.set_yticks([5, 10, 20, 40]); ax.set_yticklabels(["5", "10", "20", "40"])
ax.set_xlabel("current density, mA/cm²"); ax.set_ylabel("Mg/Li ratio (mass)")
ax.set_title("The design: a cross around the base run (made-up runs)")
ax.annotate("base run", (12, 5), textcoords="offset points", xytext=(10, -14), color=INK_2)
save(fig, "step2-design.png")

# Step 2b: shapes of P
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), sharey=True)
arm_i = [r for r in runs if r["R"] == 5]
arm_r = [r for r in runs if r["i"] == 12]
axes[0].scatter([r["i"] for r in arm_i], [r["P"] for r in arm_i], color=BLUE, zorder=3)
axes[0].set_xlabel("current density, mA/cm² (ratio 5)"); axes[0].set_ylabel("P")
axes[0].set_title("P against current density")
axes[1].scatter([r["R"] for r in arm_r], [r["P"] for r in arm_r], color=BLUE, zorder=3)
axes[1].set_xlabel("Mg/Li ratio R (12 mA/cm²)"); axes[1].set_title("P against R")
axes[2].scatter([math.log(r["R"]) for r in arm_r], [r["P"] for r in arm_r], color=BLUE, zorder=3)
axes[2].set_xlabel("ln R (12 mA/cm²)"); axes[2].set_title("P against ln R")
fig.suptitle("Each output against each input (made-up runs)", fontweight="bold", y=1.04)
save(fig, "step2-shapes.png")

# Step 3: repeat groups
fig, ax = plt.subplots(figsize=(5.6, 3.4))
for k, (key, members) in enumerate(groups_of(runs).items()):
    ys = [m["P"] for m in members]
    ax.scatter([k] * len(ys), ys, color=BLUE, zorder=3)
    for n_m, m in enumerate(sorted(members, key=lambda m: m["P"])):
        side = 1 if n_m % 2 == 0 else -1
        ax.annotate(m["run"], (k, m["P"]), textcoords="offset points", xytext=(10 * side, -3),
                    ha="left" if side > 0 else "right", color=INK_2)
    ax.hlines(np.mean(ys), k - 0.18, k + 0.18, color=INK, linewidth=2)
ax.set_xticks(range(len(groups_of(runs))))
ax.set_xticklabels([f"{i} mA/cm², ratio {r}" for i, r in groups_of(runs)])
ax.set_xlim(-0.6, len(groups_of(runs)) - 0.4)
ax.set_ylabel("P"); ax.grid(axis="x", visible=False)
ax.set_title("Repeat runs and their group averages (made-up runs)")
save(fig, "step3-repeats.png")

# Step 4: overlap before and after coding
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
axes[0].scatter(i_all, i_all ** 2, color=BLUE, zorder=3)
axes[0].set_xlabel("i"); axes[0].set_ylabel("i²")
axes[0].set_title(f"Raw: correlation {corr_raw:.2f}")
axes[1].scatter(xi, xi ** 2, color=BLUE, zorder=3)
axes[1].set_xlabel("coded x"); axes[1].set_ylabel("x²")
axes[1].set_title(f"Coded: correlation {corr_coded:.2f}")
fig.suptitle("An input and its square, before and after coding (made-up runs)", fontweight="bold", y=1.04)
save(fig, "step4-coding.png")

# Step 5: leave-one-out error up the ladder
lad = all_ladders[("P", p_scale)]
fig, ax = plt.subplots(figsize=(5.6, 3.4))
labels = list(lad)
vals = [lad[k]["rmse_loo"] for k in labels]
bars = ax.bar(labels, vals, color=BLUE, width=0.6)
for b, v in zip(bars, vals):
    ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v), textcoords="offset points",
                xytext=(0, 4), ha="center", color=INK_2)
ax.axhline(pe["P"]["s"], color=INK, linestyle="--", linewidth=1.5)
ax.annotate(f"pure error\n{pe['P']['s']:.2f}", xy=(1.0, pe["P"]["s"]), xycoords=("axes fraction", "data"),
            textcoords="offset points", xytext=(6, 0), ha="left", va="center", color=INK)
ax.set_ylabel("leave-one-out RMSE of P"); ax.grid(axis="x", visible=False)
ax.set_title(f"P: prediction error up the ladder, x₁ from {p_scale} (made-up runs)")
save(fig, "step5-ladder.png")

# Step 6: diagnostics
fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.4))
ax = axes[0, 0]
lo = min(fP["y"].min(), fP["loo_pred"].min()) - 0.3
hi = max(fP["y"].max(), fP["loo_pred"].max()) + 0.3
band = 2 * pe["P"]["s"]
xx = np.array([lo, hi])
ax.fill_between(xx, xx - band, xx + band, color=BAND, linewidth=0)
ax.plot(xx, xx, color=INK_2, linewidth=1)
ax.scatter(fP["loo_pred"], fP["y"], color=BLUE, zorder=3)
ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
ax.set_xlabel("predicted P, run left out"); ax.set_ylabel("measured P")
ax.set_title("Parity (band: ±2 pure errors)")
ax = axes[0, 1]
ax.axhspan(-2, 2, color=BAND, linewidth=0)
ax.axhline(0, color=INK_2, linewidth=1)
ax.scatter(fP["y"] - fP["e"], std_res, color=BLUE, zorder=3)
ax.set_ylim(-3, 3)
ax.set_xlabel("fitted P"); ax.set_ylabel("standardised residual"); ax.set_title("Residuals (band: ±2)")
ax = axes[1, 0]
zz = np.array([-2.0, 2.0])
ax.plot(zz, zz, color=INK_2, linewidth=1)
ax.scatter(z_expected, std_res, color=BLUE, zorder=3)
ax.set_xlabel("expected if normal"); ax.set_ylabel("standardised residual"); ax.set_title("Normal Q–Q")
ax = axes[1, 1]
ax.bar([r["run"] for r in runs], fP["cook"], color=BLUE, width=0.6)
ax.axhline(4 / fP["n"], color=INK, linestyle="--", linewidth=1.5)
ax.annotate("4/n", (-0.4, 4 / fP["n"]), textcoords="offset points", xytext=(0, 4), ha="left", color=INK)
ax.set_ylabel("Cook's distance"); ax.set_title("Influence of each run")
ax.tick_params(axis="x", labelsize=8); ax.grid(axis="x", visible=False)
fig.suptitle("Checking the chosen model for P (made-up runs)", fontweight="bold", y=1.0)
fig.tight_layout()
save(fig, "step6-checks.png")

# Step 7: polynomial against flexible model
step7_poly = np.array([predict("P", i, 5)[0] for i in step7_i])
fig, axes = plt.subplots(1, 2, figsize=(11.0, 3.6), gridspec_kw={"width_ratios": [1, 1.5]})
ax = axes[0]
names = ["polynomial", "boosted trees"]
vals = [chosen["P"][2]["rmse_loo"], numbers["flexible_P"]["rmse_loo"]]
bars = ax.bar(names, vals, color=BLUE, width=0.5)
for bb, v in zip(bars, vals):
    ax.annotate(f"{v:.2f}", (bb.get_x() + bb.get_width() / 2, v), textcoords="offset points",
                xytext=(0, 4), ha="center", color=INK_2)
ax.axhline(pe["P"]["s"], color=INK, linestyle="--", linewidth=1.5)
ax.annotate(f"pure error\n{pe['P']['s']:.2f}", xy=(1.0, pe["P"]["s"]), xycoords=("axes fraction", "data"),
            textcoords="offset points", xytext=(6, 0), ha="left", va="center", color=INK)
ax.set_ylabel("leave-one-out RMSE of P"); ax.grid(axis="x", visible=False)
ax.set_title("Prediction error on unseen runs")
ax = axes[1]
ax.axvspan(3, 24, color=BAND, linewidth=0, alpha=0.6)
ax.plot(step7_i, step7_poly, color=BLUE, label="polynomial (M3)")
ax.plot(step7_i, step7_tree, color=ORANGE, label="boosted trees", drawstyle="steps-mid")
step7_runs = [r for r in runs if r["R"] == 5]
ax.scatter([r["i"] for r in step7_runs], [r["P"] for r in step7_runs], color=INK, zorder=4, s=36, label="runs at ratio 5")
ax.set_xlabel("current density, mA/cm² (shaded: tested range)"); ax.set_ylabel("predicted P, ratio 5")
ax.set_title("Both models fitted to all ten runs")
ax.legend(loc="lower left")
fig.suptitle("P: polynomial against a flexible model (made-up runs)", fontweight="bold", y=1.03)
fig.tight_layout()
save(fig, "step7-comparison.png")

# Step 8: best setting under the gates
fig, ax = plt.subplots(figsize=(7.4, 4.0))
colors = {5: BLUE, 10: ORANGE, 20: AQUA, 40: YELLOW}
for r, pts in curves.items():
    i = np.array([p[0] for p in pts]); P = np.array([p[1] for p in pts])
    allowed = np.array([p[3] >= 35 and p[5] <= 20 for p in pts])
    ax.plot(i, np.where(allowed, np.nan, P), color=colors[r], linewidth=1.2, alpha=0.45, linestyle=(0, (3, 2)))
    ax.plot(i, np.where(allowed, P, np.nan), color=colors[r], label=f"ratio {r}")
    best = recommend[r]["point"]
    if best:
        ax.scatter(best[0], best[1], color=colors[r], zorder=4, edgecolor=SURFACE, linewidth=2, s=70)
        ax.annotate(f"{best[0]:.1f}", (best[0], best[1]), textcoords="offset points", xytext=(6, 6),
                    color=INK)
ax.set_xlabel("current density, mA/cm²"); ax.set_ylabel("predicted P")
ax.set_title("Best allowed current density per ratio (made-up runs)")
ax.legend(loc="upper right", title="solid: passes both gates\ndashed: fails one", title_fontsize=8)
save(fig, "step8-best-setting.png")

# Step 9: predictions made before the results
fig, ax = plt.subplots(figsize=(6.0, 3.4))
xs = np.arange(len(new_rows))
ax.errorbar(xs - 0.08, [r["pred"] for r in new_rows], yerr=[r["half"] for r in new_rows], fmt="o",
            color=BLUE, capsize=5, linewidth=2, label="predicted, with 95 % interval")
ax.scatter(xs + 0.08, [r["measured"] for r in new_rows], color=ORANGE, marker="D", zorder=4,
           label="measured later")
ax.set_xticks(xs)
ax.set_xticklabels([f"{r['run']}\n{r['i']} mA/cm², ratio {r['R']}" for r in new_rows], fontsize=8)
ax.set_ylabel("P"); ax.grid(axis="x", visible=False)
ax.legend(loc="lower left")
for k, r in enumerate(new_rows):
    if r["outside_range"]:
        ax.annotate("outside the\nfitted ratios", (k, r["pred"] + r["half"]), textcoords="offset points",
                    xytext=(0, 6), ha="center", color=INK_2, fontsize=8)
ax.set_ylim(0, None)
ax.set_title("Predictions written down before the results (made-up runs)")
save(fig, "step9-unseen.png")

print(json.dumps(numbers, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
