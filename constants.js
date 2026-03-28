/**
 * constants.js — NFL Combine & Pro Day Explorer
 * All app-wide constants: position groups, colors, measurements, translations.
 */

'use strict';

const APP_VERSION = 'v1.0';
const APP_DATE    = '2026/03/08';

// ─── Position Group Definitions ───────────────────────────────────────────────
const POS_GROUPS = {
  QB:    ['QB'],
  RB:    ['RB', 'FB'],
  WR:    ['WR', 'WR/CB'],
  TE:    ['TE'],
  OT:    ['OT', 'T'],
  IOL:   ['OG', 'C', 'G', 'OL'],
  Edge:  ['DE', 'EDGE', 'EDG', 'OLB'],
  DT:    ['DT', 'NT', 'IDL', 'DL'],
  ILB:   ['ILB', 'MLB', 'LB'],
  DB:    ['CB', 'S', 'FS', 'SS', 'DB', 'SAF'],
  'K/P': ['K', 'P', 'LS', 'KR'],
};
const POS_GROUP_ORDER = ['QB','RB','WR','TE','OT','IOL','Edge','DT','ILB','DB','K/P'];

const POS_COLORS = {
  QB:    '#E53935',
  RB:    '#FB8C00',
  WR:    '#FDD835',
  TE:    '#43A047',
  OT:    '#00ACC1',
  IOL:   '#4DD0E1',
  Edge:  '#FF5722',
  DT:    '#1E88E5',
  ILB:   '#8E24AA',
  DB:    '#F06292',
  'K/P': '#90A4AE',
};

const PREDRAFT_COLOR  = '#FFD600';
const PREDRAFT_BORDER = '#FF8F00';
const UDFA_SUCCESS_COLOR  = '#00C853';
const UDFA_SUCCESS_BORDER = '#1B5E20';

// ─── Draft Round Colors ────────────────────────────────────────────────────────
const DRAFT_ROUND_COLORS = {
  1: '#E53935', 2: '#FB8C00', 3: '#FDD835', 4: '#43A047',
  5: '#00ACC1', 6: '#1E88E5', 7: '#8E24AA', 'UDFA': '#6E7681',
};

// ─── Measurements ─────────────────────────────────────────────────────────────
// label -> [combine_col, proday_col]  (null = not available for that source)
const MEASUREMENTS = {
  'Height (in)':                   ['combine_height',             'pro_day_height'],
  'Weight (lbs)':                  ['combine_weight',             'pro_day_weight'],
  'Arm Length (in)':               ['combine_arm_length',         'pro_day_arm_length'],
  'Hand Size (in)':                ['combine_hand_size',          'pro_day_hand_size'],
  '40-Yard Dash (s)':              ['combine_forty_yard_dash',    'pro_day_forty_yard_dash'],
  '10-Yard Split (s)':             ['combine_ten_yard_split',     'pro_day_ten_yard_split'],
  'Bench Press (reps)':            ['combine_bench_press',        'pro_day_bench_press'],
  'Vertical Jump (in)':            ['combine_vertical_jump',      'pro_day_vertical_jump'],
  'Broad Jump (in)':               ['combine_broad_jump',         'pro_day_broad_jump'],
  '3-Cone Drill (s)':              ['combine_three_cone_drill',   'pro_day_three_cone_drill'],
  '20-Yd Shuttle (s)':             ['combine_twenty_yard_shuttle','pro_day_twenty_yard_shuttle'],
  'Wingspan (in) \u2605Pro Day only': [null,                      'pro_day_wingspan'],
  'NGS Scout Grade \u2605':        ['draft_grade',                null],
};
const MEAS_LABELS = Object.keys(MEASUREMENTS);

// Speed/time metrics where lower values are better
const LOWER_IS_BETTER = new Set([
  '40-Yard Dash (s)', '10-Yard Split (s)', '3-Cone Drill (s)', '20-Yd Shuttle (s)',
]);

