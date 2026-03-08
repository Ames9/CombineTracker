# NFL Combine & Pro Day Explorer

**v1.0 — 2026/03/08**
Built by [Ames](https://x.com/ames_NFL) & Claude Code

An interactive Streamlit app for exploring NFL Combine and Pro Day athletic measurements, with draft outcome overlays, prospect comparisons, and similar-player search.

You can open the app [here](https://ames-combinetracker.streamlit.app/).
---

## English

### Features

- **Scatter plot** — Plot any two measurements against each other; color by position group or draft round
- **Histogram** — Distribution of any measurement with KDE overlay; highlight individual players across all years
- **Player Comparison** — Radar chart comparing up to 4 players on shared measurements (percentile vs. drafted players of same position)
- **Similar Players** — Find historical players with the closest combine profile using z-score Euclidean distance
- **2026 Pre-Draft overlay** — 2026 Combine participants shown as gold markers or KDE curves
- **Bilingual UI** — Toggle between English and Japanese

### Data

| Source | Coverage |
|--------|----------|
| NFL Combine (official API) | 2006 – 2026 |
| Pro Day measurements | 2006 – 2025 (various public sources) |
| Draft data | nflverse (2006–2024) + manual (2025) |
| Career data | nflverse `players.csv` |

Data aggregated from [Roy Carpenter's nfl-draft-data](https://github.com/array-carpenter/nfl-draft-data).

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd CombineTracker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run locally
streamlit run app.py
```

### Requirements

```
streamlit
pandas
numpy
plotly
scipy
```

### Measurements Available

| Label | Description |
|-------|-------------|
| Height (in) | Height in inches |
| Weight (lbs) | Weight in pounds |
| 40-Yard Dash (s) | 40-yard dash time |
| 10-Yard Split (s) | First 10 yards of the 40 |
| Bench Press (reps) | 225 lb bench press repetitions |
| Vertical Jump (in) | Vertical leap height |
| Broad Jump (in) | Standing broad jump distance |
| 3-Cone Drill (s) | L-drill agility time |
| Shuttle Run (s) | 20-yard short shuttle time |
| Wingspan (in) | Wingspan measurement |
| Hand Size (in) | Hand circumference |
| Scout Grade ★ | Pre-draft scout evaluation (0–100) |

### Notes

- **Combine preferred**: When both Combine and Pro Day data are available, Combine takes priority. Pro Day is used as a fallback when the toggle is ON.
- **Percentiles**: Calculated against all drafted players of the same position group across all years (2006–2024). Speed/agility metrics (lower = better) are inverted.
- **2026 prospects** are pre-draft and have no draft outcome data yet.
- **Similar Players** requires at least 4 shared measurements between the query player and historical players.

---

## 日本語

### 機能一覧

- **散布図** — 任意の2測定項目をプロット。ポジション別またはドラフトラウンド別でカラーリング
- **ヒストグラム** — 任意の測定値の分布をKDEオーバーレイ付きで表示。検索した選手は年度フィルタに関係なく点線で表示
- **選手比較** — 最大4選手をレーダーチャートで比較（共通の測定項目のみ使用）。同ポジションの歴代ドラフト指名選手とのパーセンタイル比較
- **類似選手ファインダー** — z-scoreユークリッド距離で過去の最も近いコンバインプロフィールの選手を検索
- **2026年プレドラフトオーバーレイ** — 2026年コンバイン参加者をゴールドマーカーまたはKDE曲線で表示
- **バイリンガルUI** — 英語・日本語を切り替え可能

### データソース

| ソース | カバレッジ |
|--------|-----------|
| NFL Combine（公式API） | 2006 – 2026年 |
| Pro Day計測 | 2006 – 2025年（各種公開ソース） |
| ドラフトデータ | nflverse (2006–2024) + 手動入力 (2025) |
| キャリアデータ | nflverse `players.csv` |

データ集約元: [Roy Carpenter's nfl-draft-data](https://github.com/array-carpenter/nfl-draft-data)

### セットアップ

```bash
# 1. リポジトリをクローン
git clone <repo-url>
cd CombineTracker

# 2. 依存パッケージをインストール
pip install -r requirements.txt

# 3. ローカルで起動
streamlit run app.py
```

### 使い方

1. サイドバーで年度・ポジション・測定項目・データソースを設定
2. 散布図タブで2軸の相関を確認
3. ヒストグラムタブで分布を確認（選手検索で特定選手の位置を点線表示）
4. 選手比較タブで最大4選手をレーダーチャートで比較
5. 類似選手ファインダーで過去の選手との類似度を検索

### 注意事項

- **Combine優先**: CombineとPro Day両方のデータがある場合、Combineが優先されます。Pro Dayはトグルがオンの場合にフォールバックとして使用。
- **パーセンタイル**: 同じポジショングループの歴代ドラフト指名選手全員（2006–2024年）との比較。タイム系計測（低い方が良い）は反転処理済み。
- **2026年選手**はプレドラフト段階のためドラフト結果データはありません。
- **類似選手**の検索には、クエリ選手と過去選手の間で最低4つの共通測定項目が必要です。

### ライセンス

データは各出典元のライセンスに従います。アプリのコードは個人・教育目的での使用を想定しています。

---

*Built by [Ames](https://x.com/ames_NFL) & Claude Code*
