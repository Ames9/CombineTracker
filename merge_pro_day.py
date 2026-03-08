"""
combine_with_draft.csv に pro day データを統合する。

変更内容:
  1. 既存の測定カラムを combine_* プレフィックスに改名
  2. pro_day_* カラムを追加（全選手分）
  3. pro day データを対応する選手に埋め込む（コンバイン参加者も含む）
  4. コンバイン未参加・pro day 参加の選手を新規行として追加
  5. 新規行にドラフト指名情報を付与
"""

import io, re, unicodedata, urllib.request
import pandas as pd
import numpy as np

# ── 名前正規化 ─────────────────────────────────────────────────────────────────
def norm_name(s: str) -> str:
    if not isinstance(s, str): return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z ]", "", s.lower())
    return " ".join(s.split())

# ── 1. 既存 CSV 読み込み ─────────────────────────────────────────────────────────
print("Loading combine_with_draft.csv ...")
df = pd.read_csv("combine_with_draft.csv", dtype={"draft_round": "Int64", "draft_pick": "Int64"})

# ── 2. 測定カラムを combine_* にリネーム ──────────────────────────────────────────
COMBINE_RENAME = {
    "height":              "combine_height",
    "weight":              "combine_weight",
    "arm_length":          "combine_arm_length",
    "hand_size":           "combine_hand_size",
    "forty_yard_dash":     "combine_forty_yard_dash",
    "ten_yard_split":      "combine_ten_yard_split",
    "bench_press":         "combine_bench_press",
    "vertical_jump":       "combine_vertical_jump",
    "broad_jump":          "combine_broad_jump",
    "three_cone_drill":    "combine_three_cone_drill",
    "twenty_yard_shuttle": "combine_twenty_yard_shuttle",
}
df = df.rename(columns=COMBINE_RENAME)

# pro_day_* カラムを空で追加
PRO_DAY_COLS = [
    "pro_day_height", "pro_day_weight", "pro_day_arm_length", "pro_day_hand_size",
    "pro_day_forty_yard_dash", "pro_day_ten_yard_split", "pro_day_bench_press",
    "pro_day_vertical_jump", "pro_day_broad_jump", "pro_day_three_cone_drill",
    "pro_day_twenty_yard_shuttle", "pro_day_wingspan",
]
for col in PRO_DAY_COLS:
    df[col] = np.nan

df["name_key"] = df["player"].apply(norm_name)

# ── 3. Pro day データ読み込み ──────────────────────────────────────────────────
print("Loading combine_pro_day.csv ...")
pro = pd.read_csv("combine_pro_day.csv")
pro["Year"] = pro["Year"].astype(int)
pro["name_key"] = pro["player"].apply(norm_name)

PRO_MAP = {
    "Height (in)":      "pro_day_height",
    "Weight (lbs)":     "pro_day_weight",
    "Arm Length (in)":  "pro_day_arm_length",
    "Hand Size (in)":   "pro_day_hand_size",
    "40 Yard":          "pro_day_forty_yard_dash",
    "10-Yard Split":    "pro_day_ten_yard_split",
    "Bench Press":      "pro_day_bench_press",
    "Vert Leap (in)":   "pro_day_vertical_jump",
    "Broad Jump (in)":  "pro_day_broad_jump",
    "3Cone":            "pro_day_three_cone_drill",
    "Shuttle":          "pro_day_twenty_yard_shuttle",
    "Wingspan (in)":    "pro_day_wingspan",
}

# ── 4. 既存コンバイン参加者に pro day データを埋め込む ──────────────────────────────
print("Filling pro day data for existing combine attendees ...")
# (year, name_key) → df の行インデックス
combine_idx = {(row["year"], row["name_key"]): idx for idx, row in df.iterrows()}

both_count = 0
for _, prow in pro.iterrows():
    key = (prow["Year"], prow["name_key"])
    if key in combine_idx:
        idx = combine_idx[key]
        for pro_col, target_col in PRO_MAP.items():
            val = prow.get(pro_col, np.nan)
            if pd.notna(val):
                df.at[idx, target_col] = val
        both_count += 1

print(f"  Pro day data added to {both_count} existing combine rows")

# ── 5. コンバイン未参加の pro day 選手を特定 ───────────────────────────────────────
combine_keys = set(combine_idx.keys())
pro_only = pro[~pro.apply(lambda r: (r["Year"], r["name_key"]) in combine_keys, axis=1)].copy()
print(f"  Pro-day-only players: {len(pro_only)}")

# ── 6. ドラフトデータ取得（新規行に付与するため） ─────────────────────────────────────
print("Downloading draft picks from nflverse ...")
DRAFT_URL = "https://github.com/nflverse/nfldata/raw/master/data/draft_picks.csv"
raw = urllib.request.urlopen(DRAFT_URL).read().decode("utf-8")
draft = pd.read_csv(io.StringIO(raw))
draft = draft[draft["season"].astype(int) >= 2006].copy()
draft["season"] = draft["season"].astype(int)
draft["name_key"] = draft["pfr_name"].apply(norm_name)
draft["round"] = pd.to_numeric(draft["round"], errors="coerce").astype("Int64")
draft["pick"]  = pd.to_numeric(draft["pick"],  errors="coerce").astype("Int64")

