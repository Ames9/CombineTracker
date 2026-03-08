"""
NFL Combine & Pro Day Explorer
インタラクティブな散布図ツール
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats
from scipy.stats import gaussian_kde

# ── ページ設定 ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NFL Combine & Pro Day Explorer",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── スタイル ───────────────────────────────────────────────────────────────────
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&display=swap');

/* ════ GLOBAL FONT ════ */
/* Streamlitのemotionクラス（css-xxxx）を含む主要コンテナに適用。icon系のspanは避ける */
html, body,
.stApp, .main,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"],
[data-testid="stCaptionContainer"] p,
[data-testid="stText"],
.stRadio p, .stRadio div,
.stSelectbox div, .stSlider div,
.stMultiSelect div, .stToggle div,
[data-baseweb="tab"] {
    font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
/* headerはvisibility:hiddenにするとサイドバー再展開ボタンが消えるので個別に非表示 */
#MainMenu  { display: none; }

/* ════ SIDEBAR TOGGLE ════ */
[data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    opacity: 0.5;
    transition: opacity 0.2s;
}
[data-testid="stSidebarCollapseButton"]:hover { opacity: 1; }
/* 折りたたみ後の再展開ボタン — headerを隠していないので自然に表示される */
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
}
.block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px;
}

/* ════ SIDEBAR ════ */
[data-testid="stSidebar"] {
    background: #161B22 !important;
    border-right: 1px solid #30363D !important;
    min-width: 300px !important;
    max-width: 310px !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 {
    color: #E6EDF3 !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
[data-testid="stSidebar"] h3 {
    color: #58A6FF !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.14em !important;
    border-left: 3px solid #58A6FF;
    padding-left: 8px;
    margin-top: 2px !important;
    margin-bottom: 4px !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #8B949E !important;
    font-size: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #6E7681 !important;
    font-size: 11px !important;
    font-style: italic;
}

/* ════ MAIN TITLE ════ */
.block-container h1 {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.025em !important;
    background: linear-gradient(135deg, #E6EDF3 30%, #58A6FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    padding-bottom: 2px;
}
.block-container h2 {
    color: #C9D1D9 !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}
.block-container h3 {
    color: #C9D1D9 !important;
    font-weight: 600 !important;
}

/* ════ HEADER METRIC CARDS ════ */
[data-testid="stMetric"] {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    transition: border-color 0.18s, box-shadow 0.18s;
}
[data-testid="stMetric"]:hover {
    border-color: #58A6FF !important;
    box-shadow: 0 0 0 1px rgba(88,166,255,0.25) !important;
}
[data-testid="stMetricLabel"] > div {
    color: #6E7681 !important;
    font-size: 10.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* ════ STATS PANEL BOXES ════ */
.metric-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 6px 0;
    font-size: 12px;
    line-height: 2.0;
    color: #C9D1D9;
}
.metric-box b { color: #E6EDF3; }
.sig-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
}

/* ════ DIVIDERS ════ */
hr {
    border-color: #21262D !important;
    margin: 10px 0 !important;
}

/* ════ EXPANDERS ════ */
[data-testid="stExpander"] {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    color: #C9D1D9 !important;
    font-weight: 500;
    font-size: 13px;
}
[data-testid="stExpander"] summary:hover { color: #58A6FF !important; }

/* ════ ALERTS ════ */
[data-testid="stAlert"] {
    background: #1C2128 !important;
    border-radius: 8px !important;
}

/* ════ MULTISELECT TAGS ════ */
[data-baseweb="tag"] {
    background: #1F6FEB !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] span {
    color: #E6EDF3 !important;
    font-size: 11px !important;
    font-weight: 500 !important;
}

/* ════ SCROLLBAR ════ */
::-webkit-scrollbar          { width: 5px; height: 5px; }
::-webkit-scrollbar-track    { background: #0D1117; }
::-webkit-scrollbar-thumb    { background: #30363D; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #58A6FF; }
"""

st.html(f"<style>{_CSS}</style>")

# ── ポジショングループ定義 ─────────────────────────────────────────────────────
POS_GROUPS = {
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
    "K/P":  ["K", "P", "LS", "KR"],
}
POS_GROUP_ORDER = ["QB", "RB", "WR", "TE", "OT", "IOL", "Edge", "DT", "ILB", "DB", "K/P"]

POS_COLORS = {
    "QB":   "#E53935",
    "RB":   "#FB8C00",
    "WR":   "#FDD835",
    "TE":   "#43A047",
    "OT":   "#00ACC1",
    "IOL":  "#4DD0E1",
    "Edge": "#FF5722",
    "DT":   "#1E88E5",
    "ILB":  "#8E24AA",
    "DB":   "#F06292",
    "K/P":  "#90A4AE",
}

PREDRAFT_COLOR      = "#FFD600"
PREDRAFT_BORDER     = "#FF8F00"
UDFA_SUCCESS_COLOR  = "#00C853"
UDFA_SUCCESS_BORDER = "#1B5E20"

# ── 測定項目定義 ───────────────────────────────────────────────────────────────
MEASUREMENTS = {
    "Height (in)":          ("combine_height",              "pro_day_height"),
    "Weight (lbs)":         ("combine_weight",              "pro_day_weight"),
    "Arm Length (in)":      ("combine_arm_length",          "pro_day_arm_length"),
    "Hand Size (in)":       ("combine_hand_size",           "pro_day_hand_size"),
    "40-Yard Dash (s)":     ("combine_forty_yard_dash",     "pro_day_forty_yard_dash"),
    "10-Yard Split (s)":    ("combine_ten_yard_split",      "pro_day_ten_yard_split"),
    "Bench Press (reps)":   ("combine_bench_press",         "pro_day_bench_press"),
    "Vertical Jump (in)":   ("combine_vertical_jump",       "pro_day_vertical_jump"),
    "Broad Jump (in)":      ("combine_broad_jump",          "pro_day_broad_jump"),
    "3-Cone Drill (s)":     ("combine_three_cone_drill",    "pro_day_three_cone_drill"),
    "20-Yd Shuttle (s)":    ("combine_twenty_yard_shuttle", "pro_day_twenty_yard_shuttle"),
    "Wingspan (in) ★Pro Day only": (None,                  "pro_day_wingspan"),
}