// ─── Edge Combine Metrics (for Pro tab) ───────────────────────────────────────
// label -> [combine_col, proday_col]
const ECM = {
  'Arm Length (in)':    ['combine_arm_length',         'pro_day_arm_length'],
  'Hand Size (in)':     ['combine_hand_size',           'pro_day_hand_size'],
  'Height (in)':        ['combine_height',              'pro_day_height'],
  'Weight (lbs)':       ['combine_weight',              'pro_day_weight'],
  '40-Yard Dash (s)':   ['combine_forty_yard_dash',     'pro_day_forty_yard_dash'],
  '10-Yard Split (s)':  ['combine_ten_yard_split',      'pro_day_ten_yard_split'],
  'Vertical Jump (in)': ['combine_vertical_jump',       'pro_day_vertical_jump'],
  'Broad Jump (in)':    ['combine_broad_jump',          'pro_day_broad_jump'],
  '3-Cone Drill (s)':   ['combine_three_cone_drill',    'pro_day_three_cone_drill'],
  '20-Yd Shuttle (s)':  ['combine_twenty_yard_shuttle', 'pro_day_twenty_yard_shuttle'],
  'Bench Press (reps)': ['combine_bench_press',         'pro_day_bench_press'],
  'NGS Draft Grade':    ['draft_grade',                 null],
};
const ECM_LOWER_BETTER = new Set(['40-Yard Dash (s)','10-Yard Split (s)','3-Cone Drill (s)','20-Yd Shuttle (s)']);

// ─── Career-aggregated Pro metrics ────────────────────────────────────────────
// label -> [col, lower_is_better]
const PPM = {
  'QB Pressure Rate (career %)':    ['career_qbpr',          false],
  'QB Pressures / Season':          ['pressures_per_season', false],
  'QB Pressures (career total)':    ['total_qbp',            false],
  'Sacks / Season':                 ['sacks_per_season',     false],
  'Sacks (career total)':           ['total_sacks',          false],
  'Get-Off Time avg (s)':           ['avg_get_off',          true],
  'Time-to-Pressure avg (s)':       ['avg_ttp',              true],
  'Pass Rush Snaps (career total)': ['total_pr_snaps',       false],
};

// ─── Season-level Pro metrics ──────────────────────────────────────────────────
const PPM_SEASON = {
  'QB Pressure Rate (season %)':  ['qb_pressure_rate', false],
  'QB Pressures (season total)':  ['qb_pressures',     false],
  'Sacks (season)':               ['sacks',            false],
  'Sack Rate (season %)':         ['sack_rate',        false],
  'Get-Off Time (s)':             ['get_off_time',     true],
  'Time-to-Pressure (s)':         ['time_to_pressure', true],
  'Pass Rush Snaps (season)':     ['pass_rush_snaps',  false],
};

// ─── Pass-Rush Name Corrections ────────────────────────────────────────────────
const PR_NAME_CORRECTIONS = {
  'Alvin Dupree':        'Bud Dupree',
  'Alexander Okafor':    'Alex Okafor',
  'Joshua Hines-Allen':  'Josh Hines-Allen',
  'Zachary Allen':       'Zach Allen',
  'Samuel Hubbard':      'Sam Hubbard',
  'William Anderson':    'Will Anderson',
  'DeMarcus Lawrence':   'Demarcus Lawrence',
  'Trenton Murphy':      'Trent Murphy',
  'Randall Gregory':     'Randy Gregory',
  'Victor Beasley':      'Vic Beasley',
  'Timothy Williams':    'Tim Williams',
  'Vincent Biegel':      'Vince Biegel',
  'Samuel Williams':     'Sam Williams',
  'Jeffrey Gunter':      'Jeff Gunter',
  'DeMario Davis':       'Demario Davis',
  'Matthew Milano':      'Matt Milano',
  'Steven Longa':        'Steve Longa',
  "La'Darius Hamilton":  'Ladarius Hamilton',
};

// ─── Theme ────────────────────────────────────────────────────────────────────
const THEME = {
  bg:          '#0D1117',
  card_bg:     '#161B22',
  border:      '#30363D',
  grid:        '#21262D',
  text:        '#C9D1D9',
  text_bright: '#E6EDF3',
  muted:       '#6E7681',
  label:       '#8B949E',
  accent:      '#58A6FF',
};

