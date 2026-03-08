"""
NFL Combine Physical Measurements → Draft Status Analysis
- Combine data: combine_official.csv (2006-2026)
- Draft data: nflverse draft_picks (2006-2024)
- For each position group: visualize how height/weight/arm_length/hand_size
  differ between drafted and undrafted players.
"""

import urllib.request
import io
import csv
import re
import unicodedata
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

# ── Palette ──────────────────────────────────────────────────────────────────
DRAFTED_COLOR   = "#2196F3"   # blue
UNDRAFTED_COLOR = "#FF5722"   # orange-red

# ── 1. Load combine data ──────────────────────────────────────────────────────
print("Loading combine data...")
combine = pd.read_csv("combine_official.csv")
combine["year"] = combine["year"].astype(int)

PHYSICAL = ["height", "weight", "arm_length", "hand_size"]
combine[PHYSICAL] = combine[PHYSICAL].apply(pd.to_numeric, errors="coerce")

# ── 2. Download draft picks ────────────────────────────────────────────────────
print("Downloading draft picks from nflverse...")
DRAFT_URL = "https://github.com/nflverse/nfldata/raw/master/data/draft_picks.csv"
raw = urllib.request.urlopen(DRAFT_URL).read().decode("utf-8")
draft = pd.read_csv(io.StringIO(raw))
draft = draft[draft["season"].astype(int) >= 2006].copy()
draft["season"] = draft["season"].astype(int)