# ── データ読み込み（キャッシュ）────────────────────────────────────────────────
import os as _os

_CAREER_CSV  = "combine_with_career.csv"
_COMBINE_CSV = "combine_with_draft.csv"
HAS_CAREER   = _os.path.exists(_CAREER_CSV)

@st.cache_data
def load_data():
    csv_path = _CAREER_CSV if HAS_CAREER else _COMBINE_CSV
    dtype_map = {"draft_round": "Int64", "draft_pick": "Int64"}
    if HAS_CAREER:
        dtype_map.update({"career_seasons": "Int64",
                          "nfl_rookie_season": "Int64",
                          "nfl_last_season":   "Int64"})
    df = pd.read_csv(csv_path, dtype=dtype_map)
    df["year"] = df["year"].astype(int)

    pos_to_group = {}
    for grp, aliases in POS_GROUPS.items():
        for a in aliases:
            pos_to_group[a.upper()] = grp

    df["pos_group"] = df["position"].str.upper().str.strip().map(pos_to_group)
    df["_drafted_base"] = df["drafted"].map(
        {True: "Drafted", False: "Undrafted", pd.NA: "Unknown"}
    ).fillna("Unknown")

    return df

def apply_udfa_label(df: pd.DataFrame, udfa_threshold: int) -> pd.DataFrame:
    df = df.copy()
    df["drafted_label"] = df["_drafted_base"]
    if HAS_CAREER and udfa_threshold > 0:
        success_mask = (
            (df["drafted"] == False) &
            (df["career_seasons"].notna()) &
            (df["career_seasons"] >= udfa_threshold)
        )
        df.loc[success_mask, "drafted_label"] = "Undrafted NFL"
    return df

def resolve_measurement(df, label: str, use_proday: bool) -> pd.Series:
    combine_col, proday_col = MEASUREMENTS[label]
    if combine_col is None:
        return df[proday_col] if use_proday and proday_col else pd.Series(dtype=float)
    s = df[combine_col].copy()
    if use_proday and proday_col:
        s = s.combine_first(df[proday_col])
    return s

def measurement_source(df, label: str, use_proday: bool) -> pd.Series:
    combine_col, proday_col = MEASUREMENTS[label]
    if combine_col is None:
        return pd.Series(["Pro Day"] * len(df), index=df.index)
    has_combine = df[combine_col].notna()
    if use_proday and proday_col:
        has_proday = df[proday_col].notna()
        return pd.Series(
            np.where(has_combine, "Combine", np.where(has_proday, "Pro Day", "—")),
            index=df.index,
        )
    return pd.Series(np.where(has_combine, "Combine", "—"), index=df.index)