# nflverse で持っている年のセット（2025はmanualデータ）
KNOWN_YEARS_NFLVERSE = set(draft["season"].unique())

draft_lookup = {}
for _, row in draft.iterrows():
    draft_lookup[(row["season"], row["name_key"])] = (row["round"], row["pick"], row["team"])

# 2025 ドラフトデータ（combine_with_draft.csv から再利用）
draft_2025 = df[(df["year"] == 2025) & (df["drafted"] == True)][
    ["name_key", "draft_round", "draft_pick", "draft_team"]
].dropna(subset=["draft_round"])
for _, row in draft_2025.iterrows():
    draft_lookup[(2025, row["name_key"])] = (row["draft_round"], row["draft_pick"], row["draft_team"])
KNOWN_YEARS_NFLVERSE.add(2025)

# ── 7. 新規行を構築 ───────────────────────────────────────────────────────────
print("Building new rows for pro-day-only players ...")
new_rows = []
for _, prow in pro_only.iterrows():
    yr      = prow["Year"]
    key     = (yr, prow["name_key"])

    # drafted 判定
    if yr in KNOWN_YEARS_NFLVERSE:
        if key in draft_lookup:
            rnd, pick, team = draft_lookup[key]
            drafted_val  = True
            draft_round  = rnd
            draft_pick   = pick
            draft_team   = team
        else:
            drafted_val  = False
            draft_round  = pd.NA
            draft_pick   = pd.NA
            draft_team   = pd.NA
    else:
        drafted_val  = pd.NA
        draft_round  = pd.NA
        draft_pick   = pd.NA
        draft_team   = pd.NA

    row = {
        "year":         yr,
        "drafted":      drafted_val,
        "draft_round":  draft_round,
        "draft_pick":   draft_pick,
        "draft_team":   draft_team,
        "player":       prow["player"],
        "first_name":   pd.NA,
        "last_name":    pd.NA,
        "college":      prow.get("College", pd.NA),
        "position":     prow.get("POS", pd.NA),
        "position_group": prow.get("POS_GP", pd.NA),
        "person_id":    prow.get("nfl_person_id", pd.NA),
        "grade":        pd.NA,
        "draft_grade":  pd.NA,
        "draft_projection": pd.NA,
        "nfl_comparison": pd.NA,
        "name_key":     prow["name_key"],
        # combine_* 列はすべて NaN
        **{col: np.nan for col in COMBINE_RENAME.values()},
        # pro_day_* 列
        **{target: prow.get(src, np.nan) for src, target in PRO_MAP.items()},
    }
    new_rows.append(row)

new_df = pd.DataFrame(new_rows)

# ── 8. 結合・ソート・保存 ──────────────────────────────────────────────────────
combined = pd.concat([df, new_df], ignore_index=True)
combined = combined.drop(columns=["name_key"])
combined = combined.sort_values(["year", "player"]).reset_index(drop=True)

# 型を整える
combined["draft_round"] = pd.to_numeric(combined["draft_round"], errors="coerce").astype("Int64")
combined["draft_pick"]  = pd.to_numeric(combined["draft_pick"],  errors="coerce").astype("Int64")
combined["drafted"]     = combined["drafted"].astype("boolean")

out_path = "combine_with_draft.csv"
combined.to_csv(out_path, index=False)
print(f"\nSaved → {out_path}  ({len(combined)} rows, {len(combined.columns)} columns)")

# ── 9. サマリー ───────────────────────────────────────────────────────────────
print("\n--- 選手区分 ---")
has_combine  = combined[list(COMBINE_RENAME.values())].notna().any(axis=1)
has_pro_day  = combined[PRO_DAY_COLS].notna().any(axis=1)

print(f"  コンバインのみ        : {(has_combine & ~has_pro_day).sum()}")
print(f"  コンバイン + Pro Day  : {(has_combine & has_pro_day).sum()}")
print(f"  Pro Day のみ         : {(~has_combine & has_pro_day).sum()}")
print(f"  両方なし（データ欠損） : {(~has_combine & ~has_pro_day).sum()}")

print("\n--- ドラフト状況 ---")
known = combined[combined["drafted"].notna()]
print(f"  指名あり : {int(known['drafted'].astype(bool).sum())}")
print(f"  未指名   : {int((~known['drafted'].astype(bool)).sum())}")
print(f"  不明     : {combined['drafted'].isna().sum()}")

print("\n--- 年別 pro-day-only 追加数 ---")
added = new_df.groupby("year").size().sort_index()
print(added.to_string())
print(f"\n--- 新規行のうちドラフト指名された選手数 ---")
nd = new_df[new_df["drafted"] == True]
print(f"  {len(nd)} 名")
print(nd[["year","player","position","draft_round","draft_pick","draft_team"]].head(20).to_string(index=False))