// ─── Chart Constants ──────────────────────────────────────────────────────────
const MIN_SAMPLES_ELLIPSE  = 10;
const MIN_SAMPLES_STATS    = 5;
const LABEL_WARN_THRESHOLD = 80;
const HIST_BINS            = 30;
const KDE_BANDWIDTH        = 0.5;
const MIN_KDE_SAMPLES      = 5;

// ─── Plotly layout base ────────────────────────────────────────────────────────
function makePlotLayout(overrides = {}) {
  const base = {
    plot_bgcolor:  THEME.card_bg,
    paper_bgcolor: THEME.bg,
    font: { color: THEME.text, family: 'Geist, -apple-system, sans-serif' },
    hoverlabel: {
      bgcolor: '#1C2128', bordercolor: THEME.border,
      font: { color: THEME.text_bright, size: 12, family: 'Geist, sans-serif' },
    },
    legend: {
      orientation: 'h', yanchor: 'top', y: -0.14, xanchor: 'left', x: 0,
      bgcolor: 'rgba(22,27,34,0.85)', bordercolor: THEME.border, borderwidth: 1,
      font: { size: 11, color: THEME.text },
    },
    xaxis: {
      gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 },
      title_font: { color: THEME.label },
    },
    yaxis: {
      gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 },
      title_font: { color: THEME.label },
    },
    margin: { t: 20, b: 160, l: 50, r: 20 },
  };
  return Object.assign(base, overrides);
}