# ── 翻訳辞書 ─────────────────────────────────────────────────────────────────
_TR = {
    "EN": {
        "app_title":        "NFL Combine & Pro Day Explorer",
        "year_header":      "📅 Year",
        "year_range":       "Year range",
        "years_cap":        lambda s, e, n: f"{s}–{e}  ({n} years)",
        "pos_header":       "🏃 Position Group",
        "pos_select":       "Select positions",
        "pos_warn":         "⚠️ Select at least one position.",
        "meas_header":      "📏 Measurements",
        "x_axis":           "X axis",
        "y_axis":           "Y axis",
        "source_header":    "🔬 Data Source",
        "proday_toggle":    "Include Pro Day data",
        "proday_cap":       "Combine measurement takes priority when available.",
        "draft_header":     "🎯 Draft Status",
        "draft_show":       "Show",
        "draft_all":        "All players",
        "draft_drafted":    "Drafted only",
        "draft_undrafted":  "Undrafted only",
        "draft_nfl":        "NFL players (Drafted + Undrafted NFL)",
        "show_2026":        "⭐ Show 2026 Pre-Draft players",
        "show_2026_help":   "Display 2026 combine prospects as gold markers.",
        "udfa_header":      "🌟 Undrafted NFL Players",
        "udfa_slider":      "Min. NFL seasons to qualify as Undrafted NFL",
        "udfa_cap_on":      lambda n: f"≥ **{n}** NFL season{'s' if n > 1 else ''} → 🌟 Undrafted NFL",
        "udfa_cap_off":     "Undrafted NFL highlighting is **off** (threshold = 0)",
        "display_header":   "⚙️ Display",
        "marker_size":      "Marker size",
        "opacity":          "Opacity",
        "ellipse":          "Show 95% confidence ellipse",
        "stats_panel":      "Show statistics panel",
        "search_header":    "🔍 Player Search & Labels",
        "search_label":     "Search & highlight players",
        "search_ph":        "Type a name to search…",
        "search_help":      "Type to filter candidates, then click to highlight on the chart.",
        "all_labels":       "Show name labels for ALL visible players",
        "all_labels_help":  "Only recommended when ≤ 80 players are shown.",
        "tab_scatter":      "📊 Scatter Plot",
        "tab_histogram":    "📈 Histogram",
        "hist_split":       "Split Drafted / Undrafted",
        "hist_split_help":  "Show Drafted and Undrafted as separate overlapping histograms.",
        "show_2026_kde":    "Show 2026 KDE lines",
        "show_2026_kde_help": "2026 prospects shown as dashed KDE curves (per position) instead of histogram bars.",
        "stats_header":     "📊 Statistics by Position",
        "boxplot_label":    "📦 Box Plot: Drafted vs Undrafted by Position",
        "boxplot_info":     "Box plot comparison requires 'All players' filter.",
        "total_players":    "Total players",
        "drafted_metric":   "Drafted",
        "undrafted_metric": "Undrafted",
        "predraft_metric":  "⭐ 2026 Pre-Draft",
        "source_metric":    "Data source (X)",
        "density":          "Density",
        "footer_line1":     (
            "Data: NFL Combine (official) + Pro Day measurements  |  "
            "Draft data: nflverse (2006–2024) + manual (2025)  |  "
            "2026 players shown as ⭐ gold markers (pre-draft)  |  "
            "Combine preferred; Pro Day used as fallback when toggle is ON"
        ),
        "footer_line2":     (
            "Combine & Pro Day data sourced from "
            "[Roy Carpenter's nfl-draft-data](https://github.com/array-carpenter/nfl-draft-data), "
            "aggregating: NFL Combine API (official measurements, grades, projections)  |  "
            "Pro day results from various public sources  |  "
            "ESPN athlete IDs for cross-referencing with CFBD stats  |  "
            "NFLCombineResults.com"
        ),
    },
    "JP": {
        "app_title":        "NFL Combine & Pro-day 解析ツール",
        "year_header":      "📅 年度",
        "year_range":       "年度範囲",
        "years_cap":        lambda s, e, n: f"{s}–{e}  ({n} 年)",
        "pos_header":       "🏃 ポジション",
        "pos_select":       "ポジションを選択",
        "pos_warn":         "⚠️ ポジションを1つ以上選択してください。",
        "meas_header":      "📏 測定項目",
        "x_axis":           "X 軸",
        "y_axis":           "Y 軸",
        "source_header":    "🔬 データソース",
        "proday_toggle":    "Pro-dayデータを含める",
        "proday_cap":       "Combine計測値が優先されます。",
        "draft_header":     "🎯 ドラフト状況",
        "draft_show":       "表示対象",
        "draft_all":        "全選手",
        "draft_drafted":    "指名あり",
        "draft_undrafted":  "指名なし",
        "draft_nfl":        "NFL選手（指名あり + Undrafted NFL）",
        "show_2026":        "⭐ 2026 プレドラフト選手を表示",
        "show_2026_help":   "2026年Combine参加者をゴールドマーカーで表示します。",
        "udfa_header":      "🌟 Undrafted NFL選手",
        "udfa_slider":      "Undrafted NFLとみなす最低NFLシーズン数",
        "udfa_cap_on":      lambda n: f"≥ **{n}** シーズン → 🌟 Undrafted NFL",
        "udfa_cap_off":     "Undrafted NFL ハイライトは **オフ** (しきい値 = 0)",
        "display_header":   "⚙️ 表示設定",
        "marker_size":      "マーカーサイズ",
        "opacity":          "不透明度",
        "ellipse":          "95% 信頼楕円を表示",
        "stats_panel":      "統計パネルを表示",
        "search_header":    "🔍 選手検索 & ラベル",
        "search_label":     "選手を検索・ハイライト",
        "search_ph":        "名前を入力…",
        "search_help":      "入力で候補を絞り込み、クリックでハイライト。",
        "all_labels":       "表示中の全選手名を表示",
        "all_labels_help":  "80人以下のときのみ推奨。",
        "tab_scatter":      "📊 散布図",
        "tab_histogram":    "📈 ヒストグラム",
        "hist_split":       "指名あり / なしを分けて表示",
        "hist_split_help":  "ドラフト指名あり・なしを別々のヒストグラムで重ね表示。",
        "show_2026_kde":    "2026 KDE ラインを表示",
        "show_2026_kde_help": "2026年プロスペクトをバーではなく点線KDE曲線（ポジション別）で表示。",
        "stats_header":     "📊 ポジション別統計",
        "boxplot_label":    "📦 ボックスプロット：指名あり vs 指名なし",
        "boxplot_info":     "ボックスプロットは「全選手」フィルター時のみ表示。",
        "total_players":    "表示選手数",
        "drafted_metric":   "指名あり",
        "undrafted_metric": "指名なし",
        "predraft_metric":  "⭐ 2026 プレドラフト",
        "source_metric":    "データソース (X)",
        "density":          "密度",
        "footer_line1":     (
            "データ: NFL Combine（公式）+ Pro-day計測  |  "
            "ドラフトデータ: nflverse (2006–2024) + 手動入力 (2025)  |  "
            "2026年選手はゴールドマーカーで表示（未ドラフト）  |  "
            "Combine優先・トグルON時はPro-dayをフォールバック"
        ),
        "footer_line2":     (
            "Combine & Pro-dayデータは "
            "[Roy Carpenter's nfl-draft-data](https://github.com/array-carpenter/nfl-draft-data) より取得。"
            "収録元: NFL Combine API（公式計測・グレード・プロジェクション）  |  "
            "各種公開ソースによるPro-day記録  |  "
            "CFBDとの照合用ESPNアスリートID  |  "
            "NFLCombineResults.com"
        ),
    },
}

df_all = load_data()

