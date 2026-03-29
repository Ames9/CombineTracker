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

# ── テーマ定数 ────────────────────────────────────────────────────────────────
THEME = {
    "bg":       "#0D1117",
    "card_bg":  "#161B22",
    "border":   "#30363D",
    "grid":     "#21262D",
    "text":     "#C9D1D9",
    "text_bright": "#E6EDF3",
    "muted":    "#6E7681",
    "label":    "#8B949E",
    "accent":   "#58A6FF",
    "font":     "Geist, sans-serif",
}

DRAFT_ROUND_COLORS = {
    1: "#E53935", 2: "#FB8C00", 3: "#FDD835", 4: "#43A047",
    5: "#00ACC1", 6: "#1E88E5", 7: "#8E24AA", "UDFA": "#6E7681",
}

# 低いほうが良い測定項目（タイム系）
LOWER_IS_BETTER = {
    "40-Yard Dash (s)", "10-Yard Split (s)",
    "3-Cone Drill (s)", "20-Yd Shuttle (s)",
}

MIN_SAMPLES_ELLIPSE = 10
MIN_SAMPLES_STATS = 5
LABEL_WARN_THRESHOLD = 80
HIST_BINS = 30
KDE_BANDWIDTH = 0.5
MIN_KDE_SAMPLES = 5


def make_plot_layout(**overrides):
    """散布図・ヒストグラム共通のPlotlyレイアウト辞書を生成"""
    base = dict(
        plot_bgcolor=THEME["card_bg"], paper_bgcolor=THEME["bg"],
        font=dict(color=THEME["text"], family=THEME["font"]),
        hoverlabel=dict(bgcolor="#1C2128", bordercolor=THEME["border"],
                        font=dict(color=THEME["text_bright"], size=12, family=THEME["font"])),
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0,
                    bgcolor="rgba(22,27,34,0.85)", bordercolor=THEME["border"], borderwidth=1,
                    font=dict(size=11, color=THEME["text"], family=THEME["font"])),
        xaxis=dict(gridcolor=THEME["grid"], linecolor=THEME["border"], zerolinecolor=THEME["border"],
                   tickfont=dict(color=THEME["muted"], size=11), title_font=dict(color=THEME["label"])),
        yaxis=dict(gridcolor=THEME["grid"], linecolor=THEME["border"], zerolinecolor=THEME["border"],
                   tickfont=dict(color=THEME["muted"], size=11), title_font=dict(color=THEME["label"])),
        margin=dict(t=20, b=160, l=50, r=20),
    )
    base.update(overrides)
    return base

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
    "NGS Scout Grade ★":        ("draft_grade",                 None),
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

@st.cache_data
def build_player_search_options(df):
    """選手検索ラベルリストをキャッシュ生成"""
    names_df = df[["player", "year", "position"]].drop_duplicates("player").copy()
    names_df["_label"] = (
        names_df["player"] + "  ("
        + names_df["position"].fillna("?") + ", "
        + names_df["year"].astype(str) + ")"
    )
    label_to_player = dict(zip(names_df["_label"], names_df["player"]))
    sorted_labels = sorted(names_df["_label"].tolist())
    return sorted_labels, label_to_player


def resolve_measurement(df, label: str, use_proday: bool) -> pd.Series:
    combine_col, proday_col = MEASUREMENTS[label]
    if combine_col is None:
        return df[proday_col] if use_proday and proday_col else pd.Series(dtype=float)
    s = df[combine_col].copy()
    if use_proday and proday_col:
        s = s.combine_first(df[proday_col])
    return s


@st.cache_data
def compute_all_position_percentiles() -> dict:
    """全ポジション・全測定項目のドラフト指名選手分布をキャッシュ生成"""
    df = load_data()
    drafted = df[df["_drafted_base"] == "Drafted"]
    result = {}
    for pos in POS_GROUP_ORDER:
        sub = drafted[drafted["pos_group"] == pos]
        pos_dict = {}
        for label, (combine_col, proday_col) in MEASUREMENTS.items():
            col = combine_col or proday_col
            if col and col in sub.columns:
                vals = sub[col].dropna().values
                if len(vals) >= 10:
                    pos_dict[label] = vals
        result[pos] = pos_dict
    return result


def compute_position_percentiles(df_drafted, pos_group: str) -> dict:
    """ポジション別参照分布を返す（キャッシュ済みデータを利用）"""
    return _ALL_POS_PERCENTILES.get(pos_group, {})


def calc_percentile(value, reference_values, label: str) -> float | None:
    """value が reference_values 中で何パーセンタイルかを返す。低い方が良いなら反転"""
    from scipy.stats import percentileofscore as _pos
    if len(reference_values) < 5:
        return None
    pct = _pos(reference_values, value, kind="mean")
    if label in LOWER_IS_BETTER:
        pct = 100.0 - pct
    return round(pct, 1)



