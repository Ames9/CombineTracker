"""
combine_official.csv に nflverse のドラフトデータをマージして
combine_with_draft.csv として保存する。

追加カラム:
  drafted        bool   ドラフト指名された(2006-2024のみ判定, 2025-2026はNaN)
  draft_round    int    指名ラウンド (未指名 / 対象外は NaN)
  draft_pick     int    全体指名順位 (未指名 / 対象外は NaN)
  draft_team     str    指名チーム略称 (未指名 / 対象外は NaN)
"""

import urllib.request
import io
import re
import unicodedata
import warnings
warnings.filterwarnings("ignore")

import pandas as pd

# ── 1. Combine data ───────────────────────────────────────────────────────────
print("Loading combine_official.csv ...")
combine = pd.read_csv("combine_official.csv")
combine["year"] = combine["year"].astype(int)

# ── 2. Draft picks (nflverse) ─────────────────────────────────────────────────
DRAFT_URL = "https://github.com/nflverse/nfldata/raw/master/data/draft_picks.csv"
print("Downloading draft_picks from nflverse ...")
raw = urllib.request.urlopen(DRAFT_URL).read().decode("utf-8")
draft = pd.read_csv(io.StringIO(raw))
draft["season"] = draft["season"].astype(int)

# 必要カラムだけ絞る
draft = draft[["season", "pfr_name", "team", "round", "pick"]].copy()
draft.columns = ["season", "pfr_name", "draft_team", "draft_round", "draft_pick"]
draft["draft_round"] = pd.to_numeric(draft["draft_round"], errors="coerce").astype("Int64")
draft["draft_pick"]  = pd.to_numeric(draft["draft_pick"],  errors="coerce").astype("Int64")

# ── 3. Name normalisation ─────────────────────────────────────────────────────
def norm_name(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z ]", "", s.lower())
    return " ".join(s.split())

combine["name_key"] = combine["player"].apply(norm_name)
draft["name_key"]   = draft["pfr_name"].apply(norm_name)

# ── 4. Merge ──────────────────────────────────────────────────────────────────
# left join: combine の全行を保持し、draft 情報をアタッチ
merged = combine.merge(
    draft[["season", "name_key", "draft_team", "draft_round", "draft_pick"]],
    left_on=["year", "name_key"],
    right_on=["season", "name_key"],
    how="left",
).drop(columns=["season"], errors="ignore")

# drafted フラグ
#   2006-2024: draft データが存在するため True/False で判定
#   2025-2026: draft がまだ行われていない / データ未収録のため NaN
KNOWN_YEARS = set(draft["season"].unique())  # 実際にデータがある年

def assign_drafted(row):
    if row["year"] not in KNOWN_YEARS:
        return pd.NA          # 判定不能
    return pd.notna(row["draft_pick"])  # draft_pick がある = 指名済み

merged["drafted"] = merged.apply(assign_drafted, axis=1)
merged["drafted"] = merged["drafted"].astype("boolean")  # True/False/<NA>

# ── 5. カラム整理・並び替え ────────────────────────────────────────────────────
# name_key は作業用なので除去
merged = merged.drop(columns=["name_key"])

# drafted / draft_* を year の直後に挿入
orig_cols = list(combine.drop(columns=["name_key"]).columns)
new_cols  = ["drafted", "draft_round", "draft_pick", "draft_team"]
insert_at = orig_cols.index("year") + 1
final_cols = orig_cols[:insert_at] + new_cols + orig_cols[insert_at:]
merged = merged[final_cols]

# ── 6. 保存 ───────────────────────────────────────────────────────────────────
out_path = "combine_with_draft.csv"
merged.to_csv(out_path, index=False)
print(f"Saved → {out_path}  ({len(merged)} rows, {len(merged.columns)} columns)")

# ── 7. サマリー表示 ───────────────────────────────────────────────────────────
known = merged[merged["drafted"].notna()]
drafted = known["drafted"].sum()
undrafted = (~known["drafted"]).sum()
unknown = merged["drafted"].isna().sum()

print(f"\n  ドラフト判定済み: {len(known)} 選手 (年: {sorted(KNOWN_YEARS)[0]}–{sorted(KNOWN_YEARS)[-1]})")
print(f"    指名あり : {int(drafted):4d}")
print(f"    指名なし : {int(undrafted):4d}")
print(f"  判定不能  : {unknown} 選手 (2025–2026 など draft データ未収録)")
print(f"\n  ラウンド別指名数:")
print(merged["draft_round"].value_counts().sort_index().to_string())
