"""
Hand Size × ポジション別ドラフト指名比較
  - combine 計測優先、なければ pro day 計測を使用
  - QBへの影響に特に注目
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats

# ── 設定 ─────────────────────────────────────────────────────────────────────
DRAFTED_COLOR   = "#1565C0"
UNDRAFTED_COLOR = "#E53935"

POS_MAP = {
    "QB":   ["QB"],
    "RB":   ["RB", "FB"],
    "WR":   ["WR", "WR/CB"],
    "TE":   ["TE"],
    "OT":   ["OT", "T"],
    "IOL":  ["OG", "C", "G", "OL"],
    "Edge": ["DE", "EDGE", "EDG", "OLB"],
    "DT":   ["DT", "NT", "IDL", "DL"],
    "ILB":  ["ILB", "MLB", "LB"],
    "DB":   ["CB", "S", "FS", "SS", "DB", "SAF"],
}
POS_ORDER = ["QB", "WR", "TE", "RB", "OT", "IOL", "Edge", "DT", "ILB", "DB"]

# ── データ読み込み ─────────────────────────────────────────────────────────────
df = pd.read_csv("combine_with_draft.csv",
                 dtype={"draft_round": "Int64", "draft_pick": "Int64"})

df["hand_size"] = df["combine_hand_size"].combine_first(df["pro_day_hand_size"])
df["source"] = np.where(
    df["combine_hand_size"].notna(), "combine",
    np.where(df["pro_day_hand_size"].notna(), "pro_day", None)
).astype(object)

df = df[df["drafted"].notna() & df["hand_size"].notna()].copy()
df["drafted"] = df["drafted"].astype(bool)

def map_pos(pos):
    if not isinstance(pos, str): return None
    pos = pos.upper().strip()
    for group, aliases in POS_MAP.items():
        if pos in aliases: return group
    return None

df["pos_group"] = df["position"].apply(map_pos)
df = df[df["pos_group"].notna()].copy()

# ── 統計サマリー ──────────────────────────────────────────────────────────────
print(f"{'Pos':4s}  {'n_total':>7s}  {'med_D':>7s}  {'med_U':>7s}  {'Δmed':>7s}  {'p-val':>8s}  {'sig':3s}")
print("-" * 55)
stats_rows = []
for pos in POS_ORDER:
    sub = df[df["pos_group"] == pos]
    d_  = sub[sub["drafted"]]["hand_size"]
    u_  = sub[~sub["drafted"]]["hand_size"]
    if len(d_) < 10 or len(u_) < 10:
        continue
    stat, pval = stats.mannwhitneyu(d_, u_, alternative="two-sided")
    delta = d_.median() - u_.median()
    sig   = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
    print(f"{pos:4s}  {len(sub):>7d}  {d_.median():>7.3f}  {u_.median():>7.3f}  "
          f"{delta:>+7.3f}  {pval:>8.4f}  {sig:3s}")
    stats_rows.append({"pos": pos, "n_drafted": len(d_), "n_undrafted": len(u_),
                       "med_drafted": d_.median(), "med_undrafted": u_.median(),
                       "delta_median": delta, "pval": pval, "sig": sig})

stats_df = pd.DataFrame(stats_rows)

# ════════════════════════════════════════════════════════════════════════════
# Figure 1: バイオリン + 箱ひげ
# ════════════════════════════════════════════════════════════════════════════
fig1, axes = plt.subplots(2, 5, figsize=(22, 9), constrained_layout=True)
axes = axes.flatten()

patch_d = mpatches.Patch(color=DRAFTED_COLOR,   alpha=0.8, label="Drafted")
patch_u = mpatches.Patch(color=UNDRAFTED_COLOR, alpha=0.8, label="Undrafted")

for ax, pos in zip(axes, POS_ORDER):
    sub = df[df["pos_group"] == pos].copy()
    sub["Status"] = sub["drafted"].map({True: "Drafted", False: "Undrafted"})
    n_d = sub["drafted"].sum()
    n_u = (~sub["drafted"]).sum()
    palette = {"Drafted": DRAFTED_COLOR, "Undrafted": UNDRAFTED_COLOR}

    sns.violinplot(data=sub, x="Status", y="hand_size", ax=ax,
                   palette=palette, inner=None, linewidth=0.6, alpha=0.45,
                   order=["Drafted", "Undrafted"], density_norm="width")
    sns.boxplot(data=sub, x="Status", y="hand_size", ax=ax,
                palette=palette, width=0.18, linewidth=1.2,
                fliersize=0, order=["Drafted", "Undrafted"],
                boxprops=dict(alpha=0.9))

    for i, status in enumerate(["Drafted", "Undrafted"]):
        med = sub[sub["Status"] == status]["hand_size"].median()
        ax.plot([i - 0.3, i + 0.3], [med, med],
                color="white", linewidth=2.0, solid_capstyle="round", zorder=5)
        ax.text(i + 0.33, med, f"{med:.3f}″", va="center", fontsize=7.5,
                fontweight="bold",
                color=DRAFTED_COLOR if status == "Drafted" else UNDRAFTED_COLOR)

    row = stats_df[stats_df["pos"] == pos]
    if not row.empty:
        sig  = row["sig"].values[0]
        pval = row["pval"].values[0]
        ax.annotate(
            f"{sig}  (p={pval:.4f})" if sig != "ns" else f"ns  (p={pval:.3f})",
            xy=(0.5, 0.97), xycoords="axes fraction",
            ha="center", va="top", fontsize=8,
            color="black" if sig != "ns" else "grey",
            fontweight="bold" if sig != "ns" else "normal",
        )

    # QBは枠を強調
    if pos == "QB":
        for spine in ax.spines.values():
            spine.set_edgecolor("#FF8F00")
            spine.set_linewidth(2.5)

    ax.set_title(f"{pos}  (n={n_d}✓, {n_u}✗)", fontsize=11, fontweight="bold",
                 color="#FF8F00" if pos == "QB" else "black")
    ax.set_xlabel("")
    ax.set_ylabel("Hand Size (inches)", fontsize=9)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_facecolor("#FAFAFA")

fig1.legend(handles=[patch_d, patch_u], loc="upper center",
            ncol=2, fontsize=11, framealpha=0.9,
            bbox_to_anchor=(0.5, 1.025))
fig1.suptitle(
    "Hand Size by Position: Drafted vs Undrafted  (2006–2025)\n"
    "Combine measurement preferred; Pro Day used when combine unavailable  |  Orange border = focus position (QB)",
    fontsize=12, fontweight="bold", y=1.06,
)
fig1.savefig("hand_size_violin.png", dpi=150, bbox_inches="tight")
plt.close(fig1)
print("\n→ hand_size_violin.png")

# ════════════════════════════════════════════════════════════════════════════
# Figure 2: 中央値差 + 95% CI 横棒
# ════════════════════════════════════════════════════════════════════════════
rng = np.random.default_rng(42)
ci_records = []
for _, srow in stats_df.iterrows():
    pos = srow["pos"]
    sub = df[df["pos_group"] == pos]
    d_  = sub[sub["drafted"]]["hand_size"].values
    u_  = sub[~sub["drafted"]]["hand_size"].values
    deltas = [np.median(rng.choice(d_, len(d_), replace=True)) -
              np.median(rng.choice(u_, len(u_), replace=True))
              for _ in range(2000)]
    ci_lo, ci_hi = np.percentile(deltas, [2.5, 97.5])
    ci_records.append({"pos": pos, "delta": srow["delta_median"],
                        "ci_lo": ci_lo, "ci_hi": ci_hi, "sig": srow["sig"]})

ci_df = pd.DataFrame(ci_records).sort_values("delta")

fig2, ax2 = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
bar_colors = [("#FF8F00" if r["pos"] == "QB" else DRAFTED_COLOR) if r["delta"] > 0
              else UNDRAFTED_COLOR for _, r in ci_df.iterrows()]
ax2.barh(ci_df["pos"], ci_df["delta"], color=bar_colors, alpha=0.82, zorder=3, height=0.55)

for i, (_, row) in enumerate(ci_df.iterrows()):
    ax2.plot([row["ci_lo"], row["ci_hi"]], [i, i],
             color="black", linewidth=2.0, zorder=5, solid_capstyle="round")
    for x in [row["ci_lo"], row["ci_hi"]]:
        ax2.plot([x, x], [i - 0.18, i + 0.18], color="black", linewidth=1.5, zorder=5)
    xoff = 0.005 if row["delta"] >= 0 else -0.005
    ha   = "left"  if row["delta"] >= 0 else "right"
    label_color = ("#FF8F00" if row["pos"] == "QB" else DRAFTED_COLOR) if row["delta"] > 0 else UNDRAFTED_COLOR
    ax2.text(row["delta"] + xoff, i,
             f"{row['delta']:+.3f}\"  {row['sig']}",
             va="center", ha=ha, fontsize=9,
             color=label_color,
             fontweight="bold" if row["sig"] != "ns" else "normal")

ax2.axvline(0, color="black", linewidth=1.0, linestyle="--", zorder=2)
ax2.set_xlabel("Median Hand Size: Drafted − Undrafted (inches)", fontsize=11)
ax2.set_title(
    "Hand Size Advantage of Drafted Players by Position\n"
    "(Median difference with 95% bootstrap CI — orange = QB focus)",
    fontsize=12, fontweight="bold",
)
ax2.tick_params(axis="both", labelsize=10)
ax2.grid(axis="x", alpha=0.3, linestyle="--", zorder=1)
ax2.set_facecolor("#FAFAFA")
ax2.text(0.99, 0.01, "*** p<0.001  ** p<0.01  * p<0.05  ns: not significant",
         transform=ax2.transAxes, ha="right", va="bottom", fontsize=8, color="grey")

fig2.savefig("hand_size_delta.png", dpi=150, bbox_inches="tight")
plt.close(fig2)
print("→ hand_size_delta.png")

# ════════════════════════════════════════════════════════════════════════════
# Figure 3: QB フォーカス — ドラフト順位 × hand_size の詳細分析
# ════════════════════════════════════════════════════════════════════════════
qb = df[df["pos_group"] == "QB"].copy()
qb_drafted = qb[qb["drafted"]].copy()

fig3, axes3 = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
fig3.suptitle("QB Hand Size Deep Dive  (2006–2025)", fontsize=13, fontweight="bold")

# ─ 左: KDE 分布 ─
ax = axes3[0]
d_ = qb[qb["drafted"]]["hand_size"]
u_ = qb[~qb["drafted"]]["hand_size"]
ax.hist(d_, bins=18, density=True, alpha=0.35, color=DRAFTED_COLOR, label=f"Drafted (n={len(d_)})")
ax.hist(u_, bins=18, density=True, alpha=0.35, color=UNDRAFTED_COLOR, label=f"Undrafted (n={len(u_)})")
for vals, color in [(d_, DRAFTED_COLOR), (u_, UNDRAFTED_COLOR)]:
    kde = stats.gaussian_kde(vals, bw_method=0.35)
    xs  = np.linspace(vals.min() - 0.3, vals.max() + 0.3, 300)
    ax.plot(xs, kde(xs), color=color, linewidth=2.5)
    ax.axvline(vals.median(), color=color, linewidth=1.5, linestyle="--", alpha=0.9)
stat, pval = stats.mannwhitneyu(d_, u_, alternative="two-sided")
ax.set_title(f"Distribution  (p={pval:.4f}, **)", fontsize=11, fontweight="bold")
ax.set_xlabel("Hand Size (inches)", fontsize=10)
ax.set_ylabel("Density", fontsize=10)
ax.legend(fontsize=9)
ax.grid(alpha=0.3, linestyle="--")
ax.set_facecolor("#FAFAFA")

# ─ 中: ドラフト率 × hand_size ビン ─
ax = axes3[1]
qb_valid = qb.copy()
qb_valid["hand_bin"] = pd.qcut(qb_valid["hand_size"], q=6, duplicates="drop")
grp = qb_valid.groupby("hand_bin", observed=True).agg(
    draft_rate=("drafted", "mean"),
    n=("drafted", "count"),
    hand_mid=("hand_size", "median"),
).reset_index()

ax.plot(grp["hand_mid"], grp["draft_rate"] * 100,
        color="#FF8F00", linewidth=2.5, marker="o", markersize=8, zorder=4)
for _, r in grp.iterrows():
    p  = r["draft_rate"]
    n  = r["n"]
    ci = 1.96 * np.sqrt(p * (1 - p) / n) if n > 0 else 0
    ax.errorbar(r["hand_mid"], p * 100, yerr=ci * 100,
                fmt="none", color="#FF8F00", capsize=4, linewidth=1.5)
    ax.text(r["hand_mid"], p * 100 + 2, f"n={int(n)}", ha="center", fontsize=7.5, color="grey")

ax.axhline(qb["drafted"].mean() * 100, color="grey",
           linewidth=1.2, linestyle="--", label=f"Overall avg {qb['drafted'].mean()*100:.1f}%")
ax.set_ylim(0, 100)
ax.set_title("Draft Rate by Hand Size  (QB)", fontsize=11, fontweight="bold")
ax.set_xlabel("Hand Size (inches)", fontsize=10)
ax.set_ylabel("Draft Rate (%)", fontsize=10)
ax.legend(fontsize=9)
ax.grid(alpha=0.3, linestyle="--")
ax.set_facecolor("#FAFAFA")

# ─ 右: ドラフトラウンド × hand_size (指名QBのみ) ─
ax = axes3[2]
round_data = {}
for rnd in [1, 2, 3, 4, 5, 6, 7]:
    vals = qb_drafted[qb_drafted["draft_round"] == rnd]["hand_size"].dropna()
    if len(vals) >= 3:
        round_data[f"Rd {rnd}\n(n={len(vals)})"] = vals

positions_y = list(range(len(round_data)))
labels      = list(round_data.keys())

# 箱ひげ
bp = ax.boxplot(
    [round_data[k] for k in labels],
    vert=False, positions=positions_y,
    patch_artist=True, widths=0.5,
    medianprops=dict(color="white", linewidth=2),
    whiskerprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.2),
    flierprops=dict(marker="o", markersize=3, alpha=0.5),
)
cmap = plt.cm.Blues_r
for i, patch in enumerate(bp["boxes"]):
    patch.set_facecolor(cmap(0.15 + i * 0.1))
    patch.set_alpha(0.85)

# 平均値
for i, (label, vals) in enumerate(round_data.items()):
    ax.plot(vals.mean(), i, marker="D", color="#FF8F00", markersize=6, zorder=5)

ax.set_yticks(positions_y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Hand Size (inches)", fontsize=10)
ax.set_title("Hand Size by Draft Round  (QB only)\n◆ = mean", fontsize=11, fontweight="bold")
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_facecolor("#FAFAFA")

# 9インチ基準線（NFL的な目安）
for ax_ in [axes3[1], axes3[2]]:
    ref_x = 9.0
    if ax_ == axes3[2]:
        ax_.axvline(ref_x, color="red", linewidth=1.0, linestyle=":", alpha=0.6, label='9" threshold')
        ax_.legend(fontsize=8)

fig3.savefig("hand_size_qb_focus.png", dpi=150, bbox_inches="tight")
plt.close(fig3)
print("→ hand_size_qb_focus.png")

# ════════════════════════════════════════════════════════════════════════════
# Figure 4: ドラフト率 × hand_size — 全ポジション
# ════════════════════════════════════════════════════════════════════════════
fig4, axes4 = plt.subplots(2, 5, figsize=(22, 8), constrained_layout=True)
axes4 = axes4.flatten()

for ax, pos in zip(axes4, POS_ORDER):
    sub = df[df["pos_group"] == pos].copy()
    if len(sub) < 30:
        ax.set_visible(False); continue

    sub["hand_bin"] = pd.qcut(sub["hand_size"], q=8, duplicates="drop")
    grp = sub.groupby("hand_bin", observed=True).agg(
        draft_rate=("drafted", "mean"),
        n=("drafted", "count"),
        hand_mid=("hand_size", "median"),
    ).reset_index()

    lcolor = "#FF8F00" if pos == "QB" else DRAFTED_COLOR
    ax.plot(grp["hand_mid"], grp["draft_rate"] * 100,
            color=lcolor, linewidth=2.2, marker="o", markersize=6, zorder=4)
    for _, r in grp.iterrows():
        p, n_ = r["draft_rate"], r["n"]
        ci = 1.96 * np.sqrt(p * (1 - p) / n_) if n_ > 0 else 0
        ax.fill_between(
            [r["hand_mid"] - 0.03, r["hand_mid"] + 0.03],
            [(p - ci) * 100] * 2, [(p + ci) * 100] * 2,
            alpha=0.2, color=lcolor,
        )

    ax.axhline(sub["drafted"].mean() * 100, color="grey",
               linewidth=1.0, linestyle="--")
    ax.set_ylim(0, 100)

    row = stats_df[stats_df["pos"] == pos]
    sig_txt = f"  {row['sig'].values[0]}" if not row.empty else ""
    border_color = "#FF8F00" if pos == "QB" else "none"
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)
        spine.set_linewidth(2.0 if pos == "QB" else 0.8)

    ax.set_title(f"{pos}  (n={len(sub)}){sig_txt}", fontsize=10, fontweight="bold",
                 color="#FF8F00" if pos == "QB" else "black")
    ax.set_xlabel("Hand Size (inches)", fontsize=8)
    ax.set_ylabel("Draft Rate (%)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.3, linestyle="--")
    ax.set_facecolor("#FAFAFA")

fig4.suptitle(
    "Draft Rate vs Hand Size by Position  (2006–2025)\n"
    "Each point = percentile bin  |  dashed = overall draft rate  |  Orange = QB",
    fontsize=13, fontweight="bold",
)
fig4.savefig("hand_size_draft_rate.png", dpi=150, bbox_inches="tight")
plt.close(fig4)
print("→ hand_size_draft_rate.png")
print("\nDone.")
