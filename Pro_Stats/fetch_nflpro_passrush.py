"""
NFL Pro Pass Rush Stats Fetcher
--------------------------------
NFL ProのAPIからPass Rushスタッツを取得してCSVに保存する。

使い方:
  1. Chrome/SafariでNFL Proにログインし、
     https://pro.nfl.com/stats/defense/season?tab=passRush を開く
  2. DevTools (F12) → Network → ページリロード → "passRush" でフィルタ
  3. リクエストのRequest Headersから "Authorization: Bearer xxxxx" をコピー
  4. 下記 BEARER_TOKEN に貼り付けて実行:
       python3 fetch_nflpro_passrush.py

出力: nflpro_passrush_{year}.csv (2019〜2024分)
"""

import requests
import csv
import json
import time

# ★ ここにBearerトークンを貼る（"Bearer " の部分は不要、トークン文字列のみ）
BEARER_TOKEN = "YOUR_TOKEN_HERE"

SEASONS = [2019, 2020, 2021, 2022, 2023, 2024]
OUTPUT_DIR = "."  # 同じフォルダに保存

BASE_URL = "https://pro.nfl.com/api/secured/stats/defense/passRush/season"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Accept": "application/json",
    "Origin": "https://pro.nfl.com",
    "Referer": "https://pro.nfl.com/stats/defense/season",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

PARAMS_BASE = {
    "sortValue": "DESC",
    "qualifiedDefender": "false",
    "seasonType": "REG",
    "limit": 500,  # 全選手取得
}

# 全シーズン統合用
all_rows = []


def fetch_season(season: int) -> list[dict]:
    params = {**PARAMS_BASE, "season": season, "sortKey": "qbpR"}
    print(f"Fetching {season}...", end=" ", flush=True)
    r = requests.get(BASE_URL, headers=HEADERS, params=params)

    if r.status_code == 401:
        print("❌ 401 Unauthorized - トークンを確認してください")
        return []
    if r.status_code != 200:
        print(f"❌ HTTP {r.status_code}")
        return []

    data = r.json()
    # レスポンス構造を確認
    if isinstance(data, dict):
        rows = data.get("players", data.get("stats", data.get("data", [])))
    elif isinstance(data, list):
        rows = data
    else:
        print(f"❌ Unexpected response format")
        print(json.dumps(data, indent=2)[:500])
        return []

    print(f"✅ {len(rows)} 選手")
    return rows


def flatten_row(row: dict, season: int) -> dict:
    """ネストされたJSONをフラットなdictに変換"""
    flat = {"season": season}

    # 選手情報
    player = row.get("player", row)
    flat["player_id"] = player.get("id", row.get("playerId", ""))
    flat["player_name"] = player.get("displayName", player.get("name", row.get("playerName", "")))
    flat["position"] = player.get("position", row.get("position", ""))
    flat["team"] = row.get("team", {}).get("abbreviation", row.get("teamAbbr", ""))
    flat["games"] = row.get("gamesPlayed", row.get("games", ""))

    # Pass Rush スタッツ（カラム名はAPIレスポンスを見て調整が必要な場合あり）
    stats = row.get("stats", row)
    flat["sacks"] = stats.get("sacks", stats.get("sk", ""))
    flat["qb_pressures"] = stats.get("qbpR", stats.get("pressures", stats.get("totalPressures", "")))
    flat["qb_hits"] = stats.get("qbHits", stats.get("qbh", ""))
    flat["hurries"] = stats.get("hurries", stats.get("hry", ""))
    flat["tackles_for_loss"] = stats.get("tacklesForLoss", stats.get("tfl", ""))
    flat["pass_rush_snaps"] = stats.get("passRushSnaps", stats.get("prSnaps", ""))
    flat["pressure_rate"] = stats.get("pressureRate", stats.get("prRate", ""))
    flat["pass_rush_win_rate"] = stats.get("passRushWinRate", stats.get("prwr", stats.get("winRate", "")))
    flat["get_off_time"] = stats.get("getOffTime", stats.get("got", ""))
    flat["double_team_rate"] = stats.get("doubleTeamRate", stats.get("dtr", ""))
    flat["run_stop_pct"] = stats.get("runStopPct", stats.get("rsp", ""))
    flat["run_snaps"] = stats.get("runSnaps", "")

    return flat


def save_csv(rows: list[dict], filename: str):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  → Saved: {filename}")


def main():
    if BEARER_TOKEN == "YOUR_TOKEN_HERE":
        print("⚠️  BEARER_TOKEN を設定してから実行してください")
        print("   スクリプト上部の BEARER_TOKEN = '...' に貼り付けてください")
        return

    print("=== NFL Pro Pass Rush Stats Fetcher ===\n")

    # まず1シーズン取得してレスポンス構造を確認
    test_rows = fetch_season(2024)
    if test_rows:
        print("\n--- APIレスポンスサンプル (1行目) ---")
        print(json.dumps(test_rows[0], indent=2, ensure_ascii=False)[:800])
        print("---\n")

    # 全シーズン取得
    for season in SEASONS:
        rows = fetch_season(season)
        if not rows:
            continue

        flat_rows = [flatten_row(r, season) for r in rows]
        all_rows.extend(flat_rows)

        # 年別CSVも保存
        filename = f"{OUTPUT_DIR}/nflpro_passrush_{season}.csv"
        save_csv(flat_rows, filename)

        time.sleep(0.5)  # API負荷軽減

    # 全シーズン統合CSV
    if all_rows:
        save_csv(all_rows, f"{OUTPUT_DIR}/nflpro_passrush_all.csv")
        print(f"\n✅ 完了: 合計 {len(all_rows)} 行")
    else:
        print("\n❌ データを取得できませんでした")


if __name__ == "__main__":
    main()