# ════════════════════════════════════════════════════════════════════════════
# サイドバー
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # 言語切替
    lang = st.radio("", ["EN", "JP"], index=0, horizontal=True,
                    label_visibility="collapsed")
    T = _TR[lang]

    st.title("🏈 NFL Combine Explorer")
    st.markdown("---")

    # 年度
    st.subheader(T["year_header"])
    all_years = sorted(df_all["year"].unique())
    year_range = st.slider(
        T["year_range"],
        min_value=int(min(all_years)),
        max_value=int(max(all_years)),
        value=(2006, 2025),
        step=1,
    )
    selected_years = list(range(year_range[0], year_range[1] + 1))
    st.caption(T["years_cap"](year_range[0], year_range[1], len(selected_years)))

    st.markdown("---")

    # ポジション
    st.subheader(T["pos_header"])
    selected_pos = st.multiselect(
        T["pos_select"],
        options=POS_GROUP_ORDER,
        default=["WR", "TE", "RB"],
    )
    if not selected_pos:
        st.warning(T["pos_warn"])
        st.stop()

    st.markdown("---")

    # 測定項目
    st.subheader(T["meas_header"])
    meas_labels = list(MEASUREMENTS.keys())
    x_label = st.selectbox(T["x_axis"], meas_labels, index=meas_labels.index("Weight (lbs)"))
    y_label = st.selectbox(T["y_axis"], meas_labels, index=meas_labels.index("Height (in)"))

    st.markdown("---")

    # データソース
    st.subheader(T["source_header"])
    use_proday = st.toggle(T["proday_toggle"], value=True)
    st.caption(T["proday_cap"])

    st.markdown("---")

    # 選手検索 & ラベル
    st.subheader(T["search_header"])
    all_names_df = df_all[["player", "year", "position", "college"]].drop_duplicates("player").copy()
    all_names_df["_label"] = (
        all_names_df["player"] + "  ("
        + all_names_df["position"].fillna("?") + ", "
        + all_names_df["year"].astype(str) + ")"
    )
    label_to_player = dict(zip(all_names_df["_label"], all_names_df["player"]))
    highlighted_labels = st.multiselect(
        T["search_label"],
        options=sorted(all_names_df["_label"].tolist()),
        default=[],
        placeholder=T["search_ph"],
        help=T["search_help"],
    )
    highlighted_players = [label_to_player[l] for l in highlighted_labels]
    show_all_labels = st.toggle(T["all_labels"], value=False, help=T["all_labels_help"])

    st.markdown("---")

    # ドラフトフィルター
    st.subheader(T["draft_header"])
    _draft_labels = [T["draft_all"], T["draft_drafted"], T["draft_undrafted"], T["draft_nfl"]]
    _draft_keys   = ["all", "drafted", "undrafted", "nfl"]
    _sel_label    = st.radio(T["draft_show"], _draft_labels, index=0)
    draft_filter  = _draft_keys[_draft_labels.index(_sel_label)]

    show_2026 = st.toggle(T["show_2026"], value=True, help=T["show_2026_help"])

    # UDFA 成功しきい値
    if HAS_CAREER:
        st.markdown("---")
        st.subheader(T["udfa_header"])
        udfa_threshold = st.slider(
            T["udfa_slider"],
            min_value=0, max_value=6, value=0,
            help="Undrafted players with ≥ N NFL seasons are shown as 🌟 green triangles.\nSet to 0 to disable.",
        )
        if udfa_threshold > 0:
            st.caption(T["udfa_cap_on"](udfa_threshold))
        else:
            st.caption(T["udfa_cap_off"])
    else:
        udfa_threshold = 0

    # 表示設定
    st.markdown("---")
    st.subheader(T["display_header"])
    marker_size  = st.slider(T["marker_size"], 3, 12, 5)
    marker_alpha = st.slider(T["opacity"], 0.1, 1.0, 0.65, 0.05)
    show_ellipse = st.toggle(T["ellipse"], value=False)
    show_stats   = st.toggle(T["stats_panel"], value=True)

# ════════════════════════════════════════════════════════════════════════════
# 共通データ絞り込み
# ════════════════════════════════════════════════════════════════════════════
df_labeled = apply_udfa_label(df_all, udfa_threshold)

df_f = df_labeled[
    df_labeled["year"].isin(selected_years) &
    df_labeled["pos_group"].isin(selected_pos)
].copy()

if draft_filter == "drafted":
    df_f = df_f[df_f["drafted"] == True]
elif draft_filter == "undrafted":
    df_f = df_f[df_f["drafted"] == False]
elif draft_filter == "nfl":
    _nfl_thr = max(udfa_threshold, 1)
    if HAS_CAREER:
        _nfl_mask = (df_f["drafted"] == True) | (
            (df_f["drafted"] == False) &
            df_f["career_seasons"].notna() &
            (df_f["career_seasons"] >= _nfl_thr)
        )
    else:
        _nfl_mask = df_f["drafted"] == True
    df_f = df_f[_nfl_mask]

# X 軸計測値を解決（散布図・ヒストグラム共通）
df_f["_x"]     = resolve_measurement(df_f, x_label, use_proday)
df_f["_x_src"] = measurement_source(df_f, x_label, use_proday)
df_f_x = df_f[df_f["_x"].notna()].copy()

# 2026 Pre-Draft を分離
_unknown_mask = df_f_x["drafted_label"] == "Unknown"
df_2026_base  = df_f_x[_unknown_mask].copy()
df_base       = df_f_x[~_unknown_mask].copy()

# ── ヘッダー ───────────────────────────────────────────────────────────────────
st.title(T["app_title"])
col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns(5)
with col_h1:
    total_shown = len(df_base) + (len(df_2026_base) if show_2026 else 0)
    st.metric(T["total_players"], f"{total_shown:,}")
with col_h2:
    drafted_n = (df_base["drafted"] == True).sum()
    st.metric(T["drafted_metric"], f"{drafted_n:,}")
with col_h3:
    udfa_success_n = (df_base["drafted_label"] == "Undrafted NFL").sum()
    if HAS_CAREER and udfa_threshold > 0:
        st.metric("🌟 Undrafted NFL", f"{udfa_success_n:,}",
                  delta=f"≥{udfa_threshold}yr" if udfa_success_n > 0 else None)
    else:
        st.metric(T["undrafted_metric"], f"{(df_base['drafted']==False).sum():,}")
with col_h4:
    predraft_n = len(df_2026_base)
    _delta_2026 = "shown" if (show_2026 and predraft_n > 0) else "hidden" if (not show_2026 and predraft_n > 0) else None
    st.metric(T["predraft_metric"], f"{predraft_n:,}", delta=_delta_2026)
with col_h5:
    combine_n = (df_base["_x_src"] == "Combine").sum()
    proday_n  = (df_base["_x_src"] == "Pro Day").sum()
    st.metric(T["source_metric"], f"C {combine_n:,} / PD {proday_n:,}")

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════
# タブ
# ════════════════════════════════════════════════════════════════════════════
tab_sc, tab_hi = st.tabs([T["tab_scatter"], T["tab_histogram"]])