def find_similar_players(player_row: pd.Series, df_hist: pd.DataFrame, pos_group: str, n: int = 8) -> pd.DataFrame:
    """z-scoreベースのユークリッド距離で類似選手をtop-n返す"""
    sub = df_hist[df_hist["pos_group"] == pos_group].copy()
    meas_cols = []
    for label, (combine_col, proday_col) in MEASUREMENTS.items():
        col = combine_col or proday_col
        if col and col in sub.columns:
            meas_cols.append((label, col))
    if not meas_cols:
        return pd.DataFrame()

    # 使用可能な列のみ（対象選手に値がある列）
    usable = []
    for label, col in meas_cols:
        pval = player_row.get(col)
        if pd.notna(pval) and sub[col].notna().sum() >= 10:
            usable.append((label, col))
    if len(usable) < 3:
        return pd.DataFrame()

    cols = [c for _, c in usable]
    labels = [l for l, _ in usable]
    means = sub[cols].mean()
    stds  = sub[cols].std().replace(0, 1)
    player_z = np.array([(player_row.get(c, np.nan) - means[c]) / stds[c] for c in cols])

    dists = []
    for idx, row in sub.iterrows():
        row_z = np.array([(row[c] - means[c]) / stds[c] for c in cols])
        mask = ~(np.isnan(player_z) | np.isnan(row_z))
        if mask.sum() < 3:
            continue
        dist = np.sqrt(np.mean((player_z[mask] - row_z[mask]) ** 2))
        dists.append((idx, dist))

    if not dists:
        return pd.DataFrame()
    dists.sort(key=lambda x: x[1])
    top_idx = [i for i, _ in dists[1:n+1]]  # 自分自身を除く
    result = sub.loc[top_idx].copy()
    result["_similarity"] = [1 / (1 + d) * 100 for _, d in dists[1:n+1]]
    return result

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


# ══════════════════════════════════════════════════════════════════════════════
# § Edge Rusher – Combine × Pro Performance Analysis
# ══════════════════════════════════════════════════════════════════════════════

# Combine metrics for Edge Rushers:  label → (combine_col, proday_col)
_ECM = {
    "Arm Length (in)":        ("combine_arm_length",          "pro_day_arm_length"),
    "Hand Size (in)":         ("combine_hand_size",           "pro_day_hand_size"),
    "Height (in)":            ("combine_height",              "pro_day_height"),
    "Weight (lbs)":           ("combine_weight",              "pro_day_weight"),
    "40-Yard Dash (s)":       ("combine_forty_yard_dash",     "pro_day_forty_yard_dash"),
    "10-Yard Split (s)":      ("combine_ten_yard_split",      "pro_day_ten_yard_split"),
    "Vertical Jump (in)":     ("combine_vertical_jump",       "pro_day_vertical_jump"),
    "Broad Jump (in)":        ("combine_broad_jump",          "pro_day_broad_jump"),
    "3-Cone Drill (s)":       ("combine_three_cone_drill",    "pro_day_three_cone_drill"),
    "20-Yd Shuttle (s)":      ("combine_twenty_yard_shuttle", "pro_day_twenty_yard_shuttle"),
    "Bench Press (reps)":     ("combine_bench_press",         "pro_day_bench_press"),
    "NGS Draft Grade":        ("draft_grade",                 None),
}
_ECM_LOWER_BETTER = {"40-Yard Dash (s)", "10-Yard Split (s)", "3-Cone Drill (s)", "20-Yd Shuttle (s)"}

# Pro metrics: label → (df_col, lower_is_better)
_PPM = {
    "QB Pressure Rate (career %)":          ("career_qbpr",          False),
    "QB Pressures / Season":                ("pressures_per_season", False),
    "QB Pressures (career total)":          ("total_qbp",            False),
    "Sacks / Season":                       ("sacks_per_season",     False),
    "Sacks (career total)":                 ("total_sacks",          False),
    "Get-Off Time avg (s)  ↓lower=better":  ("avg_get_off",          True),
    "Time-to-Pressure avg (s)  ↓lower":     ("avg_ttp",              True),
    "Pass Rush Snaps (career total)":       ("total_pr_snaps",       False),
}

