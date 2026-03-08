"""
腕の長さ（Arm Length）× ポジション別ドラフト指名比較
  - combine 計測優先、なければ pro day 計測を使用
  - ドラフト指名あり / なし の分布を複数の観点で可視化
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
DRAFTED_COLOR   = "#1565C0"   # 濃い青
UNDRAFTED_COLOR = "#E53935"   # 赤
BOTH_ALPHA      = 0.82

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

# arm_length: combine 優先、なければ pro day
df["arm_length"] = df["combine_arm_length"].combine_first(df["pro_day_arm_length"])
df["source"] = np.where(
    df["combine_arm_length"].notna(), "combine",
    np.where(df["pro_day_arm_length"].notna(), "pro_day", None)
).astype(object)

# ドラフト判定済み & arm_length あり
df = df[df["drafted"].notna() & df["arm_length"].notna()].copy()
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
print(f"{'Pos':4s}  {'n_draft':>7s}  {'med_D':>7s}  {'med_U':>7s}  {'Δmed':>7s}  {'p-val':>8s}  {'sig':3s}")
print("-" * 55)
stats_rows = []
for pos in POS_ORDER:
    sub  = df[df["pos_group"] == pos]
    d_   = sub[sub["drafted"]]["arm_length"]
    u_   = sub[~sub["drafted"]]["arm_length"]
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
# Figure 1: バイオリン + 個別データ点（ストリップ）
# ════════════════════════════════════════════════════════════════════════════
fig1, axes = plt.subplots(2, 5, figsize=(22, 9), constrained_layout=True)
axes = axes.flatten()

patch_d = mpatches.Patch(color=DRAFTED_COLOR,   alpha=BOTH_ALPHA, label="Drafted")
patch_u = mpatches.Patch(color=UNDRAFTED_COLOR, alpha=BOTH_ALPHA, label="Undrafted")

for ax, pos in zip(axes, POS_ORDER):
    sub = df[df["pos_group"] == pos].copy()
    sub["Status"] = sub["drafted"].map({True: "Drafted", False: "Undrafted"})
    n_d = sub["drafted"].sum()
    n_u = (~sub["drafted"]).sum()

    palette = {"Drafted": DRAFTED_COLOR, "Undrafted": UNDRAFTED_COLOR}

    # バイオリン
    sns.violinplot(
        data=sub, x="Status", y="arm_length", ax=ax,
        palette=palette, inner=None, linewidth=0.6, alpha=0.45,
        order=["Drafted", "Undrafted"],
        density_norm="width",
    )
    # 四分位箱
    sns.boxplot(
        data=sub, x="Status", y="arm_length", ax=ax,
        palette=palette, width=0.18, linewidth=1.2,
        fliersize=0, order=["Drafted", "Undrafted"],
        boxprops=dict(alpha=0.9),
    )

    # 中央値ライン
    for i, status in enumerate(["Drafted", "Undrafted"]):
        med = sub[sub["Status"] == status]["arm_length"].median()
        ax.plot([i - 0.3, i + 0.3], [med, med],
                color="white", linewidth=2.0, solid_capstyle="round", zorder=5)
        ax.text(i + 0.33, med, f"{med:.2f}″", va="center",
                fontsize=7.5, fontweight="bold",
                color=DRAFTED_COLOR if status == "Drafted" else UNDRAFTED_COLOR)

    # 統計有意性
    row = stats_df[stats_df["pos"] == pos]
    if not row.empty:
        sig  = row["sig"].values[0]
        pval = row["pval"].values[0]
        ymax = sub["arm_length"].quantile(0.98)
        ax.annotate(
            f"{sig}  (p={pval:.3f})" if sig != "ns" else f"ns  (p={pval:.3f})",
            xy=(0.5, 0.97), xycoords="axes fraction",
            ha="center", va="top", fontsize=8,
            color="black" if sig != "ns" else "grey",
            fontweight="bold" if sig != "ns" else "normal",
        )

    ax.set_title(f"{pos}  (n={n_d}✓, {n_u}✗)", fontsize=11, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Arm Length (inches)", fontsize=9)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_facecolor("#FAFAFA")

fig1.legend(handles=[patch_d, patch_u], loc="upper center",
            ncol=2, fontsize=11, framealpha=0.9,
            bbox_to_anchor=(0.5, 1.025))
fig1.suptitle(
    "Arm Length by Position: Drafted vs Undrafted  (2006–2025)\n"
    "Combine measurement preferred; Pro Day used when combine unavailable",
    fontsize=13, fontweight="bold", y=1.06,
)
fig1.savefig("arm_length_violin.png", dpi=150, bbox_inches="tight")
plt.close(fig1)
print("\n→ arm_length_violin.png")

# ════════════════════════════════════════════════════════════════════════════
# Figure 2: 中央値差 + 95% CI の横棒グラフ（ポジション比較）
# ════════════════════════════════════════════════════════════════════════════
# Bootstrap で CI を計算
rng = np.random.default_rng(42)
ci_records = []
for _, srow in stats_df.iterrows():
    pos = srow["pos"]
    sub = df[df["pos_group"] == pos]
    d_  = sub[sub["drafted"]]["arm_length"].values
    u_  = sub[~sub["drafted"]]["arm_length"].values
    deltas = []
    for _ in range(2000):
        bd = rng.choice(d_, size=len(d_), replace=True)
        bu = rng.choice(u_, size=len(u_), replace=True)
        deltas.append(np.median(bd) - np.median(bu))
    ci_lo, ci_hi = np.percentile(deltas, [2.5, 97.5])
    ci_records.append({"pos": pos, "delta": srow["delta_median"],
                        "ci_lo": ci_lo, "ci_hi": ci_hi,
                        "sig": srow["sig"]})

ci_df = pd.DataFrame(ci_records).sort_values("delta")

fig2, ax2 = plt.subplots(figsize=(9, 5.5), constrained_layout=True)

bar_colors = [DRAFTED_COLOR if d > 0 else UNDRAFTED_COLOR for d in ci_df["delta"]]
bars = ax2.barh(ci_df["pos"], ci_df["delta"], color=bar_colors, alpha=0.8, zorder=3, height=0.55)

for i, (_, row) in enumerate(ci_df.iterrows()):
    # CI whisker
    ax2.plot([row["ci_lo"], row["ci_hi"]], [i, i],
             color="black", linewidth=2.0, zorder=5, solid_capstyle="round")
    ax2.plot([row["ci_lo"]] * 2, [i - 0.18, i + 0.18], color="black", linewidth=1.5, zorder=5)
    ax2.plot([row["ci_hi"]] * 2, [i - 0.18, i + 0.18], color="black", linewidth=1.5, zorder=5)
    # 値ラベル
    xoff = 0.02 if row["delta"] >= 0 else -0.02
    ha   = "left" if row["delta"] >= 0 else "right"
    ax2.text(row["delta"] + xoff, i,
             f"{row['delta']:+.3f}\"  {row['sig']}",
             va="center", ha=ha, fontsize=9,
             color=DRAFTED_COLOR if row["delta"] > 0 else UNDRAFTED_COLOR,
             fontweight="bold" if row["sig"] != "ns" else "normal")

ax2.axvline(0, color="black", linewidth=1.0, linestyle="--", zorder=2)
ax2.set_xlabel("Median Arm Length: Drafted − Undrafted (inches)", fontsize=11)
ax2.set_title(
    "Arm Length Advantage of Drafted Players by Position\n"
    "(Median difference with 95% bootstrap CI — positive = drafted players have longer arms)",
    fontsize=12, fontweight="bold",
)
ax2.tick_params(axis="both", labelsize=10)
ax2.grid(axis="x", alpha=0.3, linestyle="--", zorder=1)
ax2.set_facecolor("#FAFAFA")

note = "*** p<0.001  ** p<0.01  * p<0.05  ns: not significant"
ax2.text(0.99, 0.01, note, transform=ax2.transAxes,
         ha="right", va="bottom", fontsize=8, color="grey")

fig2.savefig("arm_length_delta.png", dpi=150, bbox_inches="tight")
plt.close(fig2)
print("→ arm_length_delta.png")

# ════════════════════════════════════════════════════════════════════════════
# Figure 3: KDE（確率密度）比較 — ポジション別
# ════════════════════════════════════════════════════════════════════════════
fig3, axes3 = plt.subplots(2, 5, figsize=(22, 8), constrained_layout=True)
axes3 = axes3.flatten()

for ax, pos in zip(axes3, POS_ORDER):
    sub = df[df["pos_group"] == pos]
    d_vals = sub[sub["drafted"]]["arm_length"]
    u_vals = sub[~sub["drafted"]]["arm_length"]

    ax.hist(d_vals, bins=20, density=True, alpha=0.35, color=DRAFTED_COLOR, label="Drafted")
    ax.hist(u_vals, bins=20, density=True, alpha=0.35, color=UNDRAFTED_COLOR, label="Undrafted")

    # KDE
    for vals, color in [(d_vals, DRAFTED_COLOR), (u_vals, UNDRAFTED_COLOR)]:
        if len(vals) > 5:
            kde = stats.gaussian_kde(vals, bw_method=0.4)
            xs = np.linspace(vals.min() - 1, vals.max() + 1, 300)
            ax.plot(xs, kde(xs), color=color, linewidth=2.2)
            ax.axvline(vals.median(), color=color, linewidth=1.4,
                       linestyle="--", alpha=0.8)

    row = stats_df[stats_df["pos"] == pos]
    sig_txt = "" if row.empty else f"  {row['sig'].values[0]}"
    ax.set_title(f"{pos}  (n={len(d_vals)}✓, {len(u_vals)}✗){sig_txt}",
                 fontsize=10, fontweight="bold")
    ax.set_xlabel("Arm Length (inches)", fontsize=8)
    ax.set_ylabel("Density", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.3, linestyle="--")
    ax.set_facecolor("#FAFAFA")

axes3[0].legend(fontsize=9, framealpha=0.9)
fig3.suptitle(
    "Arm Length Distribution: Drafted vs Undrafted by Position  (2006–2025)\n"
    "Dashed lines = median",
    fontsize=13, fontweight="bold",
)
fig3.savefig("arm_length_kde.png", dpi=150, bbox_inches="tight")
plt.close(fig3)
print("→ arm_length_kde.png")

# ════════════════════════════════════════════════════════════════════════════
# Figure 4: ドラフト率 × arm_length のビン別折れ線グラフ
# ════════════════════════════════════════════════════════════════════════════
fig4, axes4 = plt.subplots(2, 5, figsize=(22, 8), constrained_layout=True)
axes4 = axes4.flatten()

for ax, pos in zip(axes4, POS_ORDER):
    sub = df[df["pos_group"] == pos].copy()
    if len(sub) < 30:
        ax.set_visible(False); continue

    sub["arm_bin"] = pd.qcut(sub["arm_length"], q=8, duplicates="drop")
    grp = sub.groupby("arm_bin", observed=True).agg(
        draft_rate=("drafted", "mean"),
        n=("drafted", "count"),
        arm_mid=("arm_length", "median"),
    ).reset_index()

    # 太さは n に比例
    norm_n = grp["n"] / grp["n"].max()

    ax.plot(grp["arm_mid"], grp["draft_rate"] * 100,
            color=DRAFTED_COLOR, linewidth=2.2, marker="o", markersize=6, zorder=4)
    # CI (Wilson)
    for _, r in grp.iterrows():
        p  = r["draft_rate"]
        n  = r["n"]
        ci = 1.96 * np.sqrt(p * (1 - p) / n) if n > 0 else 0
        ax.fill_between([r["arm_mid"] - 0.1, r["arm_mid"] + 0.1],
                        [(p - ci) * 100] * 2, [(p + ci) * 100] * 2,
                        alpha=0.15, color=DRAFTED_COLOR)

    ax.axhline(sub["drafted"].mean() * 100, color="grey",
               linewidth=1.0, linestyle="--", label="Overall avg")
    ax.set_ylim(0, 100)
    ax.set_title(f"{pos}  (n={len(sub)})", fontsize=10, fontweight="bold")
    ax.set_xlabel("Arm Length (inches)", fontsize=8)
    ax.set_ylabel("Draft Rate (%)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(alpha=0.3, linestyle="--")
    ax.set_facecolor("#FAFAFA")

axes4[0].legend(fontsize=8)
fig4.suptitle(
    "Draft Rate vs Arm Length by Position  (2006–2025)\n"
    "Each point = percentile bin of arm length (dotted = overall draft rate)",
    fontsize=13, fontweight="bold",
)
fig4.savefig("arm_length_draft_rate.png", dpi=150, bbox_inches="tight")
plt.close(fig4)
print("→ arm_length_draft_rate.png")
print("\nDone.")