// ─── Translations ──────────────────────────────────────────────────────────────
const TR = {
  EN: {
    app_title:       'NFL Combine & Pro Day Explorer',
    year_header:     'Year',
    year_range:      'Year range',
    pos_header:      'Position Group',
    pos_select:      'Select positions',
    pos_warn:        '\u26a0\ufe0f Select at least one position.',
    meas_header:     'Measurements',
    x_axis:          'X axis',
    y_axis:          'Y axis',
    source_header:   'Data Source',
    proday_toggle:   'Include Pro Day data',
    proday_cap:      'Combine measurement takes priority when available.',
    draft_header:    'Draft Status',
    draft_show:      'Show',
    draft_all:       'All players',
    draft_drafted:   'Drafted only',
    draft_undrafted: 'Undrafted only',
    draft_nfl:       'NFL players (Drafted + Undrafted NFL)',
    show_2026:       '\u2b50 Show 2026 Pre-Draft players',
    udfa_header:     'Undrafted NFL Players',
    udfa_slider:     'Min. NFL seasons to qualify as Undrafted NFL',
    display_header:  'Display',
    marker_size:     'Marker size',
    opacity:         'Opacity',
    ellipse:         'Show 95% confidence ellipse',
    stats_panel:     'Show statistics panel',
    search_header:   'Player Search & Labels',
    search_label:    'Search & highlight players',
    search_ph:       'Type a name to search\u2026',
    all_labels:      'Show name labels for ALL visible players',
    tab_scatter:     'Scatter Plot',
    tab_histogram:   'Histogram',
    tab_compare:     'Player Comparison',
    tab_pro:         'Pro Performance',
    hist_split:      'Split Drafted / Undrafted',
    show_2026_kde:   'Show 2026 KDE lines',
    stats_header:    'Statistics by Position',
    boxplot_label:   'Box Plot: Drafted vs Undrafted by Position',
    boxplot_info:    "Box plot comparison requires 'All players' filter.",
    total_players:   'Total players',
    drafted_metric:  'Drafted',
    undrafted_metric:'Undrafted',
    predraft_metric: '2026 Pre-Draft',
    source_metric:   'Data source (X)',
    density:         'Density',
    compare_select:  'Select up to 4 players to compare',
    compare_radar:   'Percentile Radar Chart',
    compare_table:   'Measurement Details',
    compare_no_data: 'Select at least 1 player to compare.',
    compare_pct_note:'Percentiles vs. drafted players of same position group (all years). Higher = better (speed metrics inverted).',
    similar_header:  'Similar Players',
    similar_select:  'Find players similar to\u2026',
    similar_n:       'Number of results',
    similar_table:   'Most Similar Historical Players',
    color_mode:      'Color by',
    color_position:  'Position group',
    color_round:     'Draft round',
    download_csv:    '\u2b07\ufe0f Download filtered data (CSV)',
    pro_title:       'Edge Rusher: Combine \u00d7 Pro Pass Rush',
    pro_caption:     'Combines pre-draft measurements with NFL Pro Pass Rush stats (2019\u20132024). Explore which Combine attributes correlate with pass rush success.',
    pro_matched:     'Players matched',
    pro_x:           'X axis: Combine metric',
    pro_y:           'Y axis: Pro metric (career)',
    pro_use_pd:      'Include Pro Day data',
    pro_min_snaps:   'Min. Pass Rush snaps',
    pro_pos:         'Position',
    pro_draft_yr:    'Draft year range',
    pro_color_by:    'Color by',
    pro_color_yr:    'Draft Year',
    pro_color_pos:   'Position',
    pro_n:           'Players (n)',
    pro_r:           'Correlation r',
    pro_r2:          'R\u00b2',
    pro_pval:        'p-value',
    pro_slope:       'OLS slope',
    pro_sig:         '\u2705 Significant (p<0.05)',
    pro_not_sig:     '\u2014 Not significant',
    pro_thresh_hdr:  'Threshold Analysis \u2014 Does the Combine metric split Pro success?',
    pro_thresh_slider:'Set threshold for X axis',
    pro_thresh_note: '"Success" = Y \u2265 median  (or \u2264 median when lower is better)',
    pro_success:     'Success rate',
    pro_above:       '\u2265 threshold',
    pro_below:       '< threshold',
    pro_players:     'Players',
    pro_avg:         'Mean',
    pro_med:         'Median',
    pro_table_hdr:   'Data Table',
    pro_no_data:     'Not enough data ({n} players). Loosen the filters.',
    pro_no_file:     '\u26a0\ufe0f Pass Rush data not found.',
    footer_line1:    'Data: NFL Combine (official) + Pro Day measurements  |  Draft data: nflverse (2006\u20132024) + manual (2025)  |  2026 players shown as gold markers  |  Combine preferred; Pro Day used as fallback when toggle is ON',
    footer_line2:    "Combine & Pro Day data sourced from Roy Carpenter's nfl-draft-data",
    view_mode:       'View mode',
    scatter_view:    'Scatter (Combine \u2192 Pro)',
    heatmap_view:    '2D Heatmap (Combine \u00d7 Combine \u2192 Pro)',
    agg_mode:        'Aggregation',
    career_agg:      'Career',
    season_agg:      'Per Season',
    hm_x:            'X axis: Combine \u2460',
    hm_y:            'Y axis: Combine \u2461',
    hm_z:            'Color: Pro metric',
    hm_grid:         'Grid size (N\u00d7N)',
    hm_agg:          'Aggregation',
    hm_mean:         'Mean',
    hm_median:       'Median',
    hm_overlay:      'Show individual players',
    hm_n:            'Players (n)',
    hm_valid_cells:  'Valid cells',
    hm_pos:          'Position',
    hm_yr:           'Draft year range',
    agg_mode_label:  'Aggregation mode',
  },
  JP: {
    app_title:       'NFL Combine & Pro-day \u89e3\u6790\u30c4\u30fc\u30eb',
    year_header:     '\u5e74\u5ea6',
    year_range:      '\u5e74\u5ea6\u7bc4\u56f2',
    pos_header:      '\u30dd\u30b8\u30b7\u30e7\u30f3',
    pos_select:      '\u30dd\u30b8\u30b7\u30e7\u30f3\u3092\u9078\u629e',
    pos_warn:        '\u26a0\ufe0f \u30dd\u30b8\u30b7\u30e7\u30f3\u30921\u3064\u4ee5\u4e0a\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
    meas_header:     '\u6e2c\u5b9a\u9805\u76ee',
    x_axis:          'X \u8ef8',
    y_axis:          'Y \u8ef8',
    source_header:   '\u30c7\u30fc\u30bf\u30bd\u30fc\u30b9',
    proday_toggle:   'Pro-day\u30c7\u30fc\u30bf\u3092\u542b\u3081\u308b',
    proday_cap:      'Combine\u8a08\u6e2c\u5024\u304c\u512a\u5148\u3055\u308c\u307e\u3059\u3002',
    draft_header:    '\u30c9\u30e9\u30d5\u30c8\u72b6\u6cc1',
    draft_show:      '\u8868\u793a\u5bfe\u8c61',
    draft_all:       '\u5168\u9078\u624b',
    draft_drafted:   '\u6307\u540d\u3042\u308a',
    draft_undrafted: '\u6307\u540d\u306a\u3057',
    draft_nfl:       'NFL\u9078\u624b\uff08\u6307\u540d\u3042\u308a + Undrafted NFL\uff09',
    show_2026:       '\u2b50 2026 \u30d7\u30ec\u30c9\u30e9\u30d5\u30c8\u9078\u624b\u3092\u8868\u793a',
    udfa_header:     'Undrafted NFL\u9078\u624b',
    udfa_slider:     'Undrafted NFL\u3068\u307f\u306a\u3059\u6700\u4f4eNFL\u30b7\u30fc\u30ba\u30f3\u6570',
    display_header:  '\u8868\u793a\u8a2d\u5b9a',
    marker_size:     '\u30de\u30fc\u30ab\u30fc\u30b5\u30a4\u30ba',
    opacity:         '\u4e0d\u900f\u660e\u5ea6',
    ellipse:         '95% \u4fe1\u983c\u695a\u5186\u3092\u8868\u793a',
    stats_panel:     '\u7d71\u8a08\u30d1\u30cd\u30eb\u3092\u8868\u793a',
    search_header:   '\u9078\u624b\u691c\u7d22 & \u30e9\u30d9\u30eb',
    search_label:    '\u9078\u624b\u3092\u691c\u7d22\u30fb\u30cf\u30a4\u30e9\u30a4\u30c8',
    search_ph:       '\u540d\u524d\u3092\u5165\u529b\u2026',
    all_labels:      '\u8868\u793a\u4e2d\u306e\u5168\u9078\u624b\u540d\u3092\u8868\u793a',
    tab_scatter:     '\u6563\u5e03\u56f3',
    tab_histogram:   '\u30d2\u30b9\u30c8\u30b0\u30e9\u30e0',
    tab_compare:     '\u9078\u624b\u6bd4\u8f03',
    tab_pro:         '\u30d7\u30ed\u6210\u7e3e\u5206\u6790',
    hist_split:      '\u6307\u540d\u3042\u308a / \u306a\u3057\u3092\u5206\u3051\u3066\u8868\u793a',
    show_2026_kde:   '2026 KDE \u30e9\u30a4\u30f3\u3092\u8868\u793a',
    stats_header:    '\u30dd\u30b8\u30b7\u30e7\u30f3\u5225\u7d71\u8a08',
    boxplot_label:   '\u30dc\u30c3\u30af\u30b9\u30d7\u30ed\u30c3\u30c8\uff1a\u6307\u540d\u3042\u308a vs \u6307\u540d\u306a\u3057',
    boxplot_info:    '\u30dc\u30c3\u30af\u30b9\u30d7\u30ed\u30c3\u30c8\u306f\u300c\u5168\u9078\u624b\u300d\u30d5\u30a3\u30eb\u30bf\u30fc\u6642\u306e\u307f\u8868\u793a\u3002',
    total_players:   '\u8868\u793a\u9078\u624b\u6570',
    drafted_metric:  '\u6307\u540d\u3042\u308a',
    undrafted_metric:'\u6307\u540d\u306a\u3057',
    predraft_metric: '2026 \u30d7\u30ec\u30c9\u30e9\u30d5\u30c8',
    source_metric:   '\u30c7\u30fc\u30bf\u30bd\u30fc\u30b9 (X)',
    density:         '\u5bc6\u5ea6',
    compare_select:  '\u6700\u59274\u9078\u624b\u3092\u9078\u629e',
    compare_radar:   '\u30d1\u30fc\u30bb\u30f3\u30bf\u30a4\u30eb \u30ec\u30fc\u30c0\u30fc\u30c1\u30e3\u30fc\u30c8',
    compare_table:   '\u8a08\u6e2c\u5024\u8a73\u7d30',
    compare_no_data: '\u6bd4\u8f03\u3059\u308b\u9078\u624b\u30921\u4eba\u4ee5\u4e0a\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
    compare_pct_note:'\u540c\u30dd\u30b8\u30b7\u30e7\u30f3\u30fb\u5168\u5e74\u5ea6\u306e\u30c9\u30e9\u30d5\u30c8\u6307\u540d\u9078\u624b\u3068\u306e\u6bd4\u8f03\u3002\u9ad8\u3044\u307b\u3069\u826f\u3044\uff08\u30bf\u30a4\u30e0\u7cfb\u306f\u53cd\u8ee2\uff09\u3002',
    similar_header:  '\u985e\u4f3c\u9078\u624b',
    similar_select:  '\u985e\u4f3c\u9078\u624b\u3092\u63a2\u3059\u57fa\u6e96\u3068\u306a\u308b\u9078\u624b',
    similar_n:       '\u8868\u793a\u4ef6\u6570',
    similar_table:   '\u6700\u3082\u8fd1\u3044\u904e\u53bb\u306e\u9078\u624b',
    color_mode:      '\u30ab\u30e9\u30fc',
    color_position:  '\u30dd\u30b8\u30b7\u30e7\u30f3\u5225',
    color_round:     '\u30c9\u30e9\u30d5\u30c8\u30e9\u30a6\u30f3\u30c9\u5225',
    download_csv:    '\u2b07\ufe0f \u30d5\u30a3\u30eb\u30bf\u6e08\u307f\u30c7\u30fc\u30bf (CSV)',
    pro_title:       'Edge Rusher: Combine \u00d7 \u30d7\u30ed \u30d1\u30b9\u30e9\u30c3\u30b7\u30e5\u6210\u7e3e',
    pro_caption:     '\u30c9\u30e9\u30d5\u30c8\u524d\u8a08\u6e2c\u5024\u3068NFL Pro Pass Rush Stats\uff082019\u20132024\uff09\u3092\u7d50\u5408\u3057\u3001\u3069\u306eCombine\u6307\u6a19\u304c\u30d7\u30ed\u3067\u306e\u6d3b\u8e8d\u3068\u76f8\u95a2\u3059\u308b\u304b\u3092\u63a2\u308a\u307e\u3059\u3002',
    pro_matched:     '\u30de\u30c3\u30c1\u3057\u305f\u9078\u624b\u6570',
    pro_x:           'X\u8ef8: Combine\u6307\u6a19',
    pro_y:           'Y\u8ef8: Pro\u6307\u6a19\uff08\u901a\u7b97\uff09',
    pro_use_pd:      'Pro-Day\u30c7\u30fc\u30bf\u3082\u4f7f\u7528',
    pro_min_snaps:   '\u6700\u4f4e Pass Rush \u30b9\u30ca\u30c3\u30d7\u6570',
    pro_pos:         '\u30dd\u30b8\u30b7\u30e7\u30f3',
    pro_draft_yr:    '\u30c9\u30e9\u30d5\u30c8\u5e74',
    pro_color_by:    '\u30ab\u30e9\u30fc',
    pro_color_yr:    '\u30c9\u30e9\u30d5\u30c8\u5e74',
    pro_color_pos:   '\u30dd\u30b8\u30b7\u30e7\u30f3',
    pro_n:           '\u9078\u624b\u6570 (n)',
    pro_r:           '\u76f8\u95a2\u4fc2\u6570 r',
    pro_r2:          '\u6c7a\u5b9a\u4fc2\u6570 R\u00b2',
    pro_pval:        'p\u5024',
    pro_slope:       '\u56de\u5e30\u508d\u308a',
    pro_sig:         '\u2705 \u6709\u610f (p<0.05)',
    pro_not_sig:     '\u2014 \u975e\u6709\u610f',
    pro_thresh_hdr:  '\u9583\u5024\u5206\u6790 \u2014 Combine\u6307\u6a19\u306e\u4e0a\u4e0b\u3067\u30d7\u30ed\u6210\u7e3e\u306f\u3069\u3046\u5909\u308f\u308b\uff1f',
    pro_thresh_slider:'X\u8ef8\u306e\u9583\u5024\u3092\u8a2d\u5b9a',
    pro_thresh_note: '\u300c\u6210\u529f\u300d= Y \u2265 \u4e2d\u592e\u5024\uff08\u2193\u6307\u6a19\u306e\u5834\u5408\u306f Y \u2264 \u4e2d\u592e\u5024\uff09',
    pro_success:     '\u6210\u529f\u7387',
    pro_above:       '\u2265 \u9583\u5024',
    pro_below:       '< \u9583\u5024',
    pro_players:     '\u9078\u624b\u6570',
    pro_avg:         '\u5e73\u5747',
    pro_med:         '\u4e2d\u592e\u5024',
    pro_table_hdr:   '\u30c7\u30fc\u30bf\u30c6\u30fc\u30d6\u30eb',
    pro_no_data:     '\u30c7\u30fc\u30bf\u304c\u5c11\u306a\u3059\u304e\u307e\u3059\uff08{n}\u4eba\uff09\u3002\u30d5\u30a3\u30eb\u30bf\u30fc\u3092\u7de9\u3081\u3066\u304f\u3060\u3055\u3044\u3002',
    pro_no_file:     '\u26a0\ufe0f Pass Rush\u30c7\u30fc\u30bf\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3002',
    footer_line1:    '\u30c7\u30fc\u30bf: NFL Combine\uff08\u516c\u5f0f\uff09+ Pro-day\u8a08\u6e2c  |  \u30c9\u30e9\u30d5\u30c8\u30c7\u30fc\u30bf: nflverse (2006\u20132024) + \u624b\u52d5\u5165\u529b (2025)',
    footer_line2:    "Combine & Pro-day\u30c7\u30fc\u30bf\u306f Roy Carpenter's nfl-draft-data \u3088\u308a\u53d6\u5f97\u3002",
    view_mode:       '\u8868\u793a\u30e2\u30fc\u30c9',
    scatter_view:    '\u6563\u5e03\u56f3 (Combine \u2192 Pro)',
    heatmap_view:    '2D\u30d2\u30fc\u30c8\u30de\u30c3\u30d7 (Combine \u00d7 Combine \u2192 Pro)',
    agg_mode:        '\u96c6\u8a08\u30e2\u30fc\u30c9',
    career_agg:      '\u901a\u7b97 (Career)',
    season_agg:      '\u30b7\u30fc\u30ba\u30f3\u5225',
    hm_x:            'X\u8ef8: Combine\u6307\u6a19\u2460',
    hm_y:            'Y\u8ef8: Combine\u6307\u6a19\u2461',
    hm_z:            '\u8272: Pro\u6307\u6a19',
    hm_grid:         '\u30b0\u30ea\u30c3\u30c9\u30b5\u30a4\u30ba (N\u00d7N)',
    hm_agg:          '\u96c6\u8a08\u65b9\u6cd5',
    hm_mean:         '\u5e73\u5747 (mean)',
    hm_median:       '\u4e2d\u592e\u5024 (median)',
    hm_overlay:      '\u500b\u5225\u9078\u624b\u3092\u91cd\u306d\u308b',
    hm_n:            '\u9078\u624b\u6570 (n)',
    hm_valid_cells:  '\u6709\u52b9\u30bb\u30eb\u6570',
    hm_pos:          '\u30dd\u30b8\u30b7\u30e7\u30f3',
    hm_yr:           '\u30c9\u30e9\u30d5\u30c8\u5e74',
    agg_mode_label:  '\u96c6\u8a08\u30e2\u30fc\u30c9',
  },
};