# Known name mismatches between Combine CSV and NFL Pro API
_PR_NAME_CORRECTIONS = {
    "Alvin Dupree":       "Bud Dupree",
    "Alexander Okafor":   "Alex Okafor",
    "Joshua Hines-Allen": "Josh Hines-Allen",
    "Zachary Allen":      "Zach Allen",
    "Samuel Hubbard":     "Sam Hubbard",
    "William Anderson":   "Will Anderson",
    "DeMarcus Lawrence":  "Demarcus Lawrence",
    "Trenton Murphy":     "Trent Murphy",
    "Randall Gregory":    "Randy Gregory",
    "Victor Beasley":     "Vic Beasley",
    "Timothy Williams":   "Tim Williams",
    "Vincent Biegel":     "Vince Biegel",
    "Samuel Williams":    "Sam Williams",
    "Jeffrey Gunter":     "Jeff Gunter",
    "DeMario Davis":      "Demario Davis",
    "Matthew Milano":     "Matt Milano",
    "Steven Longa":       "Steve Longa",
    "La'Darius Hamilton": "Ladarius Hamilton",
}


@st.cache_data
def load_passrush_data() -> pd.DataFrame:
    _pr_path = "Pro_Stats/nflpro_passrush_all.csv"
    if not _os.path.exists(_pr_path):
        return pd.DataFrame()
    return pd.read_csv(_pr_path)


@st.cache_data
def build_merged_edge_data() -> pd.DataFrame:
    """Combine × NGS Pass Rush – career aggregated (DE/OLB のみ)"""
    _combine = load_data()
    _pr_raw  = load_passrush_data()
    if _pr_raw.empty:
        return pd.DataFrame()

    _EDGE_C = {"DE", "OLB", "LOLB", "ROLB", "EDGE", "DL"}
    _EDGE_P = {"DE", "OLB", "LOLB", "ROLB"}

    _c = _combine[_combine["position"].isin(_EDGE_C)].copy()
    # display_name 優先でマッチ名を生成（なければ first+last）
    _c["_match_name"] = _c["display_name"].fillna("").str.strip()
    _fb = _c["first_name"].str.strip() + " " + _c["last_name"].str.strip()
    _c["_match_name"] = _c["_match_name"].where(_c["_match_name"] != "", _fb)
    _c["_match_name"] = _c["_match_name"].replace(_PR_NAME_CORRECTIONS)

    _p = _pr_raw[_pr_raw["position"].isin(_EDGE_P)].copy()

    def _nz_mean(s: pd.Series) -> float:
        v = s[s > 0]
        return float(v.mean()) if len(v) > 0 else np.nan

    _pr_career = (
        _p.groupby("name")
        .agg(
            nfl_id         = ("nfl_id",           "first"),
            seasons        = ("season",           "nunique"),
            season_first   = ("season",           "min"),
            season_last    = ("season",           "max"),
            total_games    = ("games_played",     "sum"),
            total_pr_snaps = ("pass_rush_snaps",  "sum"),
            total_qbp      = ("qb_pressures",     "sum"),
            total_sacks    = ("sacks",            "sum"),
            avg_get_off    = ("get_off_time",      _nz_mean),
            avg_ttp        = ("time_to_pressure",  _nz_mean),
        )
        .reset_index()
    )
    _pr_career["career_qbpr"]          = (_pr_career["total_qbp"] / _pr_career["total_pr_snaps"].clip(lower=1)).round(4)
    _pr_career["pressures_per_season"] = (_pr_career["total_qbp"] / _pr_career["seasons"]).round(2)
    _pr_career["sacks_per_season"]     = (_pr_career["total_sacks"] / _pr_career["seasons"]).round(2)

    return _c.merge(_pr_career, left_on="_match_name", right_on="name", how="inner")


@st.cache_data
def build_merged_edge_season_data() -> pd.DataFrame:
    """Combine × NGS Pass Rush – season-level (1行 = 1選手1シーズン)"""
    _combine = load_data()
    _pr_raw  = load_passrush_data()
    if _pr_raw.empty:
        return pd.DataFrame()

    _EDGE_C = {"DE", "OLB", "LOLB", "ROLB", "EDGE", "DL"}
    _EDGE_P = {"DE", "OLB", "LOLB", "ROLB"}

    _c = _combine[_combine["position"].isin(_EDGE_C)].copy()
    _c["_match_name"] = _c["display_name"].fillna("").str.strip()
    _fb = _c["first_name"].str.strip() + " " + _c["last_name"].str.strip()
    _c["_match_name"] = _c["_match_name"].where(_c["_match_name"] != "", _fb)
    _c["_match_name"] = _c["_match_name"].replace(_PR_NAME_CORRECTIONS)

    _p = _pr_raw[_pr_raw["position"].isin(_EDGE_P)].copy()

    _merged = _c.merge(_p, left_on="_match_name", right_on="name", how="inner")

    # combine 側と pr 側で同名列が衝突する可能性がある position/position_group を整理
    if "position_x" in _merged.columns:
        _merged["position"] = _merged["position_x"]
    if "position_group_x" in _merged.columns:
        _merged["position_group"] = _merged["position_group_x"]

    return _merged