# ── 3. Name normalisation for fuzzy matching ───────────────────────────────────
def norm_name(s: str) -> str:
    """Lowercase, remove accents, strip punctuation/spaces."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z ]", "", s.lower())
    return " ".join(s.split())

combine["name_key"] = combine["player"].apply(norm_name)
draft["name_key"]   = draft["pfr_name"].apply(norm_name)

# Build lookup set: (season, name_key) for all drafted players
drafted_set = set(zip(draft["season"], draft["name_key"]))

def is_drafted(row):
    return (row["year"], row["name_key"]) in drafted_set

combine["drafted"] = combine.apply(is_drafted, axis=1)

# Only keep 2006-2024 (draft data available)
combine_known = combine[combine["year"] <= 2024].copy()

drafted_pct = combine_known["drafted"].mean() * 100
print(f"Match rate: {drafted_pct:.1f}% drafted ({combine_known['drafted'].sum()} / {len(combine_known)})")

# ── 4. Position groups ────────────────────────────────────────────────────────
# Use broad position groups for enough sample size
POS_MAP = {
    "QB":  ["QB"],
    "RB":  ["RB", "FB"],
    "WR":  ["WR"],
    "TE":  ["TE"],
    "OL":  ["OT", "OG", "C", "OL", "G", "T"],
    "DL":  ["DE", "DT", "NT", "DL", "EDGE", "IDL"],
    "LB":  ["LB", "ILB", "OLB", "MLB"],
    "DB":  ["CB", "S", "FS", "SS", "DB"],
    "K/P": ["K", "P", "LS"],
}

def map_pos(pos):
    if not isinstance(pos, str):
        return "Other"
    pos = pos.upper().strip()
    for group, aliases in POS_MAP.items():
        if pos in aliases:
            return group
    return "Other"

combine_known["pos_group"] = combine_known["position"].apply(map_pos)
main_groups = [g for g in POS_MAP if g != "K/P"]  # exclude small special teams

# ── 5. Helper: violin + strip plot ────────────────────────────────────────────
FEAT_LABELS = {
    "height":     "Height (inches)",
    "weight":     "Weight (lbs)",
    "arm_length": "Arm Length (inches)",
    "hand_size":  "Hand Size (inches)",
}

def violin_strip(ax, data, feature, title):
    sub = data[["drafted", feature]].dropna()
    if len(sub) < 10:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                transform=ax.transAxes, fontsize=9, color="grey")
        ax.set_title(title, fontsize=9, fontweight="bold")
        return

    sub["Status"] = sub["drafted"].map({True: "Drafted", False: "Undrafted"})
    palette = {"Drafted": DRAFTED_COLOR, "Undrafted": UNDRAFTED_COLOR}

    sns.violinplot(
        data=sub, x="Status", y=feature, ax=ax,
        palette=palette, inner="quartile", linewidth=0.8,
        order=["Drafted", "Undrafted"],
    )
    # medians
    for i, status in enumerate(["Drafted", "Undrafted"]):
        med = sub[sub["Status"] == status][feature].median()
        ax.text(i, med, f" {med:.2f}", va="center", ha="left",
                fontsize=7, color="white", fontweight="bold")

    ax.set_title(title, fontsize=9, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel(FEAT_LABELS.get(feature, feature), fontsize=8)
    ax.tick_params(axis="both", labelsize=7)

# ── 6. Figure A: 4×8 grid of violin plots (position × feature) ───────────────
print("Creating Figure A: violin plots by position × feature...")

features_plot = ["height", "weight", "arm_length", "hand_size"]
n_pos = len(main_groups)
n_feat = len(features_plot)

fig_a, axes_a = plt.subplots(
    n_pos, n_feat,
    figsize=(5 * n_feat, 3.5 * n_pos),
    constrained_layout=True,
)
fig_a.suptitle(
    "NFL Combine: Physical Measurements vs Draft Status (2006–2024)\n"
    "Blue = Drafted | Orange = Undrafted",
    fontsize=14, fontweight="bold", y=1.01,
)

for r, pos in enumerate(main_groups):
    sub_pos = combine_known[combine_known["pos_group"] == pos]
    n_d = sub_pos["drafted"].sum()
    n_u = (~sub_pos["drafted"]).sum()
    for c, feat in enumerate(features_plot):
        ax = axes_a[r, c]
        violin_strip(ax, sub_pos, feat, f"{pos}  (n={n_d}✓, {n_u}✗)")

# row labels on right
for r, pos in enumerate(main_groups):
    axes_a[r, 0].set_ylabel(f"{pos}\n{FEAT_LABELS[features_plot[0]]}", fontsize=8)

# column headers
for c, feat in enumerate(features_plot):
    axes_a[0, c].set_title(
        FEAT_LABELS[feat] + f"\n{axes_a[0, c].get_title()}",
        fontsize=9, fontweight="bold",
    )

fig_a.savefig("fig_A_violins.png", dpi=150, bbox_inches="tight")
plt.close(fig_a)
print("  → fig_A_violins.png")

# ── 7. Figure B: Logistic Regression feature importance per position ───────────
print("Creating Figure B: logistic regression coefficients...")

results = []  # (pos_group, feature, coef, n_total)

for pos in main_groups:
    sub = combine_known[combine_known["pos_group"] == pos][features_plot + ["drafted"]].dropna()
    if len(sub) < 50 or sub["drafted"].nunique() < 2:
        continue

    X = sub[features_plot].values
    y = sub["drafted"].values.astype(int)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs")),
    ])
    pipe.fit(X, y)
    coefs = pipe.named_steps["lr"].coef_[0]

    # Bootstrap 95% CI
    ci_lo, ci_hi = [], []
    for _ in range(300):
        Xi, yi = resample(X, y, random_state=None)
        if yi.sum() == 0 or yi.sum() == len(yi):
            ci_lo.append(np.nan); ci_hi.append(np.nan)
            continue
        pipe2 = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=500, class_weight="balanced", solver="lbfgs")),
        ])
        pipe2.fit(Xi, yi)
        ci_lo.append(pipe2.named_steps["lr"].coef_[0])
        ci_hi.append(pipe2.named_steps["lr"].coef_[0])
    ci_lo = np.nanpercentile(ci_lo, 2.5, axis=0)
    ci_hi = np.nanpercentile(ci_hi, 97.5, axis=0)

    for i, feat in enumerate(features_plot):
        results.append({
            "pos_group": pos,
            "feature":   feat,
            "coef":      coefs[i],
            "ci_lo":     ci_lo[i],
            "ci_hi":     ci_hi[i],
            "n":         len(sub),
        })

res_df = pd.DataFrame(results)

fig_b, axes_b = plt.subplots(
    1, n_feat,
    figsize=(4.5 * n_feat, 6),
    constrained_layout=True,
)
fig_b.suptitle(
    "Logistic Regression: Effect of Physical Measurements on Draft Probability\n"
    "(Standardized coefficients, 95% bootstrap CI — positive = more likely drafted)",
    fontsize=13, fontweight="bold",
)

for c, feat in enumerate(features_plot):
    ax = axes_b[c]
    sub_r = res_df[res_df["feature"] == feat].sort_values("coef")

    colors = [DRAFTED_COLOR if v > 0 else UNDRAFTED_COLOR for v in sub_r["coef"]]
    bars = ax.barh(sub_r["pos_group"], sub_r["coef"], color=colors, alpha=0.85, zorder=3)

    # 95% CI whiskers (use numeric index for y position)
    pos_list = list(sub_r["pos_group"])
    for i, (_, row) in enumerate(sub_r.iterrows()):
        ax.plot(
            [row["ci_lo"], row["ci_hi"]],
            [i, i],
            color="black", linewidth=1.5, zorder=4,
        )
        ax.plot(
            [row["ci_lo"], row["ci_lo"]],
            [i - 0.15, i + 0.15],
            color="black", linewidth=1.5, zorder=4,
        )
        ax.plot(
            [row["ci_hi"], row["ci_hi"]],
            [i - 0.15, i + 0.15],
            color="black", linewidth=1.5, zorder=4,
        )

    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(FEAT_LABELS[feat], fontsize=10, fontweight="bold")
    ax.set_xlabel("Standardized coefficient", fontsize=9)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="x", alpha=0.3, zorder=1)

fig_b.savefig("fig_B_coefficients.png", dpi=150, bbox_inches="tight")
plt.close(fig_b)
print("  → fig_B_coefficients.png")

# ── 8. Figure C: Median difference heatmap ────────────────────────────────────
print("Creating Figure C: median difference heatmap...")

FEAT_LABELS_SHORT = {
    "height":     "Height",
    "weight":     "Weight",
    "arm_length": "Arm\nLength",
    "hand_size":  "Hand\nSize",
}

records = []
for pos in main_groups:
    sub = combine_known[combine_known["pos_group"] == pos]
    row = {"pos_group": pos}
    for feat in features_plot:
        d = sub[sub["drafted"] == True][feat].dropna()
        u = sub[sub["drafted"] == False][feat].dropna()
        if len(d) > 5 and len(u) > 5:
            row[feat] = d.median() - u.median()
        else:
            row[feat] = np.nan
    records.append(row)

heat_df = pd.DataFrame(records).set_index("pos_group")[features_plot]
heat_df.columns = [FEAT_LABELS_SHORT[f] for f in features_plot]

fig_c, ax_c = plt.subplots(figsize=(6, 5.5), constrained_layout=True)
cmap = sns.diverging_palette(15, 220, as_cmap=True)
sns.heatmap(
    heat_df, ax=ax_c, cmap=cmap, center=0, annot=True, fmt=".2f",
    linewidths=0.5, cbar_kws={"label": "Median (Drafted) − Median (Undrafted)"},
    annot_kws={"fontsize": 9},
)
ax_c.set_title(
    "Physical Advantage of Drafted vs Undrafted Players\n"
    "(Positive = drafted players are larger/longer)",
    fontsize=11, fontweight="bold",
)
ax_c.set_xlabel("Measurement", fontsize=10)
ax_c.set_ylabel("Position Group", fontsize=10)
ax_c.tick_params(axis="both", labelsize=9)

fig_c.savefig("fig_C_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig_c)
print("  → fig_C_heatmap.png")

# ── 9. Figure D: Sample size summary table ────────────────────────────────────
print("Creating Figure D: sample size & draft rate table...")

summary = []
for pos in main_groups:
    sub = combine_known[combine_known["pos_group"] == pos]
    n_total  = len(sub)
    n_draft  = sub["drafted"].sum()
    draft_rt = n_draft / n_total * 100 if n_total > 0 else 0
    avail_pct = sub[features_plot].notna().mean() * 100
    summary.append({
        "Position": pos,
        "Total in Combine": n_total,
        "Drafted": int(n_draft),
        "Draft Rate (%)": f"{draft_rt:.1f}",
        "Height avail.": f"{avail_pct['height']:.0f}%",
        "Weight avail.": f"{avail_pct['weight']:.0f}%",
        "Arm avail.":    f"{avail_pct['arm_length']:.0f}%",
        "Hand avail.":   f"{avail_pct['hand_size']:.0f}%",
    })

sum_df = pd.DataFrame(summary)
fig_d, ax_d = plt.subplots(figsize=(10, 3), constrained_layout=True)
ax_d.axis("off")
tbl = ax_d.table(
    cellText=sum_df.values,
    colLabels=sum_df.columns,
    cellLoc="center", loc="center",
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1, 1.5)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor("#37474F")
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#ECEFF1")
ax_d.set_title("Sample Sizes and Data Availability by Position Group",
               fontsize=11, fontweight="bold", pad=15)
fig_d.savefig("fig_D_table.png", dpi=150, bbox_inches="tight")
plt.close(fig_d)
print("  → fig_D_table.png")

# ── 10. Console summary ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("MEDIAN DIFFERENCE (Drafted − Undrafted) by position:")
print(heat_df.to_string(float_format="{:+.2f}".format))
print("="*60)
print("\nLogistic regression top effects:")
top = res_df.reindex(res_df["coef"].abs().nlargest(10).index)
for _, r in top.iterrows():
    print(f"  {r['pos_group']:4s} {r['feature']:12s}  coef={r['coef']:+.3f}")

print("\nAll figures saved:")
print("  fig_A_violins.png      — violin plots (position × feature)")
print("  fig_B_coefficients.png — logistic regression coefficients")
print("  fig_C_heatmap.png      — median difference heatmap")
print("  fig_D_table.png        — sample size table")
