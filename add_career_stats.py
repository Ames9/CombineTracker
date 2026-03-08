"""
nflverse players.csv からキャリア統計を取得して combine_with_draft.csv にマージ。

追加カラム:
  career_seasons     int     NFL在籍年数 (years_of_experience)
  nfl_rookie_season  int     NFL初年度
  nfl_last_season    int     NFL最終年度
  nfl_status         str     現在のステータス (ACT/RES/RET/DEV/NaN)
  career_matched     bool    nflverse players.csv にマッチした場合 True

出力: combine_with_career.csv
"""

import warnings
warnings.filterwarnings("ignore")

import urllib.request
import io
import unicodedata
import re
import pandas as pd

# ── nflverse players.csv を取得 ────────────────────────────────────────────────
PLAYERS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
)

print("Fetching nflverse players.csv ...")
raw = urllib.request.urlopen(PLAYERS_URL).read().decode("utf-8")
players = pd.read_csv(io.StringIO(raw))
print(f"  players.csv: {len(players):,} rows, {len(players.columns)} cols")

# 必要カラムだけ取り出す
players_sub = players[[
    "smart_id",
    "display_name",
    "years_of_experience",
    "rookie_season",
    "last_season",
    "status",
]].copy()

players_sub.rename(columns={
    "smart_id":            "person_id",
    "years_of_experience": "career_seasons",
    "rookie_season":       "nfl_rookie_season",
    "last_season":         "nfl_last_season",
    "status":              "nfl_status",
}, inplace=True)

# ── combine_with_draft.csv を読み込み ──────────────────────────────────────────
print("Loading combine_with_draft.csv ...")
df = pd.read_csv(
    "combine_with_draft.csv",
    dtype={"draft_round": "Int64", "draft_pick": "Int64"},
)
print(f"  combine: {len(df):,} rows")

# ── person_id (=smart_id) でマージ ────────────────────────────────────────────
df_merged = df.merge(
    players_sub,
    on="person_id",
    how="left",
)

# マッチフラグ
df_merged["career_matched"] = df_merged["career_seasons"].notna()

# 数値型変換
df_merged["career_seasons"]   = pd.to_numeric(df_merged["career_seasons"],   errors="coerce").astype("Int64")
df_merged["nfl_rookie_season"] = pd.to_numeric(df_merged["nfl_rookie_season"], errors="coerce").astype("Int64")
df_merged["nfl_last_season"]   = pd.to_numeric(df_merged["nfl_last_season"],   errors="coerce").astype("Int64")

# ── 統計サマリー ──────────────────────────────────────────────────────────────
total      = len(df_merged)
matched    = df_merged["career_matched"].sum()
drafted_m  = df_merged[df_merged["drafted"] == True]["career_matched"].sum()
undrafted_m = df_merged[df_merged["drafted"] == False]["career_matched"].sum()
udfa_total  = (df_merged["drafted"] == False).sum()

print(f"\nMatch summary:")
print(f"  Total rows     : {total:,}")
print(f"  Matched        : {matched:,} ({matched/total*100:.1f}%)")
print(f"  Drafted matched: {drafted_m:,}")
print(f"  UDFA total     : {udfa_total:,}")
print(f"  UDFA matched   : {undrafted_m:,} ({undrafted_m/udfa_total*100:.1f}%)")

print("\nUDFA career_seasons distribution:")
udfa = df_merged[df_merged["drafted"] == False]
dist = udfa["career_seasons"].value_counts().sort_index()
for k, v in dist.items():
    print(f"  {k:>3} seasons: {v:>4} players")

# 代表的なUDFA成功例
print("\nTop UDFA by career seasons:")
top_udfa = (
    df_merged[df_merged["drafted"] == False]
    .nlargest(10, "career_seasons")[
        ["player", "year", "position", "career_seasons", "nfl_rookie_season", "nfl_last_season", "nfl_status"]
    ]
)
print(top_udfa.to_string(index=False))

# ── 保存 ──────────────────────────────────────────────────────────────────────
df_merged.to_csv("combine_with_career.csv", index=False)
print(f"\n→ combine_with_career.csv saved ({len(df_merged):,} rows)")
print("  New columns: career_seasons, nfl_rookie_season, nfl_last_season, nfl_status, career_matched")