# シーズン単位 Pro 指標の定義: label → (df_col, lower_is_better)
_PPM_SEASON = {
    "QB Pressure Rate (season %)":          ("qb_pressure_rate", False),
    "QB Pressures (season total)":          ("qb_pressures",     False),
    "Sacks (season)":                       ("sacks",            False),
    "Sack Rate (season %)":                 ("sack_rate",        False),
    "Get-Off Time (s)  ↓lower=better":      ("get_off_time",     True),
    "Time-to-Pressure (s)  ↓lower":         ("time_to_pressure", True),
    "Pass Rush Snaps (season)":             ("pass_rush_snaps",  False),
}


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
        "tab_compare":      "🔍 Player Comparison",
        "compare_select":   "Select up to 4 players to compare",
        "compare_pos_warn": "Select players from the same position group for best results.",
        "compare_radar":    "Percentile Radar Chart",
        "compare_table":    "Measurement Details",
        "compare_no_data":  "Select at least 1 player to compare.",
        "compare_pct_note": "Percentiles vs. drafted players of same position group (all years). Higher = better (speed metrics inverted).",
        "similar_header":   "🔗 Similar Players",
        "similar_select":   "Find players similar to…",
        "similar_help":     "Finds historical players with the most similar combine profile (z-score distance).",
        "similar_n":        "Number of results",
        "similar_table":    "Most Similar Historical Players",
        "color_mode":       "Color by",
        "color_position":   "Position group",
        "color_round":      "Draft round",
        "download_csv":     "⬇️ Download filtered data (CSV)",
        "tab_pro":          "🏈 Pro Performance",
        "pro_title":        "Edge Rusher: Combine × Pro Pass Rush",
        "pro_caption":      (
            "Combines pre-draft measurements with NFL Pro Pass Rush stats (2019–2024). "
            "Explore which Combine attributes correlate with pass rush success."
        ),
        "pro_matched":      "Players matched",
        "pro_x":            "X axis: Combine metric",
        "pro_y":            "Y axis: Pro metric (2019–2024 career)",
        "pro_use_pd":       "Include Pro Day data",
        "pro_min_snaps":    "Min. Pass Rush snaps",
        "pro_min_snaps_help": "Exclude players with few PR snaps (statistically noisy).",
        "pro_pos":          "Position",
        "pro_draft_yr":     "Draft year range",
        "pro_color_by":     "Color by",
        "pro_color_yr":     "Draft Year",
        "pro_color_pos":    "Position",
        "pro_n":            "Players (n)",
        "pro_r":            "Correlation r",
        "pro_r2":           "R²",
        "pro_pval":         "p-value",
        "pro_slope":        "OLS slope",
        "pro_sig":          "✅ Significant (p<0.05)",
        "pro_not_sig":      "— Not significant",
        "pro_thresh_hdr":   "📊 Threshold Analysis — Does the Combine metric split Pro success?",
        "pro_thresh_slider": "Set threshold for X axis",
        "pro_thresh_note":  "\"Success\" = Y ≥ median  (or ≤ median when lower is better)",
        "pro_success":      "Success rate",
        "pro_above":        "≥ threshold",
        "pro_below":        "< threshold",
        "pro_players":      "Players",
        "pro_avg":          "Mean",
        "pro_med":          "Median",
        "pro_conclusion":   lambda x_lbl, thr, diff, direction: (
            f"{'⬆️' if diff > 0 else '⬇️'} Players with **{x_lbl} ≥ {thr:.3f}** have "
            f"a success rate **{abs(diff):.1f} pp {'higher' if diff > 0 else 'lower'}** than those below."
        ),
        "pro_table_hdr":    "📋 Data Table",
        "pro_no_data":      "Not enough data ({n} players). Loosen the filters.",
        "pro_no_file":      "⚠️ Pass Rush data not found. Check `Pro_Stats/nflpro_passrush_all.csv`.",
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
        "tab_compare":      "🔍 選手比較",
        "compare_select":   "最大4選手を選択",
        "compare_pos_warn": "同じポジショングループの選手を比較すると最も意味があります。",
        "compare_radar":    "パーセンタイル レーダーチャート",
        "compare_table":    "計測値詳細",
        "compare_no_data":  "比較する選手を1人以上選択してください。",
        "compare_pct_note": "同ポジション・全年度のドラフト指名選手との比較。高いほど良い（タイム系は反転）。",
        "similar_header":   "🔗 類似選手",
        "similar_select":   "類似選手を探す基準となる選手",
        "similar_help":     "z-score距離で過去の最も近い運動能力プロフィールの選手を検索。",
        "similar_n":        "表示件数",
        "similar_table":    "最も近い過去の選手",
        "color_mode":       "カラー",
        "color_position":   "ポジション別",
        "color_round":      "ドラフトラウンド別",
        "download_csv":     "⬇️ フィルタ済みデータ (CSV)",
        "tab_pro":          "🏈 プロ成績分析",
        "pro_title":        "Edge Rusher: Combine × プロ パスラッシュ成績",
        "pro_caption":      (
            "ドラフト前計測値と NFL Pro Pass Rush Stats（2019–2024）を結合し、"
            "どのCombine指標がプロでの活躍と相関するかを探ります。"
        ),
        "pro_matched":      "マッチした選手数",
        "pro_x":            "X軸: Combine指標",
        "pro_y":            "Y軸: Pro指標（2019–2024 通算）",
        "pro_use_pd":       "Pro-Dayデータも使用",
        "pro_min_snaps":    "最低 Pass Rush スナップ数",
        "pro_min_snaps_help": "スナップが少ない選手は統計的に不安定なため除外推奨。",
        "pro_pos":          "ポジション",
        "pro_draft_yr":     "ドラフト年",
        "pro_color_by":     "カラー",
        "pro_color_yr":     "ドラフト年",
        "pro_color_pos":    "ポジション",
        "pro_n":            "選手数 (n)",
        "pro_r":            "相関係数 r",
        "pro_r2":           "決定係数 R²",
        "pro_pval":         "p値",
        "pro_slope":        "回帰傾き",
        "pro_sig":          "✅ 有意 (p<0.05)",
        "pro_not_sig":      "— 非有意",
        "pro_thresh_hdr":   "📊 閾値分析 — Combine指標の上下でプロ成績はどう変わる？",
        "pro_thresh_slider": "X軸の閾値を設定",
        "pro_thresh_note":  "「成功」= Y ≥ 中央値（↓指標の場合は Y ≤ 中央値）",
        "pro_success":      "成功率",
        "pro_above":        "≥ 閾値",
        "pro_below":        "< 閾値",
        "pro_players":      "選手数",
        "pro_avg":          "平均",
        "pro_med":          "中央値",
        "pro_conclusion":   lambda x_lbl, thr, diff, direction: (
            f"{'⬆️' if diff > 0 else '⬇️'} **{x_lbl} ≥ {thr:.3f}** の選手は、"
            f"そうでない選手より成功率が **{abs(diff):.1f} pp {'高い' if diff > 0 else '低い'}**。"
        ),
        "pro_table_hdr":    "📋 データテーブル",
        "pro_no_data":      "データが少なすぎます（{n}人）。フィルターを緩めてください。",
        "pro_no_file":      "⚠️ Pass Rushデータが見つかりません。`Pro_Stats/nflpro_passrush_all.csv` を確認してください。",
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
_ALL_POS_PERCENTILES = compute_all_position_percentiles()