# ────────────────────────────────────────────────────────────────────────────
# 散布図タブ
# ────────────────────────────────────────────────────────────────────────────
with tab_sc:
    # Y 軸計測値を解決
    df_plot = df_base.copy()
    df_plot["_y"]     = resolve_measurement(df_plot, y_label, use_proday)
    df_plot["_y_src"] = measurement_source(df_plot, y_label, use_proday)
    df_plot = df_plot[df_plot["_y"].notna()].copy()

    df_2026_plot = df_2026_base.copy()
    df_2026_plot["_y"]     = resolve_measurement(df_2026_plot, y_label, use_proday)
    df_2026_plot["_y_src"] = measurement_source(df_2026_plot, y_label, use_proday)

    color_map  = {p: POS_COLORS[p] for p in selected_pos}
    symbol_map = {
        "Drafted":       "circle",
        "Undrafted NFL": "triangle-up",
        "Undrafted":     "x",
        "Unknown":      "diamond",
    }

    hover_cols = {
        "player": True, "year": True, "college": True,
        "drafted_label": True, "draft_round": True,
        "draft_pick": True, "draft_team": True, "_x_src": True,
    }
    if use_proday:
        hover_cols["_y_src"] = True
    if HAS_CAREER:
        hover_cols["career_seasons"]   = True
        hover_cols["nfl_rookie_season"] = True
        hover_cols["nfl_last_season"]   = True

    fig = px.scatter(
        df_plot,
        x="_x", y="_y",
        color="pos_group",
        symbol="drafted_label",
        color_discrete_map=color_map,
        symbol_map=symbol_map,
        hover_data=hover_cols,
        labels={
            "_x": x_label, "_y": y_label,
            "pos_group": "Position", "drafted_label": "Status",
            "_x_src": "X source", "_y_src": "Y source",
            "player": "Player", "year": "Year",
            "college": "College", "draft_round": "Round",
            "draft_pick": "Pick", "draft_team": "Team",
            "career_seasons": "NFL Seasons",
            "nfl_rookie_season": "Rookie Year",
            "nfl_last_season": "Last Season",
        },
        opacity=marker_alpha,
    )
    fig.update_traces(marker_size=marker_size)

    # 95% 信頼楕円
    if show_ellipse and draft_filter == "all":
        for pos in selected_pos:
            for drafted_val, linestyle in [(True, "solid"), (False, "dot")]:
                sub = df_plot[
                    (df_plot["pos_group"] == pos) &
                    (df_plot["drafted"] == drafted_val)
                ][["_x", "_y"]].dropna()
                if len(sub) < 10:
                    continue
                cov  = np.cov(sub["_x"], sub["_y"])
                mean = sub[["_x", "_y"]].mean().values
                eigvals, eigvecs = np.linalg.eigh(cov)
                order = eigvals.argsort()[::-1]
                eigvals, eigvecs = eigvals[order], eigvecs[:, order]
                scale  = np.sqrt(5.991)
                angle  = np.linspace(0, 2 * np.pi, 100)
                ellipse = np.column_stack([np.cos(angle), np.sin(angle)])
                ellipse = ellipse @ np.diag(np.sqrt(eigvals) * scale) @ eigvecs.T + mean
                fig.add_trace(go.Scatter(
                    x=ellipse[:, 0], y=ellipse[:, 1],
                    mode="lines",
                    line=dict(color=POS_COLORS[pos], width=1.5, dash=linestyle),
                    name=f"{pos} {'D' if drafted_val else 'U'} 95%CI",
                    showlegend=False, hoverinfo="skip",
                ))

    # 2026 Pre-Draft オーバーレイ
    def _make_hover_2026(row):
        x_val = f"{row['_x']:.3f}" if pd.notna(row["_x"]) else "—"
        y_val = f"{row['_y']:.3f}" if pd.notna(row.get("_y")) else "—"
        src_x = row.get("_x_src", "—")
        src_y = row.get("_y_src", "—") if use_proday else ""
        src_line = f"Source: {src_x} / {src_y}" if use_proday else f"Source: {src_x}"
        return (
            f"<b>⭐ {row['player']}</b>  [2026 Pre-Draft]<br>"
            f"{row.get('position', '?')} • {row.get('college', '')}<br>"
            f"{x_label}: {x_val}<br>"
            f"{y_label}: {y_val}<br>"
            f"{src_line}"
        )

    if show_2026 and not df_2026_plot.empty:
        _df2026_valid = df_2026_plot[df_2026_plot["_y"].notna()]
        if not _df2026_valid.empty:
            # ポジション別に色分け（diamond-open で歴史データと区別）
            for pos in selected_pos:
                _sub2026 = _df2026_valid[_df2026_valid["pos_group"] == pos]
                if _sub2026.empty:
                    continue
                hover_2026 = _sub2026.apply(_make_hover_2026, axis=1)
                fig.add_trace(go.Scatter(
                    x=_sub2026["_x"], y=_sub2026["_y"],
                    mode="markers",
                    name=f"2026 {pos} ⭐",
                    marker=dict(
                        symbol="diamond-open",
                        size=marker_size * 1.6,
                        color=POS_COLORS[pos],
                        opacity=0.90,
                        line=dict(color=POS_COLORS[pos], width=2),
                    ),
                    hovertext=hover_2026, hoverinfo="text",
                    showlegend=True,
                ))
            # フィルター外ポジションの2026選手（グレーで表示）
            _sub2026_other = _df2026_valid[~_df2026_valid["pos_group"].isin(selected_pos)]
            if not _sub2026_other.empty:
                hover_2026_other = _sub2026_other.apply(_make_hover_2026, axis=1)
                fig.add_trace(go.Scatter(
                    x=_sub2026_other["_x"], y=_sub2026_other["_y"],
                    mode="markers",
                    name="2026 Other ⭐",
                    marker=dict(
                        symbol="diamond-open",
                        size=marker_size * 1.4,
                        color=PREDRAFT_COLOR,
                        opacity=0.55,
                        line=dict(color=PREDRAFT_COLOR, width=1.5),
                    ),
                    hovertext=hover_2026_other, hoverinfo="text",
                    showlegend=True,
                ))

    # ハイライト選手（ポジションフィルター外でも表示）
    if highlighted_players:
        # 現在の表示範囲（ポジションフィルター適用済み）
        _all_visible = pd.concat(
            [df_plot, df_2026_plot[df_2026_plot["_y"].notna()]], ignore_index=True
        ) if not df_2026_plot.empty else df_plot.copy()

        # 全データから年度・ポジションフィルターを無視して検索（x/y両方必要）
        _df_ext = apply_udfa_label(df_all, udfa_threshold).copy()
        if draft_filter == "drafted":
            _df_ext = _df_ext[_df_ext["drafted"] == True]
        elif draft_filter == "undrafted":
            _df_ext = _df_ext[_df_ext["drafted"] == False]
        elif draft_filter == "nfl":
            _nfl_thr_ext = max(udfa_threshold, 1)
            if HAS_CAREER:
                _nfl_mask_ext = (_df_ext["drafted"] == True) | (
                    (_df_ext["drafted"] == False) &
                    _df_ext["career_seasons"].notna() &
                    (_df_ext["career_seasons"] >= _nfl_thr_ext)
                )
            else:
                _nfl_mask_ext = _df_ext["drafted"] == True
            _df_ext = _df_ext[_nfl_mask_ext]
        _df_ext["_x"] = resolve_measurement(_df_ext, x_label, use_proday)
        _df_ext["_y"] = resolve_measurement(_df_ext, y_label, use_proday)
        _df_ext = _df_ext[_df_ext["_x"].notna() & _df_ext["_y"].notna()].copy()

        # 3グループに分類
        # 1. 現在のフィルター内（pos + year）→ 通常表示済み
        # 2. ポジション外 or 年度外 → 追加プロット（違うマーカーで区別）
        # 3. データなし → 警告
        _already      = set(_all_visible["player"].values)
        hl_in_view    = _all_visible[_all_visible["player"].isin(highlighted_players)].copy()
        hl_outside    = _df_ext[
            _df_ext["player"].isin(highlighted_players) &
            ~_df_ext["player"].isin(_already)
        ].copy()
        _found_all    = _already | set(_df_ext["player"].values)
        hl_not_found  = [p for p in highlighted_players if p not in _found_all]

        def _hl_hover(row, note=""):
            draft_info = ""
            if pd.notna(row.get("draft_round")):
                draft_info = f"  Rd{int(row['draft_round'])} #{int(row['draft_pick'])} {row['draft_team']}"
            elif row.get("drafted") == False:
                draft_info = "  (Undrafted)"
            return (
                f"<b>{row['player']}</b>{note}<br>"
                f"{row.get('position','?')}  {int(row['year'])}<br>"
                f"{row.get('college','')}{draft_info}<br>"
                f"X: {row['_x']:.3f}  Y: {row['_y']:.3f}"
            )

        # グループ1: フィルター内（solid circle）
        for _, row in hl_in_view.iterrows():
            pos_c = POS_COLORS.get(row.get("pos_group", ""), "#FF6F00")
            fig.add_trace(go.Scatter(
                x=[row["_x"]], y=[row["_y"]],
                mode="markers+text",
                marker=dict(size=marker_size * 3.2, color=pos_c, opacity=0.95,
                            line=dict(color="white", width=2.5), symbol="circle"),
                text=[row["player"]], textposition="top center",
                textfont=dict(size=11, color="#E6EDF3", family="Geist, sans-serif"),
                name=row["player"],
                hovertext=_hl_hover(row), hoverinfo="text", showlegend=True,
            ))

        # グループ2: フィルター外（circle-open + 注記）
        for _, row in hl_outside.iterrows():
            pos_c = POS_COLORS.get(row.get("pos_group", ""), "#FF6F00")
            in_year = int(row["year"]) in selected_years
            in_pos  = row.get("pos_group") in selected_pos
            notes   = []
            if not in_pos:
                notes.append(row.get("position", "?"))
            if not in_year:
                notes.append(f"{int(row['year'])}")
            note_str = f"  [{', '.join(notes)} — outside filter]" if notes else ""
            fig.add_trace(go.Scatter(
                x=[row["_x"]], y=[row["_y"]],
                mode="markers+text",
                marker=dict(size=marker_size * 3.2, color=pos_c, opacity=0.90,
                            line=dict(color="white", width=2, dash="dot"), symbol="circle-open"),
                text=[row["player"]], textposition="top center",
                textfont=dict(size=11, color="#E6EDF3", family="Geist, sans-serif"),
                name=f"{row['player']} ({row.get('position','?')}, {int(row['year'])})",
                hovertext=_hl_hover(row, note_str), hoverinfo="text", showlegend=True,
            ))

        # グループ3: データなし
        for pname in hl_not_found:
            found = df_all[df_all["player"] == pname]
            if found.empty:
                st.warning(f"⚠️ **{pname}**: not found in dataset.")
            else:
                row0 = found.iloc[0]
                reasons = []
                val_x = resolve_measurement(found, x_label, use_proday).iloc[0]
                val_y = resolve_measurement(found, y_label, use_proday).iloc[0]
                if pd.isna(val_x): reasons.append(f"no {x_label} data")
                if pd.isna(val_y): reasons.append(f"no {y_label} data")
                reason_str = ";  ".join(reasons) if reasons else "data unavailable"
                st.info(f"ℹ️ **{pname}** ({row0.get('position','?')}, {int(row0['year'])}) — {reason_str}.")

    # 全選手ラベル（最後に追加してすべてのマーカーの前面に表示）
    if show_all_labels:
        label_df = pd.concat([df_plot, df_2026_plot[df_2026_plot["_y"].notna()]], ignore_index=True) if (show_2026 and not df_2026_plot.empty) else df_plot.copy()
        if len(label_df) > 80:
            st.warning(f"⚠️ {len(label_df)} players visible — labels hidden (reduce filters to ≤ 80).")
        else:
            fig.add_trace(go.Scatter(
                x=label_df["_x"], y=label_df["_y"],
                mode="text", text=label_df["player"],
                textposition="top center",
                textfont=dict(size=9, color="#C9D1D9"),
                showlegend=False, hoverinfo="skip", name="labels_all",
            ))

    _plot_layout = dict(
        plot_bgcolor="#161B22", paper_bgcolor="#0D1117",
        font=dict(color="#C9D1D9", family="Geist, sans-serif"),
        hoverlabel=dict(bgcolor="#1C2128", bordercolor="#30363D",
                        font=dict(color="#E6EDF3", size=12, family="Geist, sans-serif")),
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0,
                    bgcolor="rgba(22,27,34,0.85)", bordercolor="#30363D", borderwidth=1,
                    font=dict(size=11, color="#C9D1D9", family="Geist, sans-serif")),
        xaxis=dict(gridcolor="#21262D", linecolor="#30363D", zerolinecolor="#30363D",
                   tickfont=dict(color="#6E7681", size=11), title_font=dict(color="#8B949E")),
        yaxis=dict(gridcolor="#21262D", linecolor="#30363D", zerolinecolor="#30363D",
                   tickfont=dict(color="#6E7681", size=11), title_font=dict(color="#8B949E")),
        margin=dict(t=20, b=160, l=50, r=20),
    )

    fig.update_layout(
        xaxis_title=x_label, yaxis_title=y_label, height=660,
        **_plot_layout,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#21262D")
    fig.update_yaxes(showgrid=True, gridcolor="#21262D")

    # ダウンロードボタン（グラフ上部・右寄せ、遅延生成）
    _pos_str = "+".join(selected_pos)
    _fname   = f"NFL_{_pos_str}_{x_label.split(' (')[0]}_vs_{y_label.split(' (')[0]}.png".replace(" ", "_")
    _, _btn_col = st.columns([5, 1])
    with _btn_col:
        try:
            import kaleido  # noqa: F401 — available check
            if st.button("Download Chart", use_container_width=True, key="dl_prepare"):
                with st.spinner("Preparing…"):
                    _img_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
                st.download_button(
                    "Save PNG",
                    data=_img_bytes,
                    file_name=_fname,
                    mime="image/png",
                    use_container_width=True,
                    key="dl_save",
                )
        except Exception:
            pass  # kaleido 未インストール時はスキップ

    st.plotly_chart(fig, use_container_width=True)

    # 統計パネル
    if show_stats:
        st.markdown("---")
        st.subheader(T["stats_header"])
        stat_cols = st.columns(min(len(selected_pos), 4))
        for i, pos in enumerate(selected_pos):
            with stat_cols[i % len(stat_cols)]:
                sub_pos = df_plot[df_plot["pos_group"] == pos]
                d_x     = sub_pos[sub_pos["drafted"] == True]["_x"].dropna()
                us_x    = sub_pos[sub_pos["drafted_label"] == "Undrafted NFL"]["_x"].dropna()
                u_x     = sub_pos[(sub_pos["drafted"] == False) & (sub_pos["drafted_label"] != "Undrafted NFL")]["_x"].dropna()
                all_u_x = sub_pos[sub_pos["drafted"] == False]["_x"].dropna()

                st.markdown(f"**{pos}**  <span style='color:{POS_COLORS[pos]};font-size:18px'>●</span>",
                            unsafe_allow_html=True)

                def _sig_html(a, b):
                    if len(a) < 5 or len(b) < 5:
                        return '<span class="sig-badge" style="background:#ccc;color:#666">n/a</span>', None
                    _, pv = stats.mannwhitneyu(a, b, alternative="two-sided")
                    sg = "***" if pv < 0.001 else "**" if pv < 0.01 else "*" if pv < 0.05 else "ns"
                    sc = {"***": "#d32f2f", "**": "#e64a19", "*": "#f57c00", "ns": "#888"}[sg]
                    return f'<span class="sig-badge" style="background:{sc};color:white">{sg}</span>', pv

                x_name = x_label.split(" (")[0]
                lines  = [f"<b>X: {x_name}</b>"]
                lines.append(f"  Drafted  n={len(d_x)}, med={d_x.median():.3f}" if len(d_x) else "  Drafted  n=0")
                if HAS_CAREER and udfa_threshold > 0:
                    lines.append(f"  🌟 UDFA n={len(us_x)}, med={us_x.median():.3f}" if len(us_x) else "  🌟 UDFA n=0")
                    lines.append(f"  Undrafted n={len(u_x)}, med={u_x.median():.3f}" if len(u_x) else "  Undrafted n=0")
                else:
                    lines.append(f"  Undrafted n={len(all_u_x)}, med={all_u_x.median():.3f}" if len(all_u_x) else "  Undrafted n=0")

                sh, pval = _sig_html(d_x, all_u_x)
                if pval is not None:
                    delta = d_x.median() - all_u_x.median() if len(d_x) and len(all_u_x) else 0
                    lines.append(f"  D vs U Δ: {delta:+.3f}  {sh}")
                    lines.append(f"  p = {pval:.4f}")

                if HAS_CAREER and udfa_threshold > 0 and len(us_x) >= 5 and len(u_x) >= 5:
                    sh_us, _ = _sig_html(us_x, u_x)
                    lines.append(f"  🌟 vs U Δ: {us_x.median()-u_x.median():+.3f}  {sh_us}")

                d_y     = sub_pos[sub_pos["drafted"] == True]["_y"].dropna()
                all_u_y = sub_pos[sub_pos["drafted"] == False]["_y"].dropna()
                y_name  = y_label.split(" (")[0]
                lines  += [f"<b>Y: {y_name}</b>"]
                lines.append(f"  Drafted  n={len(d_y)}, med={d_y.median():.3f}" if len(d_y) else "  Drafted  n=0")
                lines.append(f"  Undrafted n={len(all_u_y)}, med={all_u_y.median():.3f}" if len(all_u_y) else "  Undrafted n=0")
                sh_y, pval_y = _sig_html(d_y, all_u_y)
                if pval_y is not None:
                    lines.append(f"  D vs U Δ: {d_y.median()-all_u_y.median():+.3f}  {sh_y}")

                both = sub_pos[["_x", "_y"]].dropna()
                if len(both) >= 5:
                    r, pr = stats.pearsonr(both["_x"], both["_y"])
                    lines.append(f"<b>Pearson r = {r:.3f}</b>  (p={pr:.3f})")

                st.markdown(
                    f'<div class="metric-box" style="border-top: 3px solid {POS_COLORS[pos]}">'
                    + "<br>".join(lines) + "</div>",
                    unsafe_allow_html=True,
                )

    # ボックスプロット
    st.markdown("---")
    with st.expander(T["boxplot_label"], expanded=False):
        if draft_filter == "all":
            fig_box = go.Figure()
            for pos in selected_pos:
                for drafted_val, lbl, pat in [
                    (True,  "Drafted",   ""),
                    (False, "Undrafted", "/"),
                ]:
                    sub = df_plot[(df_plot["pos_group"] == pos) & (df_plot["drafted"] == drafted_val)]["_x"].dropna()
                    if len(sub) < 3:
                        continue
                    fig_box.add_trace(go.Box(
                        y=sub,
                        x=[pos] * len(sub),
                        name=lbl,
                        legendgroup=lbl,
                        showlegend=(pos == selected_pos[0]),
                        marker_color=POS_COLORS[pos],
                        fillcolor=POS_COLORS[pos] if drafted_val else "rgba(0,0,0,0)",
                        line_color=POS_COLORS[pos],
                        opacity=0.85 if drafted_val else 0.6,
                        boxmean="sd",
                    ))
            fig_box.update_layout(
                boxmode="group",
                yaxis_title=x_label, height=480,
                showlegend=True,
                **{k: v for k, v in _plot_layout.items() if k != "margin"},
                margin=dict(t=40, b=60),
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info(T["boxplot_info"])

# ────────────────────────────────────────────────────────────────────────────
# ヒストグラムタブ
# ────────────────────────────────────────────────────────────────────────────
with tab_hi:
    _hcol1, _hcol2 = st.columns(2)
    with _hcol1:
        hist_split = st.toggle(T["hist_split"], value=False, help=T["hist_split_help"])
    with _hcol2:
        show_2026_kde = st.toggle(T["show_2026_kde"], value=True, help=T["show_2026_kde_help"])

    fig_hi = go.Figure()

    for pos in selected_pos:
        sub_all = df_base[df_base["pos_group"] == pos]["_x"].dropna()
        sub_d   = df_base[(df_base["pos_group"] == pos) & (df_base["drafted"] == True)]["_x"].dropna()
        sub_u   = df_base[(df_base["pos_group"] == pos) & (df_base["drafted"] == False)]["_x"].dropna()

        if not hist_split:
            if len(sub_all) > 0:
                fig_hi.add_trace(go.Histogram(
                    x=sub_all, name=pos,
                    opacity=0.6, marker_color=POS_COLORS[pos],
                    histnorm="probability density", nbinsx=30,
                ))
        else:
            if len(sub_d) > 0:
                fig_hi.add_trace(go.Histogram(
                    x=sub_d, name=f"{pos} Drafted",
                    opacity=0.75, marker_color=POS_COLORS[pos],
                    histnorm="probability density", nbinsx=30,
                ))
            if len(sub_u) > 0:
                fig_hi.add_trace(go.Histogram(
                    x=sub_u, name=f"{pos} Undrafted",
                    opacity=0.35, marker_color=POS_COLORS[pos],
                    marker_line=dict(color=POS_COLORS[pos], width=1.5),
                    histnorm="probability density", nbinsx=30,
                ))

    # 2026: KDE ライン（ポジション別、バーではなく曲線）
    if show_2026 and show_2026_kde and not df_2026_base.empty:
        _x_min = df_base["_x"].min() if len(df_base) else df_2026_base["_x"].min()
        _x_max = df_base["_x"].max() if len(df_base) else df_2026_base["_x"].max()
        x_range = np.linspace(_x_min, _x_max, 400)

        for pos in selected_pos:
            sub_2026_pos = df_2026_base[df_2026_base["pos_group"] == pos]["_x"].dropna()
            if len(sub_2026_pos) < 5:
                continue
            kde = gaussian_kde(sub_2026_pos.values, bw_method=0.5)
            fig_hi.add_trace(go.Scatter(
                x=x_range, y=kde(x_range),
                mode="lines",
                name=f"2026 {pos} ⭐",
                line=dict(color=POS_COLORS[pos], width=2.5, dash="dash"),
                opacity=0.85,
            ))

    # ハイライト選手を縦線で表示
    if highlighted_players:
        _all_hist = pd.concat([df_base, df_2026_base], ignore_index=True) if not df_2026_base.empty else df_base
        hl_in_hist = _all_hist[_all_hist["player"].isin(highlighted_players)].copy()
        for _, row in hl_in_hist.iterrows():
            line_color = PREDRAFT_BORDER if row["drafted_label"] == "Unknown" else POS_COLORS.get(row.get("pos_group", ""), "#FF6F00")
            fig_hi.add_vline(
                x=row["_x"],
                line=dict(color=line_color, width=2, dash="dash"),
                annotation_text=f"{row['player']} ({row['_x']:.2f})",
                annotation_position="top",
                annotation_font_size=10,
                annotation_font_color="#C9D1D9",
            )

    fig_hi.update_layout(
        barmode="overlay",
        title=dict(
            text=f"{x_label} — Distribution by Position"
                 + (" (Drafted / Undrafted split)" if hist_split else ""),
            font=dict(size=13, color="#6E7681", family="Geist, sans-serif"),
            x=0, xanchor="left",
        ),
        xaxis_title=x_label,
        yaxis_title=T["density"],
        height=520,
        plot_bgcolor="#161B22", paper_bgcolor="#0D1117",
        font=dict(color="#C9D1D9", family="Geist, sans-serif"),
        hoverlabel=dict(bgcolor="#1C2128", bordercolor="#30363D",
                        font=dict(color="#E6EDF3", size=12, family="Geist, sans-serif")),
        legend=dict(
            orientation="h",
            bgcolor="rgba(22,27,34,0.85)", bordercolor="#30363D", borderwidth=1,
            font=dict(size=11, color="#C9D1D9", family="Geist, sans-serif"),
        ),
        xaxis=dict(gridcolor="#21262D", linecolor="#30363D",
                   tickfont=dict(color="#6E7681", size=11), title_font=dict(color="#8B949E")),
        yaxis=dict(gridcolor="#21262D", linecolor="#30363D",
                   tickfont=dict(color="#6E7681", size=11), title_font=dict(color="#8B949E")),
        margin=dict(t=60, b=40, l=50, r=20),
    )

    st.plotly_chart(fig_hi, use_container_width=True)

# ── フッター ───────────────────────────────────────────────────────────────────
st.markdown("---")
_career_note = (
    "  |  Career data: nflverse players.csv  |  "
    "🌟 Undrafted NFL = undrafted player with ≥ N NFL seasons"
    if HAS_CAREER else ""
)
st.caption(T["footer_line1"] + _career_note)
st.caption(T["footer_line2"])