# ════════════════════════════════════════════════════════════════════════════
# サイドバー
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # 言語切替
    lang = st.radio("", ["EN", "JP"], index=1, horizontal=True,
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
        value=(2006, 2026),
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
    # Hide "Select all" option that appears in multiselect dropdown
    st.markdown(
        "<style>[data-testid='stMultiSelect'] [title='Select all'],"
        "[data-testid='stMultiSelect'] [aria-label='Select all'] { display: none !important; }"
        "</style>",
        unsafe_allow_html=True,
    )
    _search_options, label_to_player = build_player_search_options(df_all)
    highlighted_labels = st.multiselect(
        T["search_label"],
        options=_search_options,
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
    color_mode   = st.radio(T["color_mode"],
                            [T["color_position"], T["color_round"]],
                            horizontal=True, index=0)
    use_round_color = color_mode == T["color_round"]
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
APP_VERSION = "v1.0"
APP_DATE    = "2026/03/08"

st.title(T["app_title"])
st.caption(
    f"{APP_VERSION}  ·  {APP_DATE}  ·  "
    "Built by [Ames](https://x.com/ames_NFL) & Claude Code"
)
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
tab_sc, tab_hi, tab_cmp, tab_pro = st.tabs([
    T["tab_scatter"], T["tab_histogram"], T["tab_compare"], T["tab_pro"],
])

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

    if use_round_color:
        # ドラフトラウンド別カラーリング
        def _round_label(row):
            if pd.isna(row.get("draft_round")):
                return "UDFA"
            return f"Rd {int(row['draft_round'])}"
        df_plot["_color_key"] = df_plot.apply(_round_label, axis=1)
        _round_color_map = {f"Rd {r}": c for r, c in DRAFT_ROUND_COLORS.items() if isinstance(r, int)}
        _round_color_map["UDFA"] = DRAFT_ROUND_COLORS["UDFA"]
        fig = px.scatter(
            df_plot,
            x="_x", y="_y",
            color="_color_key",
            symbol="drafted_label",
            color_discrete_map=_round_color_map,
            symbol_map=symbol_map,
            hover_data=hover_cols,
            labels={
                "_x": x_label, "_y": y_label,
                "_color_key": "Round", "drafted_label": "Status",
                "_x_src": "X source", "_y_src": "Y source",
                "player": "Player", "year": "Year",
                "college": "College", "draft_round": "Round",
                "draft_pick": "Pick", "draft_team": "Team",
                "career_seasons": "NFL Seasons",
                "nfl_rookie_season": "Rookie Year",
                "nfl_last_season": "Last Season",
            },
            category_orders={"_color_key": [f"Rd {r}" for r in range(1, 8)] + ["UDFA"]},
            opacity=marker_alpha,
        )
    else:
        color_map = {p: POS_COLORS[p] for p in selected_pos}
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
        pos = row.get("pos_group", "")
        ref = compute_position_percentiles(None, pos)
        x_pct_str, y_pct_str = "", ""
        if x_label in ref and pd.notna(row.get("_x")):
            pct = calc_percentile(row["_x"], ref[x_label], x_label)
            if pct is not None:
                x_pct_str = f"  ({pct:.0f}th %ile)"
        if y_label in ref and pd.notna(row.get("_y")):
            pct = calc_percentile(row["_y"], ref[y_label], y_label)
            if pct is not None:
                y_pct_str = f"  ({pct:.0f}th %ile)"
        return (
            f"<b>⭐ {row['player']}</b>  [2026 Pre-Draft]<br>"
            f"{row.get('position', '?')} • {row.get('college', '')}<br>"
            f"{x_label}: {x_val}{x_pct_str}<br>"
            f"{y_label}: {y_val}{y_pct_str}<br>"
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

    fig.update_layout(
        xaxis_title=x_label, yaxis_title=y_label, height=660,
        **make_plot_layout(),
    )
    fig.update_xaxes(showgrid=True, gridcolor=THEME["grid"])
    fig.update_yaxes(showgrid=True, gridcolor=THEME["grid"])

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
                **make_plot_layout(margin=dict(t=40, b=60)),
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

    # ハイライト選手を縦線で表示（年度フィルタに関係なく全データから取得）
    if highlighted_players:
        _hist_ext = apply_udfa_label(df_all, udfa_threshold).copy()
        _hist_ext["_x"] = resolve_measurement(_hist_ext, x_label, use_proday)
        _hist_ext = _hist_ext[_hist_ext["_x"].notna()]
        # 2026 prospectも追加（df_2026_baseから）
        if not df_2026_base.empty:
            _hist_ext = pd.concat([_hist_ext, df_2026_base[df_2026_base["_x"].notna()]], ignore_index=True)
        hl_in_hist = _hist_ext[_hist_ext["player"].isin(highlighted_players)].sort_values("_x").reset_index(drop=True)
        # y positions staggered to avoid label overlap (cycles through 5 levels)
        _y_levels = [0.97, 0.89, 0.81, 0.73, 0.65]
        for i, (_, row) in enumerate(hl_in_hist.iterrows()):
            line_color = PREDRAFT_BORDER if row["drafted_label"] == "Unknown" else POS_COLORS.get(row.get("pos_group", ""), "#FF6F00")
            fig_hi.add_vline(
                x=row["_x"],
                line=dict(color=line_color, width=2, dash="dash"),
            )
            fig_hi.add_annotation(
                x=row["_x"],
                y=_y_levels[i % len(_y_levels)],
                yref="paper",
                text=f"{row['player']} ({row['_x']:.2f})",
                showarrow=True,
                arrowhead=2,
                arrowsize=0.8,
                arrowcolor=line_color,
                font=dict(size=10, color="#C9D1D9", family=THEME["font"]),
                bgcolor=THEME["card_bg"],
                bordercolor=line_color,
                borderwidth=1,
                borderpad=3,
                opacity=0.92,
                xanchor="left",
            )

    fig_hi.update_layout(
        barmode="overlay",
        title=dict(
            text=f"{x_label} — Distribution by Position"
                 + (" (Drafted / Undrafted split)" if hist_split else ""),
            font=dict(size=13, color=THEME["muted"], family=THEME["font"]),
            x=0, xanchor="left",
        ),
        xaxis_title=x_label,
        yaxis_title=T["density"],
        height=520,
        **make_plot_layout(margin=dict(t=60, b=40, l=50, r=20)),
    )

    st.plotly_chart(fig_hi, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# 選手比較タブ（B1 レーダーチャート + B4 類似選手）
# ────────────────────────────────────────────────────────────────────────────
with tab_cmp:
    _cmp_search_opts, _cmp_label_to_player = build_player_search_options(df_all)

    cmp_col1, cmp_col2 = st.columns([1, 1])
    with cmp_col1:
        st.subheader(T["compare_radar"])
        cmp_selected_labels = st.multiselect(
            T["compare_select"],
            options=_cmp_search_opts,
            default=[],
            max_selections=4,
            placeholder="Type a name…",
        )
        cmp_players = [_cmp_label_to_player[l] for l in cmp_selected_labels]

    with cmp_col2:
        st.subheader(T["similar_header"])
        sim_selected_label = st.selectbox(
            T["similar_select"],
            options=[""] + _cmp_search_opts,
            index=0,
            help=T["similar_help"],
        )
        sim_n = st.slider(T["similar_n"], 5, 15, 8)

    st.markdown("---")

    # ── レーダーチャート ──
    if not cmp_players:
        st.info(T["compare_no_data"])
    else:
        radar_labels_all = [l for l in MEASUREMENTS.keys() if l != "NGS Scout Grade ★" and "Wingspan" not in l]

        fig_radar = go.Figure()
        radar_data_rows = []

        # ── Pass 1: collect per-player data and find common labels ──
        _player_data: list[dict] = []  # {pname, pos, prow, ref, available_labels}
        _common_labels: set | None = None

        for pname in cmp_players:
            _rows = df_all[df_all["player"] == pname]
            if _rows.empty:
                continue
            prow = _rows.iloc[0]
            pos  = prow.get("pos_group", "")
            ref  = compute_position_percentiles(None, pos)

            available = set()
            for label in radar_labels_all:
                if label not in ref:
                    continue
                combine_col, proday_col = MEASUREMENTS[label]
                val = prow.get(combine_col) if combine_col else None
                if pd.isna(val) and proday_col:
                    val = prow.get(proday_col)
                if val is not None and not pd.isna(val):
                    available.add(label)

            if not available:
                continue
            _player_data.append({"pname": pname, "pos": pos, "prow": prow, "ref": ref, "available": available})
            _common_labels = available if _common_labels is None else _common_labels & available

        if _common_labels is None:
            _common_labels = set()

        # Keep original order
        shared_labels = [l for l in radar_labels_all if l in _common_labels]

        if _player_data and not shared_labels:
            st.warning(T.get("compare_no_common", "No measurements in common across selected players."))

        # ── Pass 2: build traces using shared labels only ──
        _pos_player_idx: dict[str, int] = {}

        for pd_item in _player_data:
            pname = pd_item["pname"]
            pos   = pd_item["pos"]
            prow  = pd_item["prow"]
            ref   = pd_item["ref"]

            r_vals, r_labs, r_raw = [], [], []
            for label in shared_labels:
                combine_col, proday_col = MEASUREMENTS[label]
                val = prow.get(combine_col) if combine_col else None
                if pd.isna(val) and proday_col:
                    val = prow.get(proday_col)
                pct = calc_percentile(val, ref[label], label)
                if pct is not None:
                    r_vals.append(pct)
                    r_labs.append(label.split(" (")[0])
                    r_raw.append(val)

            if not r_vals:
                continue

            # Vary brightness per player within same position group
            idx = _pos_player_idx.get(pos, 0)
            _pos_player_idx[pos] = idx + 1
            base_hex = POS_COLORS.get(pos, THEME["accent"]).lstrip("#")
            base_r, base_g, base_b = (int(base_hex[i:i+2], 16) for i in (0, 2, 4))
            shift = [0, 45, -45, 22][idx % 4]
            c_r = max(0, min(255, base_r + shift))
            c_g = max(0, min(255, base_g + shift))
            c_b = max(0, min(255, base_b + shift))
            pos_color = f"#{c_r:02x}{c_g:02x}{c_b:02x}"

            fig_radar.add_trace(go.Scatterpolar(
                r=r_vals + [r_vals[0]],
                theta=r_labs + [r_labs[0]],
                fill="toself",
                fillcolor=f"rgba{tuple(int(pos_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.15,)}",
                line=dict(color=pos_color, width=2),
                name=f"{pname} ({pos})",
                hovertemplate="<b>%{theta}</b><br>%{r:.0f}th %ile<extra></extra>",
            ))
            radar_data_rows.append({
                "Player": pname, "Position": pos, "Year": int(prow.get("year", 0)),
                **{l: f"{v:.1f}  ({p:.0f}th)" for l, v, p in zip(r_labs, r_raw, r_vals)},
            })

        fig_radar.update_layout(
            polar=dict(
                bgcolor=THEME["card_bg"],
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    tickfont=dict(color=THEME["muted"], size=9),
                    gridcolor=THEME["grid"],
                    linecolor=THEME["border"],
                ),
                angularaxis=dict(
                    tickfont=dict(color=THEME["text"], size=10, family=THEME["font"]),
                    gridcolor=THEME["grid"],
                    linecolor=THEME["border"],
                ),
            ),
            **make_plot_layout(margin=dict(t=40, b=60, l=60, r=60)),
            height=500,
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.caption(T["compare_pct_note"])

        if radar_data_rows:
            st.subheader(T["compare_table"])
            st.dataframe(pd.DataFrame(radar_data_rows).set_index("Player"), use_container_width=True)

    st.markdown("---")

    # ── 類似選手ファインダー ──
    st.subheader(T["similar_table"])
    if sim_selected_label and sim_selected_label != "":
        sim_player_name = _cmp_label_to_player.get(sim_selected_label)
        if sim_player_name:
            _sim_rows = df_all[df_all["player"] == sim_player_name]
            if not _sim_rows.empty:
                _sim_row = _sim_rows.iloc[0]
                _sim_pos = _sim_row.get("pos_group", "")
                _df_hist_sim = df_all[
                    (df_all["_drafted_base"] != "Unknown") &
                    (df_all["pos_group"] == _sim_pos)
                ]
                similar_df = find_similar_players(_sim_row, _df_hist_sim, _sim_pos, n=sim_n)
                if not similar_df.empty:
                    base_cols = ["player", "year", "college", "drafted_label",
                                 "draft_round", "draft_pick", "_similarity"]
                    if HAS_CAREER:
                        base_cols += ["career_seasons"]
                    # 利用可能な測定値列を追加
                    meas_display_cols = []
                    for _lbl, (c_col, p_col) in MEASUREMENTS.items():
                        if _lbl in ("NGS Scout Grade ★",):
                            continue
                        col = c_col or p_col
                        if col and col in similar_df.columns and similar_df[col].notna().any():
                            meas_display_cols.append((col, _lbl.split(" (")[0]))
                    all_display = [c for c in base_cols if c in similar_df.columns]
                    similar_show = similar_df[all_display].copy()
                    col_rename = {
                        "player": "Player", "year": "Year", "college": "College",
                        "drafted_label": "Status", "draft_round": "Round",
                        "draft_pick": "Pick", "_similarity": "Sim %",
                        "career_seasons": "NFL Seasons",
                    }
                    similar_show.columns = [col_rename.get(c, c) for c in all_display]
                    similar_show["Sim %"] = similar_show["Sim %"].round(1)
                    # 測定値列を追加（生値 + 対象選手との比較）
                    for raw_col, short_lbl in meas_display_cols:
                        ref_val = _sim_row.get(raw_col)
                        similar_show[short_lbl] = similar_df[raw_col].apply(
                            lambda v: f"{v:.2f}  (ref: {ref_val:.2f})" if pd.notna(v) and pd.notna(ref_val) else (f"{v:.2f}" if pd.notna(v) else "—")
                        )
                    st.caption(f"Most similar to **{sim_player_name}** ({_sim_pos}, {int(_sim_row.get('year', 0))})")
                    st.dataframe(similar_show.reset_index(drop=True), use_container_width=True)
                else:
                    st.info("Not enough measurement data to find similar players.")
    else:
        st.info(T["compare_no_data"])

# ────────────────────────────────────────────────────────────────────────────
# 🏈 Pro Performance タブ (Edge Rusher Combine × Pass Rush)
# ────────────────────────────────────────────────────────────────────────────
with tab_pro:
    st.markdown("""
    <div style="
        text-align:center;
        padding:60px 20px;
        color:#8B949E;
    ">
        <div style="font-size:3rem;margin-bottom:16px">🚧</div>
        <div style="font-size:1.3rem;font-weight:700;color:#E6EDF3;margin-bottom:8px">
            準備中 / Coming Soon
        </div>
        <div style="font-size:0.95rem;line-height:1.8">
            Edge Rusher Combine × Pro Pass Rush 分析は現在開発中です。<br>
            <span style="color:#6E7681">Pro Performance analysis is under development.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── フッター ───────────────────────────────────────────────────────────────────
st.markdown("---")
_career_note = (
    "  |  Career data: nflverse players.csv  |  "
    "🌟 Undrafted NFL = undrafted player with ≥ N NFL seasons"
    if HAS_CAREER else ""
)
st.caption(T["footer_line1"] + _career_note)
st.caption(T["footer_line2"])
st.caption(
    f"{APP_VERSION}  ·  {APP_DATE}  ·  "
    "Built by [Ames](https://x.com/ames_NFL) & Claude Code"
)
