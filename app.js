/**
 * app.js — NFL Combine & Pro Day Explorer
 * Main application logic: data loading, preprocessing, rendering, and UI wiring.
 */

'use strict';

// ─── Global Data ───────────────────────────────────────────────────────────────
let RAW_DATA      = [];   // All rows from combine CSV (year < 2026)
let DATA_2026     = [];   // Rows with year === 2026
let PASSRUSH_RAW  = [];   // All rows from passrush CSV
let MERGED_EDGE   = [];   // Career-aggregated Edge join
let MERGED_SEASON = [];   // Season-level Edge join
let POS_TO_GROUP  = {};   // position -> pos_group
let POS_PERCENTILES = {}; // { pos_group: { label: [sorted drafted values] } }

// ─── Application State ─────────────────────────────────────────────────────────
const STATE = {
  lang:              'EN',
  yearStart:         2006,
  yearEnd:           2025,
  selectedPos:       [...POS_GROUP_ORDER],
  xLabel:            '40-Yard Dash (s)',
  yLabel:            'Vertical Jump (in)',
  useProDay:         true,
  draftFilter:       'all',
  show2026:          true,
  udfaThreshold:     0,
  colorMode:         'position',
  markerSize:        5,
  opacity:           0.65,
  showEllipse:       false,
  showStats:         true,
  highlightedPlayers:[],
  showAllLabels:     false,
  activeTab:         'scatter',
  histSplit:         false,
  show2026kde:       true,
  comparePlayers:    [],
  simPlayer:         null,
  simN:              8,
  proViewMode:       'scatter',
  proAggMode:        'career',
  proXLabel:         'Arm Length (in)',
  proYLabel:         'QB Pressure Rate (career %)',
  proUseProDay:      true,
  proMinSnaps:       200,
  proPosFilter:      ['DE', 'OLB'],
  proYearStart:      2008,
  proYearEnd:        2022,
  proColorBy:        'year',
  proThreshold:      null,
  hmXLabel:          'Arm Length (in)',
  hmYLabel:          '40-Yard Dash (s)',
  hmZLabel:          'QB Pressure Rate (career %)',
  hmMinSnaps:        200,
  hmPosFilter:       ['DE', 'OLB'],
  hmYearStart:       2008,
  hmYearEnd:         2022,
  hmNBins:           12,
  hmAggFunc:         'mean',
  hmShowScatter:     true,
  hmUseProDay:       true,
};

// ─── DOM Helper ────────────────────────────────────────────────────────────────
const el = id => document.getElementById(id);

// ─── Translation Helper ────────────────────────────────────────────────────────
function t(key) {
  return (TR[STATE.lang] && TR[STATE.lang][key]) || TR.EN[key] || key;
}

function applyTranslations() {
  document.querySelectorAll('[data-tr]').forEach(node => {
    const key = node.getAttribute('data-tr');
    const text = t(key);
    if (text) node.textContent = text;
  });
  el('app-title').textContent = t('app_title');
}

// ─── Utility ───────────────────────────────────────────────────────────────────
function parseNum(v) {
  if (v === null || v === undefined || v === '' || v === 'NA' || v === 'N/A') return NaN;
  const n = parseFloat(v);
  return isFinite(n) ? n : NaN;
}

function formatNum(v, decimals = 2) {
  if (!isFinite(v)) return '—';
  return v.toFixed(decimals);
}

function fmtPval(p) {
  if (!isFinite(p)) return '—';
  if (p < 0.001) return '<0.001';
  return p.toFixed(3);
}

// ─── Position Mapping ──────────────────────────────────────────────────────────
function buildPosToGroup() {
  POS_TO_GROUP = {};
  for (const [group, positions] of Object.entries(POS_GROUPS)) {
    for (const pos of positions) {
      POS_TO_GROUP[pos.toUpperCase()] = group;
    }
  }
}

// ─── Measurement Resolution ────────────────────────────────────────────────────
function resolveMeasurement(row, label, useProDay) {
  const cols = MEASUREMENTS[label] || ECM[label];
  if (!cols) return NaN;
  const [combineCol, proDayCol] = cols;

  const combineVal = combineCol ? parseNum(row[combineCol]) : NaN;
  if (isFinite(combineVal)) return combineVal;

  if (useProDay && proDayCol) {
    const pdVal = parseNum(row[proDayCol]);
    if (isFinite(pdVal)) return pdVal;
  }
  return NaN;
}

function getMeasurementSource(row, label, useProDay) {
  const cols = MEASUREMENTS[label] || ECM[label];
  if (!cols) return 'N/A';
  const [combineCol, proDayCol] = cols;
  if (combineCol && isFinite(parseNum(row[combineCol]))) return 'Combine';
  if (useProDay && proDayCol && isFinite(parseNum(row[proDayCol]))) return 'Pro Day';
  return 'N/A';
}

// ─── Draft Label ───────────────────────────────────────────────────────────────
function applyDraftedLabel(row, threshold) {
  if (row.year === 2026) {
    row._drafted_base = 'Unknown';
    return;
  }
  const drafted = (row.drafted || '').toString().trim().toLowerCase();
  if (drafted === 'true' || drafted === '1' || drafted === 'yes') {
    row._drafted_base = 'Drafted';
  } else if (drafted === 'false' || drafted === '0' || drafted === 'no') {
    const seasons = parseNum(row.career_seasons);
    if (isFinite(seasons) && threshold > 0 && seasons >= threshold) {
      row._drafted_base = 'Undrafted NFL';
    } else {
      row._drafted_base = 'Undrafted';
    }
  } else {
    row._drafted_base = 'Unknown';
  }
}

// ─── Number Parsing for All Rows ──────────────────────────────────────────────
const NUMERIC_COLS = [
  'year','draft_round','draft_pick',
  'combine_height','combine_weight','combine_arm_length','combine_hand_size',
  'combine_forty_yard_dash','combine_ten_yard_split','combine_bench_press',
  'combine_vertical_jump','combine_broad_jump','combine_three_cone_drill',
  'combine_twenty_yard_shuttle',
  'grade','draft_grade',
  'pro_day_height','pro_day_weight','pro_day_arm_length','pro_day_hand_size',
  'pro_day_forty_yard_dash','pro_day_ten_yard_split','pro_day_bench_press',
  'pro_day_vertical_jump','pro_day_broad_jump','pro_day_three_cone_drill',
  'pro_day_twenty_yard_shuttle','pro_day_wingspan',
  'career_seasons','nfl_rookie_season','nfl_last_season',
];

const PASSRUSH_NUMERIC_COLS = [
  'season','games_played','games_started','game_snaps','team_snaps',
  'pass_rush_snaps','pass_rush_rate','get_off_time','qb_pressures',
  'qb_pressure_rate','time_to_pressure','sacks','sack_rate','time_to_sack',
  'qb_defeats','turn_pressures',
];

function preprocessRow(row) {
  for (const col of NUMERIC_COLS) {
    if (col in row) row[col] = parseNum(row[col]);
  }
  // Position group mapping
  const rawPos = (row.position || '').toUpperCase().trim();
  row.pos_group = POS_TO_GROUP[rawPos] || row.position_group || rawPos || 'Unknown';
  // Name corrections / display name
  row._display = row.display_name || row.player || `${row.first_name || ''} ${row.last_name || ''}`.trim();
  return row;
}

function preprocessPassrushRow(row) {
  for (const col of PASSRUSH_NUMERIC_COLS) {
    if (col in row) row[col] = parseNum(row[col]);
  }
  // Apply name corrections
  const rawName = (row.name || '').trim();
  row._normName = PR_NAME_CORRECTIONS[rawName] || rawName;
  return row;
}

// ─── Percentile Computation ────────────────────────────────────────────────────
function computeAllPosPercentiles() {
  POS_PERCENTILES = {};
  for (const pg of POS_GROUP_ORDER) {
    POS_PERCENTILES[pg] = {};
    const draftedRows = RAW_DATA.filter(r => r.pos_group === pg && r._drafted_base === 'Drafted');
    for (const label of MEAS_LABELS) {
      const vals = draftedRows.map(r => resolveMeasurement(r, label, true)).filter(v => isFinite(v));
      POS_PERCENTILES[pg][label] = vals.sort((a, b) => a - b);
    }
  }
}

function calcPercentile(value, refValues, label) {
  if (!isFinite(value) || !refValues || refValues.length === 0) return NaN;
  let pct = percentileOfScore(refValues, value);
  if (LOWER_IS_BETTER.has(label)) pct = 100 - pct;
  return pct;
}

// ─── Merged Edge Data ──────────────────────────────────────────────────────────
function buildMergedEdgeData() {
  // Group passrush by normalized name: career aggregates
  const byName = {};
  for (const row of PASSRUSH_RAW) {
    const name = row._normName;
    if (!name) continue;
    if (!byName[name]) {
      byName[name] = {
        name,
        positions: new Set(),
        seasons: [],
        total_pr_snaps: 0,
        total_qbp: 0,
        total_sacks: 0,
        get_off_times: [],
        ttps: [],
      };
    }
    const b = byName[name];
    b.positions.add(row.position || '');
    b.total_pr_snaps += (isFinite(row.pass_rush_snaps) ? row.pass_rush_snaps : 0);
    b.total_qbp     += (isFinite(row.qb_pressures) ? row.qb_pressures : 0);
    b.total_sacks   += (isFinite(row.sacks) ? row.sacks : 0);
    if (isFinite(row.get_off_time) && row.get_off_time > 0) b.get_off_times.push(row.get_off_time);
    if (isFinite(row.time_to_pressure) && row.time_to_pressure > 0) b.ttps.push(row.time_to_pressure);
    b.seasons.push(row.season);
  }

  // Build career aggregated records
  const careerMap = {};
  for (const [name, b] of Object.entries(byName)) {
    const uniqueSeasons = new Set(b.seasons).size;
    if (uniqueSeasons === 0) continue;
    careerMap[name] = {
      career_qbpr:           b.total_pr_snaps > 0 ? (b.total_qbp / b.total_pr_snaps) * 100 : NaN,
      pressures_per_season:  b.total_qbp / uniqueSeasons,
      sacks_per_season:      b.total_sacks / uniqueSeasons,
      total_qbp:             b.total_qbp,
      total_sacks:           b.total_sacks,
      total_pr_snaps:        b.total_pr_snaps,
      avg_get_off:           b.get_off_times.length > 0 ? nanMean(b.get_off_times) : NaN,
      avg_ttp:               b.ttps.length > 0 ? nanMean(b.ttps) : NaN,
      pro_seasons:           uniqueSeasons,
      pro_positions:         [...b.positions].filter(Boolean).join('/'),
    };
  }

  // Join with combine data (Edge position group)
  MERGED_EDGE = [];
  const edgeRows = RAW_DATA.filter(r => r.pos_group === 'Edge');
  for (const row of edgeRows) {
    const name = row._display;
    const career = careerMap[name];
    if (!career) continue;
    if (career.total_pr_snaps === 0) continue;
    MERGED_EDGE.push({ ...row, ...career });
  }
}

function buildMergedEdgeSeasonData() {
  // Join combine with each season row
  MERGED_SEASON = [];
  const edgeRows = RAW_DATA.filter(r => r.pos_group === 'Edge');
  const combineByName = {};
  for (const row of edgeRows) {
    const name = row._display;
    if (!combineByName[name]) combineByName[name] = [];
    combineByName[name].push(row);
  }

  for (const prRow of PASSRUSH_RAW) {
    const name = prRow._normName;
    if (!name) continue;
    const combineRows = combineByName[name];
    if (!combineRows || combineRows.length === 0) continue;
    // Use first match (same player)
    const combineRow = combineRows[0];
    MERGED_SEASON.push({ ...combineRow, ...prRow, _display: name });
  }
}

// ─── Filtered Data ─────────────────────────────────────────────────────────────
function getFilteredData() {
  // Apply UDFA threshold first
  const allData = RAW_DATA.map(r => {
    const copy = { ...r };
    applyDraftedLabel(copy, STATE.udfaThreshold);
    return copy;
  });

  let dfBase = allData.filter(r => {
    const yr = r.year;
    if (!isFinite(yr) || yr < STATE.yearStart || yr > STATE.yearEnd) return false;
    if (!STATE.selectedPos.includes(r.pos_group)) return false;
    // Draft filter
    const db = r._drafted_base;
    if (STATE.draftFilter === 'drafted' && db !== 'Drafted') return false;
    if (STATE.draftFilter === 'undrafted' && db !== 'Undrafted' && db !== 'Undrafted NFL') return false;
    if (STATE.draftFilter === 'nfl' && db !== 'Drafted' && db !== 'Undrafted NFL') return false;
    return true;
  });

  // 2026 data filtered by position
  const df2026Base = DATA_2026.filter(r => STATE.selectedPos.includes(r.pos_group));

  return { dfBase, df2026Base };
}

// ─── Data Source Counting ──────────────────────────────────────────────────────
function countDataSource(df) {
  let combine = 0, proday = 0, none = 0;
  for (const row of df) {
    const src = getMeasurementSource(row, STATE.xLabel, STATE.useProDay);
    if (src === 'Combine') combine++;
    else if (src === 'Pro Day') proday++;
    else none++;
  }
  return { combine, proday, none };
}

// ─── Metric Cards ─────────────────────────────────────────────────────────────
function updateMetricCards(dfBase, df2026Base) {
  const drafted    = dfBase.filter(r => r._drafted_base === 'Drafted').length;
  const undrafted  = dfBase.filter(r => r._drafted_base === 'Undrafted' || r._drafted_base === 'Undrafted NFL').length;
  const total      = dfBase.length;
  const predraft   = STATE.show2026 ? df2026Base.length : 0;

  el('card-total').textContent    = total.toLocaleString();
  el('card-drafted').textContent  = drafted.toLocaleString();
  el('card-undrafted').textContent= undrafted.toLocaleString();
  el('card-predraft').textContent = predraft.toLocaleString();

  // Card labels
  el('card-total-label').textContent    = t('total_players');
  el('card-drafted-label').textContent  = t('drafted_metric');
  el('card-undrafted-label').textContent= t('undrafted_metric');
  el('card-predraft-label').textContent = t('predraft_metric');
  el('card-source-label').textContent   = t('source_metric');

  // Data source breakdown
  const src = countDataSource(dfBase);
  const hasProDay = src.proday > 0;
  el('card-source').textContent = hasProDay
    ? `Combine: ${src.combine} / Pro Day: ${src.proday}`
    : `Combine: ${src.combine}`;
}

// ─── Plot Symbol Helper ────────────────────────────────────────────────────────
function getSymbol(status) {
  if (status === 'Drafted')       return 'circle';
  if (status === 'Undrafted NFL') return 'triangle-up';
  if (status === 'Undrafted')     return 'x';
  return 'diamond';
}

function getMarkerColor(row, colorMode) {
  if (colorMode === 'round') {
    const rd = row.draft_round;
    if (isFinite(rd) && rd >= 1 && rd <= 7) return DRAFT_ROUND_COLORS[rd];
    if (row._drafted_base === 'Undrafted' || row._drafted_base === 'Undrafted NFL') return DRAFT_ROUND_COLORS['UDFA'];
    return THEME.muted;
  }
  return POS_COLORS[row.pos_group] || THEME.muted;
}

// ─── SCATTER PLOT ─────────────────────────────────────────────────────────────
function renderScatter() {
  const { dfBase, df2026Base } = getFilteredData();
  updateMetricCards(dfBase, df2026Base);

  const xLabel = STATE.xLabel;
  const yLabel = STATE.yLabel;
  const useProDay = STATE.useProDay;

  if (STATE.selectedPos.length === 0) {
    el('pos-warn').style.display = 'block';
    Plotly.react('scatter-plot', [], makePlotLayout());
    return;
  }
  el('pos-warn').style.display = 'none';

  const traces = [];

  // Group data by pos_group and drafted status
  const groups = {};
  for (const row of dfBase) {
    const xv = resolveMeasurement(row, xLabel, useProDay);
    const yv = resolveMeasurement(row, yLabel, useProDay);
    if (!isFinite(xv) || !isFinite(yv)) continue;

    const key = `${row.pos_group}__${row._drafted_base}`;
    if (!groups[key]) groups[key] = { rows: [], xs: [], ys: [] };
    groups[key].rows.push(row);
    groups[key].xs.push(xv);
    groups[key].ys.push(yv);
  }

  // Check if label warning needed
  const totalVisible = dfBase.length;
  let labelWarn = false;
  if (STATE.showAllLabels && totalVisible > LABEL_WARN_THRESHOLD) labelWarn = true;

  // Build main scatter traces grouped by pos_group x status
  const seenLegend = new Set();
  for (const pg of POS_GROUP_ORDER) {
    if (!STATE.selectedPos.includes(pg)) continue;
    for (const status of ['Drafted', 'Undrafted NFL', 'Undrafted', 'Unknown']) {
      const key = `${pg}__${status}`;
      const grp = groups[key];
      if (!grp || grp.rows.length === 0) continue;

      const color = getMarkerColor({ pos_group: pg, _drafted_base: status, draft_round: NaN }, STATE.colorMode);
      const symbol = getSymbol(status);
      const legendKey = STATE.colorMode === 'position' ? pg : status;

      const textArr = grp.rows.map(r => {
        if (STATE.highlightedPlayers.includes(r._display)) return r._display;
        if (STATE.showAllLabels && !labelWarn) return r._display;
        return '';
      });

      const isHighlighted = grp.rows.some(r => STATE.highlightedPlayers.includes(r._display));

      const hoverArr = grp.rows.map(r => {
        const xv = resolveMeasurement(r, xLabel, useProDay);
        const yv = resolveMeasurement(r, yLabel, useProDay);
        const src = getMeasurementSource(r, xLabel, useProDay);
        return [
          `<b>${r._display}</b>`,
          `Year: ${r.year} | ${r.pos_group} | ${r._drafted_base}`,
          `${xLabel}: ${formatNum(xv, 2)} (${src})`,
          `${yLabel}: ${formatNum(yv, 2)}`,
          r.draft_round && isFinite(r.draft_round) ? `Round ${r.draft_round}, Pick ${r.draft_pick || '—'}` : '',
          r.college ? `College: ${r.college}` : '',
        ].filter(Boolean).join('<br>');
      });

      const showLeg = !seenLegend.has(legendKey);
      if (showLeg) seenLegend.add(legendKey);

      const markerSizes = grp.rows.map(r => {
        return STATE.highlightedPlayers.includes(r._display) ? STATE.markerSize * 2.5 : STATE.markerSize;
      });

      traces.push({
        type: 'scatter',
        mode: STATE.showAllLabels && !labelWarn ? 'markers+text' : 'markers',
        x: grp.xs,
        y: grp.ys,
        text: textArr,
        textposition: 'top center',
        textfont: { size: 9, color: THEME.text },
        hovertemplate: '%{customdata}<extra></extra>',
        customdata: hoverArr,
        name: STATE.colorMode === 'position' ? pg : status,
        legendgroup: legendKey,
        showlegend: showLeg,
        marker: {
          color,
          symbol,
          size: markerSizes,
          opacity: STATE.opacity,
          line: { width: 0.5, color: 'rgba(0,0,0,0.3)' },
        },
      });
    }
  }

  // Highlighted player overlay (large markers with text)
  if (STATE.highlightedPlayers.length > 0) {
    const hlRows = [];
    for (const row of dfBase) {
      if (STATE.highlightedPlayers.includes(row._display)) {
        const xv = resolveMeasurement(row, xLabel, useProDay);
        const yv = resolveMeasurement(row, yLabel, useProDay);
        if (isFinite(xv) && isFinite(yv)) hlRows.push({ row, xv, yv });
      }
    }
    if (hlRows.length > 0) {
      traces.push({
        type: 'scatter',
        mode: 'markers+text',
        x: hlRows.map(d => d.xv),
        y: hlRows.map(d => d.yv),
        text: hlRows.map(d => d.row._display),
        textposition: 'top center',
        textfont: { size: 11, color: THEME.text_bright, family: 'Geist, sans-serif' },
        hoverinfo: 'skip',
        showlegend: false,
        marker: {
          color: hlRows.map(d => getMarkerColor(d.row, STATE.colorMode)),
          symbol: hlRows.map(d => getSymbol(d.row._drafted_base)),
          size: STATE.markerSize * 2.8,
          opacity: 1,
          line: { width: 2, color: THEME.accent },
        },
      });
    }
  }

  // 95% CI Ellipses
  if (STATE.showEllipse) {
    for (const pg of STATE.selectedPos) {
      const pgRows = dfBase.filter(r => r.pos_group === pg);
      const xs = pgRows.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
      const ys = pgRows.map(r => resolveMeasurement(r, yLabel, useProDay)).filter(isFinite);
      // We need pairs
      const pairs = pgRows.reduce((acc, r) => {
        const xv = resolveMeasurement(r, xLabel, useProDay);
        const yv = resolveMeasurement(r, yLabel, useProDay);
        if (isFinite(xv) && isFinite(yv)) acc.push([xv, yv]);
        return acc;
      }, []);
      if (pairs.length < MIN_SAMPLES_ELLIPSE) continue;
      const ell = confidenceEllipse(pairs.map(p => p[0]), pairs.map(p => p[1]));
      if (ell.x.length === 0) continue;
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: ell.x,
        y: ell.y,
        name: `${pg} ellipse`,
        legendgroup: pg,
        showlegend: false,
        line: { color: POS_COLORS[pg] || THEME.muted, width: 1.5, dash: 'dot' },
        hoverinfo: 'skip',
      });
    }
  }

  // 2026 Pre-Draft Overlay
  if (STATE.show2026 && df2026Base.length > 0) {
    const xs2026 = [], ys2026 = [], hover2026 = [];
    for (const row of df2026Base) {
      const xv = resolveMeasurement(row, xLabel, useProDay);
      const yv = resolveMeasurement(row, yLabel, useProDay);
      if (!isFinite(xv) || !isFinite(yv)) continue;
      xs2026.push(xv);
      ys2026.push(yv);
      hover2026.push([
        `<b>${row._display}</b> ⭐ 2026`,
        `${row.pos_group}`,
        `${xLabel}: ${formatNum(xv, 2)}`,
        `${yLabel}: ${formatNum(yv, 2)}`,
        row.nfl_comparison ? `Comp: ${row.nfl_comparison}` : '',
        row.draft_projection ? `Proj: ${row.draft_projection}` : '',
      ].filter(Boolean).join('<br>'));
    }
    if (xs2026.length > 0) {
      traces.push({
        type: 'scatter',
        mode: 'markers',
        x: xs2026,
        y: ys2026,
        name: '2026 Pre-Draft',
        showlegend: true,
        hovertemplate: '%{customdata}<extra></extra>',
        customdata: hover2026,
        marker: {
          color: PREDRAFT_COLOR,
          symbol: 'diamond-open',
          size: STATE.markerSize * 2,
          line: { width: 2, color: PREDRAFT_BORDER },
        },
      });
    }
  }

  const layout = makePlotLayout({
    xaxis: {
      title: xLabel,
      gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 },
      title_font: { color: THEME.label },
    },
    yaxis: {
      title: yLabel,
      gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 },
      title_font: { color: THEME.label },
    },
  });

  Plotly.react('scatter-plot', traces, layout, { responsive: true, displayModeBar: false });

  // Stats panel
  if (STATE.showStats) {
    el('stats-panel-wrap').style.display = 'block';
    renderStatsPanel(dfBase);
    renderBoxPlot(dfBase);
  } else {
    el('stats-panel-wrap').style.display = 'none';
  }
}

// ─── Stats Panel ──────────────────────────────────────────────────────────────
function renderStatsPanel(df) {
  const xLabel = STATE.xLabel;
  const yLabel = STATE.yLabel;
  const useProDay = STATE.useProDay;

  const grid = el('stats-grid');
  grid.innerHTML = '';

  for (const pg of STATE.selectedPos) {
    const rows = df.filter(r => r.pos_group === pg);
    if (rows.length < MIN_SAMPLES_STATS) continue;

    const drafted   = rows.filter(r => r._drafted_base === 'Drafted');
    const undrafted = rows.filter(r => r._drafted_base === 'Undrafted' || r._drafted_base === 'Undrafted NFL');

    const dXs = drafted.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
    const dYs = drafted.map(r => resolveMeasurement(r, yLabel, useProDay)).filter(isFinite);
    const uXs = undrafted.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
    const uYs = undrafted.map(r => resolveMeasurement(r, yLabel, useProDay)).filter(isFinite);
    const allXs = rows.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
    const allYs = rows.map(r => resolveMeasurement(r, yLabel, useProDay)).filter(isFinite);

    const pval = dXs.length >= 5 && uXs.length >= 5 ? mannWhitneyU(dXs, uXs) : null;
    const pearX = pearsonR(allXs, allYs);

    const sig = pval !== null && pval < 0.05;
    const sigBadge = pval !== null
      ? `<span class="badge ${sig ? 'badge-green' : 'badge-muted'}">${sig ? '★ p=' + fmtPval(pval) : 'p=' + fmtPval(pval)}</span>`
      : '';

    const card = document.createElement('div');
    card.className = 'stats-card';
    card.style.borderLeft = `3px solid ${POS_COLORS[pg] || THEME.muted}`;
    card.innerHTML = `
      <div class="stats-card-title">${pg} <span style="font-size:0.75rem;color:${THEME.muted}">(n=${rows.length})</span></div>
      <div class="stats-row">
        <div class="stats-col">
          <div class="stats-label">Drafted (${dXs.length})</div>
          <div>X med: <b>${formatNum(nanMedian(dXs), 2)}</b></div>
          <div>Y med: <b>${formatNum(nanMedian(dYs), 2)}</b></div>
        </div>
        <div class="stats-col">
          <div class="stats-label">Undrafted (${uXs.length})</div>
          <div>X med: <b>${formatNum(nanMedian(uXs), 2)}</b></div>
          <div>Y med: <b>${formatNum(nanMedian(uYs), 2)}</b></div>
        </div>
      </div>
      <div class="stats-footer">
        MW test (X): ${sigBadge || '—'}
        &nbsp;|&nbsp; r(X,Y): <b>${isFinite(pearX?.r) ? pearX.r.toFixed(3) : '—'}</b>
      </div>
    `;
    grid.appendChild(card);
  }
}

// ─── Box Plot ─────────────────────────────────────────────────────────────────
function renderBoxPlot(df) {
  const expander = el('boxplot-expander');
  if (!expander.open) return;

  const xLabel = STATE.xLabel;
  const useProDay = STATE.useProDay;

  const infoDiv = el('boxplot-info');
  if (STATE.draftFilter !== 'all') {
    infoDiv.style.display = 'block';
    Plotly.react('boxplot-plot', [], makePlotLayout({ height: 480 }));
    return;
  }
  infoDiv.style.display = 'none';

  const traces = [];
  for (const status of ['Drafted', 'Undrafted']) {
    const vals = {};
    for (const row of df) {
      if (row._drafted_base !== status && !(status === 'Undrafted' && row._drafted_base === 'Undrafted NFL')) continue;
      const pg = row.pos_group;
      if (!vals[pg]) vals[pg] = [];
      const v = resolveMeasurement(row, xLabel, useProDay);
      if (isFinite(v)) vals[pg].push(v);
    }
    for (const pg of STATE.selectedPos) {
      if (!vals[pg] || vals[pg].length < 3) continue;
      traces.push({
        type: 'box',
        y: vals[pg],
        name: `${pg} / ${status}`,
        boxpoints: 'outliers',
        marker: { color: status === 'Drafted' ? POS_COLORS[pg] : THEME.muted, size: 3 },
        line: { width: 1.5 },
      });
    }
  }

  const layout = makePlotLayout({
    yaxis: { title: xLabel },
    legend: { orientation: 'h', y: -0.2 },
    margin: { t: 20, b: 120, l: 50, r: 20 },
  });

  Plotly.react('boxplot-plot', traces, layout, { responsive: true, displayModeBar: false });
}

// ─── HISTOGRAM ────────────────────────────────────────────────────────────────
function renderHistogram() {
  const { dfBase, df2026Base } = getFilteredData();
  const xLabel  = STATE.xLabel;
  const useProDay = STATE.useProDay;

  const traces = [];

  for (const pg of STATE.selectedPos) {
    const rows = dfBase.filter(r => r.pos_group === pg);
    if (rows.length < 3) continue;

    const color = POS_COLORS[pg] || THEME.muted;

    if (STATE.histSplit) {
      for (const [status, opacity] of [['Drafted', 0.75], ['Undrafted', 0.45]]) {
        const subset = rows.filter(r =>
          r._drafted_base === status || (status === 'Undrafted' && r._drafted_base === 'Undrafted NFL')
        );
        if (subset.length < 3) continue;
        const vals = subset.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
        traces.push({
          type: 'histogram',
          x: vals,
          name: `${pg} ${status}`,
          legendgroup: `${pg}-${status}`,
          autobinx: false,
          xbins: { size: (nanMax(vals) - nanMin(vals)) / HIST_BINS || 1 },
          histnorm: 'probability density',
          marker: { color, opacity },
          hovertemplate: `${pg} ${status}<br>%{x:.2f}<br>Density: %{y:.4f}<extra></extra>`,
        });
      }
    } else {
      const vals = rows.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
      if (vals.length < 3) continue;
      traces.push({
        type: 'histogram',
        x: vals,
        name: pg,
        legendgroup: pg,
        autobinx: false,
        xbins: { size: (nanMax(vals) - nanMin(vals)) / HIST_BINS || 1 },
        histnorm: 'probability density',
        marker: { color, opacity: 0.65 },
        hovertemplate: `${pg}<br>%{x:.2f}<br>Density: %{y:.4f}<extra></extra>`,
      });
    }
  }

  // 2026 KDE dashed lines per position
  if (STATE.show2026kde && df2026Base.length > 0) {
    for (const pg of STATE.selectedPos) {
      const rows2026 = df2026Base.filter(r => r.pos_group === pg);
      if (rows2026.length < MIN_KDE_SAMPLES) continue;
      const vals = rows2026.map(r => resolveMeasurement(r, xLabel, useProDay)).filter(isFinite);
      if (vals.length < MIN_KDE_SAMPLES) continue;

      const allVals = dfBase
        .filter(r => r.pos_group === pg)
        .map(r => resolveMeasurement(r, xLabel, useProDay))
        .filter(isFinite);

      const minV = nanMin([...allVals, ...vals]);
      const maxV = nanMax([...allVals, ...vals]);
      if (!isFinite(minV) || !isFinite(maxV)) continue;

      const nPts = 100;
      const evalPts = Array.from({ length: nPts }, (_, i) => minV + (i / (nPts - 1)) * (maxV - minV));
      const kde = gaussianKDE(vals, evalPts, KDE_BANDWIDTH);

      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: evalPts,
        y: kde,
        name: `${pg} 2026 KDE`,
        legendgroup: pg,
        showlegend: true,
        line: { color: PREDRAFT_COLOR, width: 2, dash: 'dash' },
        hovertemplate: `${pg} 2026<br>${xLabel}: %{x:.2f}<br>Density: %{y:.4f}<extra></extra>`,
      });
    }
  }

  // Highlighted players as vertical dashed lines
  for (const playerName of STATE.highlightedPlayers) {
    const row = dfBase.find(r => r._display === playerName)
               || df2026Base.find(r => r._display === playerName);
    if (!row) continue;
    const xv = resolveMeasurement(row, xLabel, useProDay);
    if (!isFinite(xv)) continue;

    traces.push({
      type: 'scatter',
      mode: 'lines',
      x: [xv, xv],
      y: [0, 1],
      yaxis: 'y',
      name: playerName,
      showlegend: true,
      line: { color: THEME.accent, width: 2, dash: 'dashdot' },
      hovertemplate: `<b>${playerName}</b><br>${xLabel}: ${formatNum(xv, 2)}<extra></extra>`,
    });
  }

  const layout = makePlotLayout({
    barmode: 'overlay',
    xaxis: {
      title: xLabel,
      gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label },
    },
    yaxis: {
      title: t('density'),
      gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label },
      rangemode: 'tozero',
    },
    margin: { t: 20, b: 160, l: 60, r: 20 },
  });

  Plotly.react('histogram-plot', traces, layout, { responsive: true, displayModeBar: false });
}

// ─── PLAYER COMPARISON ────────────────────────────────────────────────────────
function findSimilarPlayers(playerRow, df, posGroup, n) {
  const pg = posGroup;
  // Gather all measurement labels that have finite values for the player
  const availLabels = MEAS_LABELS.filter(lbl => {
    const v = resolveMeasurement(playerRow, lbl, true);
    return isFinite(v);
  });

  if (availLabels.length === 0) return [];

  // Compute mean and std for z-score normalization
  const stats = {};
  for (const lbl of availLabels) {
    const allVals = df
      .filter(r => r.pos_group === pg && r._display !== playerRow._display)
      .map(r => resolveMeasurement(r, lbl, true))
      .filter(isFinite);
    const mu  = nanMean(allVals);
    const sig = nanStd(allVals);
    stats[lbl] = { mu, sig: sig || 1 };
  }

  // Compute distance to every candidate
  const candidates = df.filter(r =>
    r.pos_group === pg &&
    r._display !== playerRow._display &&
    r.year !== 2026
  );

  const scored = [];
  for (const cand of candidates) {
    let sumSqDist = 0;
    let count = 0;
    for (const lbl of availLabels) {
      const pv = resolveMeasurement(playerRow, lbl, true);
      const cv = resolveMeasurement(cand, lbl, true);
      if (!isFinite(cv)) continue;
      const zP = (pv - stats[lbl].mu) / stats[lbl].sig;
      const zC = (cv - stats[lbl].mu) / stats[lbl].sig;
      sumSqDist += (zP - zC) ** 2;
      count++;
    }
    if (count < 2) continue;
    const dist = Math.sqrt(sumSqDist / count);
    const similarity = Math.max(0, 100 - dist * 15);
    scored.push({ row: cand, dist, similarity });
  }

  scored.sort((a, b) => a.dist - b.dist);
  return scored.slice(0, n);
}

function renderCompare() {
  const allData = [...RAW_DATA, ...DATA_2026].map(r => {
    const copy = { ...r };
    applyDraftedLabel(copy, STATE.udfaThreshold);
    return copy;
  });

  // ── Radar Chart ──────────────────────────────────────────────────────────────
  const comparePlayers = STATE.comparePlayers;
  const cmpNoData = el('cmp-no-data');
  const radarPlot = el('radar-plot');
  const cmpNote = el('cmp-note');
  const cmpTableWrap = el('cmp-table-wrap');

  if (comparePlayers.length === 0) {
    cmpNoData.style.display = 'block';
    radarPlot.style.display = 'none';
    cmpNote.style.display = 'none';
    cmpTableWrap.style.display = 'none';
    Plotly.react('radar-plot', [], {});
  } else {
    cmpNoData.style.display = 'none';
    radarPlot.style.display = 'block';
    cmpNote.style.display = 'block';
    cmpTableWrap.style.display = 'block';

    // Find rows for selected players
    const playerRows = comparePlayers.map(name =>
      allData.find(r => r._display === name)
    ).filter(Boolean);

    if (playerRows.length === 0) {
      cmpNoData.style.display = 'block';
      radarPlot.style.display = 'none';
      return;
    }

    // Find shared measurements
    const sharedLabels = MEAS_LABELS.filter(lbl =>
      playerRows.some(r => isFinite(resolveMeasurement(r, lbl, true)))
    );

    const radarColors = ['#58A6FF', '#FF7B72', '#3FB950', '#D2A8FF'];
    const radarTraces = [];

    for (let i = 0; i < playerRows.length; i++) {
      const row = playerRows[i];
      const pg  = row.pos_group;
      const refVals = POS_PERCENTILES[pg] || {};

      const pcts = sharedLabels.map(lbl => {
        const v = resolveMeasurement(row, lbl, true);
        const ref = refVals[lbl] || [];
        return calcPercentile(v, ref, lbl);
      });

      // Close the radar
      const rLabels = [...sharedLabels, sharedLabels[0]];
      const rPcts   = [...pcts, pcts[0]];

      radarTraces.push({
        type: 'scatterpolar',
        r: rPcts,
        theta: rLabels,
        fill: 'toself',
        name: row._display,
        line: { color: radarColors[i % radarColors.length], width: 2 },
        fillcolor: radarColors[i % radarColors.length].replace(')', ',0.15)').replace('rgb', 'rgba').replace('#', 'rgba(').replace('rgba(', 'rgba('),
        opacity: 0.85,
        hovertemplate: '%{theta}<br>Percentile: %{r:.1f}<extra>' + row._display + '</extra>',
      });
    }

    const polarLayout = {
      paper_bgcolor: THEME.bg,
      plot_bgcolor:  THEME.card_bg,
      font: { color: THEME.text, family: 'Geist, -apple-system, sans-serif' },
      polar: {
        bgcolor: THEME.card_bg,
        radialaxis: {
          visible: true, range: [0, 100],
          gridcolor: THEME.grid, linecolor: THEME.border,
          tickfont: { color: THEME.muted, size: 10 },
          ticksuffix: '%',
        },
        angularaxis: {
          gridcolor: THEME.grid, linecolor: THEME.border,
          tickfont: { color: THEME.label, size: 10 },
        },
      },
      legend: {
        orientation: 'h', yanchor: 'top', y: -0.08, xanchor: 'left', x: 0,
        bgcolor: 'rgba(22,27,34,0.85)', bordercolor: THEME.border, borderwidth: 1,
        font: { size: 11, color: THEME.text },
      },
      margin: { t: 30, b: 60, l: 40, r: 40 },
    };

    Plotly.react('radar-plot', radarTraces, polarLayout, { responsive: true, displayModeBar: false });

    // ── Measurement Table ──────────────────────────────────────────────────────
    const thead = el('cmp-thead');
    const tbody = el('cmp-tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    const thRow = document.createElement('tr');
    thRow.innerHTML = '<th>Measurement</th>' +
      playerRows.map(r => `<th>${r._display}<br><small>${r.year} · ${r.pos_group}</small></th>`).join('');
    thead.appendChild(thRow);

    for (const lbl of sharedLabels) {
      const tr = document.createElement('tr');
      let cells = `<td>${lbl}</td>`;
      for (const row of playerRows) {
        const v = resolveMeasurement(row, lbl, true);
        const pg = row.pos_group;
        const ref = POS_PERCENTILES[pg]?.[lbl] || [];
        const pct = calcPercentile(v, ref, lbl);
        const pctText = isFinite(pct) ? ` <small style="color:${THEME.muted}">(${pct.toFixed(0)}th)</small>` : '';
        cells += `<td>${isFinite(v) ? formatNum(v, 2) : '—'}${pctText}</td>`;
      }
      tr.innerHTML = cells;
      tbody.appendChild(tr);
    }
  }

  // ── Similar Players ────────────────────────────────────────────────────────
  const simNoData   = el('sim-no-data');
  const simContent  = el('sim-result-content');
  const simCaption  = el('sim-caption');
  const simThead    = el('sim-thead');
  const simTbody    = el('sim-tbody');

  if (!STATE.simPlayer) {
    simNoData.style.display = 'block';
    simContent.style.display = 'none';
  } else {
    const targetRow = allData.find(r => r._display === STATE.simPlayer);
    if (!targetRow) {
      simNoData.style.display = 'block';
      simContent.style.display = 'none';
    } else {
      simNoData.style.display = 'none';
      simContent.style.display = 'block';

      const pg = targetRow.pos_group;
      const pgRows = RAW_DATA.map(r => {
        const copy = { ...r };
        applyDraftedLabel(copy, STATE.udfaThreshold);
        return copy;
      }).filter(r => r.pos_group === pg);

      const similar = findSimilarPlayers(targetRow, pgRows, pg, STATE.simN);

      simCaption.textContent = `${t('similar_header')}: ${STATE.simPlayer} (${pg}, ${targetRow.year})`;

      // Table headers
      const keyMeasLabels = MEAS_LABELS.filter(lbl =>
        isFinite(resolveMeasurement(targetRow, lbl, true))
      ).slice(0, 5);

      simThead.innerHTML = '';
      simTbody.innerHTML = '';

      const htr = document.createElement('tr');
      htr.innerHTML = '<th>Player</th><th>Year</th><th>College</th><th>Status</th><th>Round</th><th>Similarity</th>'
        + keyMeasLabels.map(l => `<th>${l}</th>`).join('');
      simThead.appendChild(htr);

      for (const { row, similarity } of similar) {
        const tr = document.createElement('tr');
        const rd = isFinite(row.draft_round) ? `Rd ${row.draft_round}` : (row._drafted_base === 'Undrafted' ? 'UDFA' : '—');
        let cells = `<td>${row._display}</td><td>${row.year}</td><td>${row.college || '—'}</td><td>${row._drafted_base}</td><td>${rd}</td>`;
        cells += `<td><b>${similarity.toFixed(1)}%</b></td>`;
        for (const lbl of keyMeasLabels) {
          const v = resolveMeasurement(row, lbl, true);
          cells += `<td>${isFinite(v) ? formatNum(v, 2) : '—'}</td>`;
        }
        tr.innerHTML = cells;
        simTbody.appendChild(tr);
      }
    }
  }
}

// ─── PRO PERFORMANCE ──────────────────────────────────────────────────────────
function getProFilteredData() {
  const isCareer = STATE.proAggMode === 'career';
  const srcData  = isCareer ? MERGED_EDGE : MERGED_SEASON;

  const xLabel    = isCareer ? STATE.proXLabel : STATE.proXLabel;
  const yLabel    = isCareer ? STATE.proYLabel : STATE.proYLabel;
  const ppmMap    = isCareer ? PPM : PPM_SEASON;
  const yCols     = ppmMap[yLabel];
  const yCol      = yCols ? yCols[0] : null;

  const minSnaps  = isCareer ? STATE.proMinSnaps : STATE.proMinSnaps;
  const posFilter = STATE.proPosFilter;
  const yrStart   = STATE.proYearStart;
  const yrEnd     = STATE.proYearEnd;

  return srcData.filter(row => {
    // Year filter on draft year
    const yr = row.year;
    if (!isFinite(yr) || yr < yrStart || yr > yrEnd) return false;
    // Position filter
    const pos = (row.position || row.pos_group || '').toUpperCase();
    if (posFilter.length > 0 && !posFilter.some(p => pos.includes(p.toUpperCase()))) return false;
    // Snaps filter
    const snaps = isCareer ? row.total_pr_snaps : row.pass_rush_snaps;
    if (!isFinite(snaps) || snaps < minSnaps) return false;
    // Must have valid X and Y
    const xv = resolveMeasurement(row, xLabel, STATE.proUseProDay);
    if (!isFinite(xv)) return false;
    if (yCol && !isFinite(row[yCol])) return false;
    return true;
  });
}

function getHmFilteredData() {
  const srcData = MERGED_EDGE;
  const posFilter = STATE.hmPosFilter;
  const yrStart   = STATE.hmYearStart;
  const yrEnd     = STATE.hmYearEnd;
  const minSnaps  = STATE.hmMinSnaps;
  const ppmMap    = STATE.proAggMode === 'career' ? PPM : PPM_SEASON;
  const zLabel    = STATE.hmZLabel;
  const zCols     = ppmMap[zLabel];
  const zCol      = zCols ? zCols[0] : null;

  return srcData.filter(row => {
    const yr = row.year;
    if (!isFinite(yr) || yr < yrStart || yr > yrEnd) return false;
    const pos = (row.position || '').toUpperCase();
    if (posFilter.length > 0 && !posFilter.some(p => pos.includes(p.toUpperCase()))) return false;
    const snaps = row.total_pr_snaps;
    if (!isFinite(snaps) || snaps < minSnaps) return false;
    const xv = resolveMeasurement(row, STATE.hmXLabel, STATE.hmUseProDay);
    const yv = resolveMeasurement(row, STATE.hmYLabel, STATE.hmUseProDay);
    if (!isFinite(xv) || !isFinite(yv)) return false;
    if (zCol && !isFinite(row[zCol])) return false;
    return true;
  });
}

function renderPro() {
  // Show/hide no-data warning
  const noFileWarn = el('pro-no-file-warn');
  const proContent = el('pro-content');

  if (PASSRUSH_RAW.length === 0) {
    noFileWarn.style.display = 'flex';
    proContent.style.display = 'none';
    return;
  }
  noFileWarn.style.display = 'none';
  proContent.style.display = 'block';

  // Update matched counts
  el('pro-matched-val').textContent = MERGED_EDGE.length.toLocaleString();
  el('pro-seasons-val').textContent  = MERGED_SEASON.length.toLocaleString();

  if (STATE.proViewMode === 'scatter') {
    el('pro-scatter-controls').style.display  = '';
    el('pro-heatmap-controls').style.display  = 'none';
    el('pro-scatter-stats').style.display     = '';
    el('pro-heatmap-stats').style.display     = 'none';
    el('thresh-expander').style.display       = '';
    el('pro-table-expander').style.display    = '';
    renderProScatter();
  } else {
    el('pro-scatter-controls').style.display  = 'none';
    el('pro-heatmap-controls').style.display  = '';
    el('pro-scatter-stats').style.display     = 'none';
    el('pro-heatmap-stats').style.display     = '';
    el('thresh-expander').style.display       = 'none';
    el('pro-table-expander').style.display    = 'none';
    renderProHeatmap();
  }
}

function renderProScatter() {
  const isCareer  = STATE.proAggMode === 'career';
  const ppmMap    = isCareer ? PPM : PPM_SEASON;
  const xLabel    = STATE.proXLabel;
  const yLabel    = STATE.proYLabel;
  const yCols     = ppmMap[yLabel];
  const yCol      = yCols ? yCols[0] : null;
  const yLower    = yCols ? yCols[1] : false;

  const filtered = getProFilteredData();

  if (filtered.length < 3) {
    const msg = t('pro_no_data').replace('{n}', filtered.length);
    Plotly.react('pro-plot', [{
      type: 'scatter', mode: 'text',
      x: [0.5], y: [0.5], text: [msg],
      textfont: { color: THEME.muted, size: 14 },
    }], makePlotLayout(), { responsive: true, displayModeBar: false });
    ['pro-n-val','pro-r-val','pro-r2-val','pro-pval-val','pro-slope-val'].forEach(id => el(id).textContent = '—');
    el('pro-pval-sig').textContent = '—';
    return;
  }

  const xs = filtered.map(r => resolveMeasurement(r, xLabel, STATE.proUseProDay));
  const ys = filtered.map(r => yCol ? r[yCol] : NaN);

  // Regression
  const reg = linregress(xs, ys);
  if (reg) {
    el('pro-n-val').textContent     = filtered.length;
    el('pro-r-val').textContent     = reg.r.toFixed(3);
    el('pro-r2-val').textContent    = reg.r2.toFixed(3);
    el('pro-pval-val').textContent  = fmtPval(reg.pvalue);
    el('pro-pval-sig').textContent  = reg.pvalue < 0.05 ? t('pro_sig') : t('pro_not_sig');
    el('pro-slope-val').textContent = reg.slope.toFixed(4);
  }

  const traces = [];

  // Color scale
  if (STATE.proColorBy === 'year') {
    const years = filtered.map(r => r.year);
    const minYr = nanMin(years), maxYr = nanMax(years);
    const snaps = isCareer
      ? filtered.map(r => r.total_pr_snaps)
      : filtered.map(r => r.pass_rush_snaps);

    traces.push({
      type: 'scatter',
      mode: 'markers',
      x: xs,
      y: ys,
      hovertemplate: filtered.map((r, i) =>
        `<b>${r._display}</b><br>${xLabel}: ${formatNum(xs[i], 2)}<br>${yLabel}: ${formatNum(ys[i], 2)}<br>Year: ${r.year}<br>Pos: ${r.position || ''}${isCareer ? `<br>PR Snaps: ${r.total_pr_snaps}` : `<br>Season: ${r.season}`}<extra></extra>`
      ),
      showlegend: false,
      marker: {
        color: years,
        colorscale: 'Plasma',
        cmin: minYr, cmax: maxYr,
        size: snaps.map(s => Math.max(5, Math.sqrt(isFinite(s) ? s : 0) * 0.5)),
        opacity: 0.8,
        colorbar: { title: 'Draft Year', thickness: 12, len: 0.6, tickfont: { color: THEME.muted, size: 10 }, titlefont: { color: THEME.label, size: 11 } },
        line: { width: 0.5, color: 'rgba(0,0,0,0.3)' },
      },
    });
  } else {
    // Color by position
    const posSet = [...new Set(filtered.map(r => r.position || r.pos_group || ''))];
    const posColorMap = {};
    const palette = Object.values(POS_COLORS);
    posSet.forEach((p, i) => { posColorMap[p] = palette[i % palette.length]; });

    const byPos = {};
    filtered.forEach((r, i) => {
      const pos = r.position || r.pos_group || '';
      if (!byPos[pos]) byPos[pos] = { rows: [], xs: [], ys: [] };
      byPos[pos].rows.push(r);
      byPos[pos].xs.push(xs[i]);
      byPos[pos].ys.push(ys[i]);
    });

    for (const [pos, d] of Object.entries(byPos)) {
      const snaps = isCareer
        ? d.rows.map(r => r.total_pr_snaps)
        : d.rows.map(r => r.pass_rush_snaps);
      traces.push({
        type: 'scatter', mode: 'markers',
        x: d.xs, y: d.ys,
        name: pos, showlegend: true,
        hovertemplate: d.rows.map((r, i) =>
          `<b>${r._display}</b><br>${xLabel}: ${formatNum(d.xs[i], 2)}<br>${yLabel}: ${formatNum(d.ys[i], 2)}<br>Pos: ${pos}<extra></extra>`
        ),
        marker: {
          color: posColorMap[pos],
          size: snaps.map(s => Math.max(5, Math.sqrt(isFinite(s) ? s : 0) * 0.5)),
          opacity: 0.8,
          line: { width: 0.5, color: 'rgba(0,0,0,0.3)' },
        },
      });
    }
  }

  // OLS regression line + 95% CI band
  if (reg) {
    const xMin = nanMin(xs), xMax = nanMax(xs);
    const nPts = 50;
    const regXs = Array.from({ length: nPts }, (_, i) => xMin + (i / (nPts - 1)) * (xMax - xMin));
    const regYs = regXs.map(x => reg.slope * x + reg.intercept);

    // SE for prediction interval
    const n  = filtered.length;
    const xm = nanMean(xs);
    const sxx = xs.reduce((s, x) => s + (x - xm) ** 2, 0);
    const se = reg.stderr * Math.sqrt(sxx);

    const ciUpper = regXs.map((x, i) => regYs[i] + 1.96 * reg.stderr * Math.sqrt(1 / n + (x - xm) ** 2 / (sxx + 1e-20)));
    const ciLower = regXs.map((x, i) => regYs[i] - 1.96 * reg.stderr * Math.sqrt(1 / n + (x - xm) ** 2 / (sxx + 1e-20)));

    // CI band
    traces.push({
      type: 'scatter', mode: 'lines',
      x: [...regXs, ...regXs.slice().reverse()],
      y: [...ciUpper, ...ciLower.slice().reverse()],
      fill: 'toself',
      fillcolor: 'rgba(88,166,255,0.10)',
      line: { width: 0 },
      showlegend: false, hoverinfo: 'skip', name: '95% CI',
    });

    // Regression line
    traces.push({
      type: 'scatter', mode: 'lines',
      x: regXs, y: regYs,
      name: `OLS (r=${reg.r.toFixed(2)})`,
      line: { color: THEME.accent, width: 2 },
      hoverinfo: 'skip',
    });

    // Median crosshairs
    const xMed = nanMedian(xs), yMed = nanMedian(ys);
    traces.push({
      type: 'scatter', mode: 'lines',
      x: [xMed, xMed], y: [nanMin(ys) * 0.9, nanMax(ys) * 1.1],
      line: { color: THEME.muted, width: 1, dash: 'dash' },
      showlegend: false, hoverinfo: 'skip', name: 'X median',
    });
    traces.push({
      type: 'scatter', mode: 'lines',
      x: [nanMin(xs) * 0.99, nanMax(xs) * 1.01], y: [yMed, yMed],
      line: { color: THEME.muted, width: 1, dash: 'dash' },
      showlegend: false, hoverinfo: 'skip', name: 'Y median',
    });

    // 4-quadrant annotations
    const q1Label = '✅ High-High';  // x >= med, y >= med
    const q2Label = '⚠️ Low-High';   // x < med, y >= med
    const q3Label = '❌ Low-Low';    // x < med, y < med
    const q4Label = 'ℹ️ High-Low';   // x >= med, y < med

    const xRange = [nanMin(xs), nanMax(xs)];
    const yRange = [nanMin(ys), nanMax(ys)];
    const quadAnns = [
      { x: (xMed + xRange[1]) / 2, y: (yMed + yRange[1]) / 2, text: q1Label },
      { x: (xRange[0] + xMed) / 2, y: (yMed + yRange[1]) / 2, text: q2Label },
      { x: (xRange[0] + xMed) / 2, y: (yRange[0] + yMed) / 2, text: q3Label },
      { x: (xMed + xRange[1]) / 2, y: (yRange[0] + yMed) / 2, text: q4Label },
    ];

    const layout = makePlotLayout({
      xaxis: {
        title: xLabel,
        gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
        tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label },
      },
      yaxis: {
        title: yLabel,
        gridcolor: THEME.grid, linecolor: THEME.border, zerolinecolor: THEME.border,
        tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label },
      },
      annotations: quadAnns.map(a => ({
        x: a.x, y: a.y, text: a.text, showarrow: false,
        font: { color: THEME.muted, size: 11 }, xref: 'x', yref: 'y',
        bgcolor: 'rgba(13,17,23,0.5)',
      })),
    });

    Plotly.react('pro-plot', traces, layout, { responsive: true, displayModeBar: false });
  } else {
    const layout = makePlotLayout({
      xaxis: { title: xLabel, gridcolor: THEME.grid, linecolor: THEME.border, tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label } },
      yaxis: { title: yLabel, gridcolor: THEME.grid, linecolor: THEME.border, tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label } },
    });
    Plotly.react('pro-plot', traces, layout, { responsive: true, displayModeBar: false });
  }

  // Threshold analysis
  renderThresholdAnalysis(filtered, xs, ys, xLabel, yLabel, yLower);

  // Data table
  renderProDataTable(filtered, xLabel, yLabel, xs, ys);
}

function renderThresholdAnalysis(filtered, xs, ys, xLabel, yLabel, yLower) {
  const slider = el('thresh-slider');
  if (!slider) return;

  const validPairs = [];
  for (let i = 0; i < filtered.length; i++) {
    if (isFinite(xs[i]) && isFinite(ys[i])) validPairs.push({ x: xs[i], y: ys[i], row: filtered[i] });
  }
  if (validPairs.length < 5) return;

  const xMin = nanMin(validPairs.map(p => p.x));
  const xMax = nanMax(validPairs.map(p => p.x));
  const xMed = nanMedian(validPairs.map(p => p.x));
  const yMed = nanMedian(validPairs.map(p => p.y));

  // Set slider range
  slider.min  = xMin.toFixed(4);
  slider.max  = xMax.toFixed(4);
  slider.step = ((xMax - xMin) / 100).toFixed(4);
  if (STATE.proThreshold === null || STATE.proThreshold < xMin || STATE.proThreshold > xMax) {
    STATE.proThreshold = xMed;
    slider.value = xMed;
  }
  el('thresh-val').textContent = formatNum(STATE.proThreshold, 2);

  const thresh = STATE.proThreshold;
  const above  = validPairs.filter(p => p.x >= thresh);
  const below  = validPairs.filter(p => p.x < thresh);

  function successRate(pairs) {
    if (pairs.length === 0) return { rate: NaN, n: 0, mean: NaN, median: NaN };
    const yVals = pairs.map(p => p.y);
    const successes = yLower
      ? pairs.filter(p => p.y <= yMed).length
      : pairs.filter(p => p.y >= yMed).length;
    return {
      rate:   (successes / pairs.length) * 100,
      n:      pairs.length,
      mean:   nanMean(yVals),
      median: nanMedian(yVals),
    };
  }

  const sa = successRate(above);
  const sb = successRate(below);

  const aboveBox = el('thresh-above');
  const belowBox = el('thresh-below');

  aboveBox.innerHTML = `
    <div style="font-weight:600;margin-bottom:4px">${t('pro_above')} (≥${formatNum(thresh,2)})</div>
    <div style="font-size:1.4rem;font-weight:700;color:${THEME.accent}">${isFinite(sa.rate) ? sa.rate.toFixed(1) + '%' : '—'}</div>
    <div style="font-size:0.8rem;color:${THEME.muted}">${t('pro_success')}</div>
    <div style="margin-top:6px;font-size:0.85rem">
      <span>${t('pro_players')}: <b>${sa.n}</b></span><br>
      <span>${t('pro_avg')}: <b>${formatNum(sa.mean,2)}</b></span><br>
      <span>${t('pro_med')}: <b>${formatNum(sa.median,2)}</b></span>
    </div>
  `;
  belowBox.innerHTML = `
    <div style="font-weight:600;margin-bottom:4px">${t('pro_below')} (<${formatNum(thresh,2)})</div>
    <div style="font-size:1.4rem;font-weight:700;color:${THEME.muted}">${isFinite(sb.rate) ? sb.rate.toFixed(1) + '%' : '—'}</div>
    <div style="font-size:0.8rem;color:${THEME.muted}">${t('pro_success')}</div>
    <div style="margin-top:6px;font-size:0.85rem">
      <span>${t('pro_players')}: <b>${sb.n}</b></span><br>
      <span>${t('pro_avg')}: <b>${formatNum(sb.mean,2)}</b></span><br>
      <span>${t('pro_med')}: <b>${formatNum(sb.median,2)}</b></span>
    </div>
  `;

  // Conclusion text
  const concl = el('thresh-conclusion');
  if (isFinite(sa.rate) && isFinite(sb.rate)) {
    const diff = sa.rate - sb.rate;
    if (Math.abs(diff) < 5) {
      concl.textContent = `Little difference: success rates within 5% of each other.`;
    } else if (diff > 0) {
      concl.textContent = `Players ≥ ${formatNum(thresh,2)} show ${diff.toFixed(1)}% higher success rate in ${yLabel}.`;
    } else {
      concl.textContent = `Players < ${formatNum(thresh,2)} show ${(-diff).toFixed(1)}% higher success rate — the metric may not predict ${yLabel} in the expected direction.`;
    }
  }

  // Bar chart
  const barTraces = [{
    type: 'bar',
    x: [t('pro_above'), t('pro_below')],
    y: [sa.rate, sb.rate],
    marker: { color: [THEME.accent, THEME.muted] },
    text: [sa.rate.toFixed(1) + '%', sb.rate.toFixed(1) + '%'],
    textposition: 'outside',
    textfont: { color: THEME.text },
    hovertemplate: '%{x}<br>Success: %{y:.1f}%<extra></extra>',
  }];
  const barLayout = makePlotLayout({
    yaxis: { title: 'Success Rate (%)', range: [0, 105], gridcolor: THEME.grid, linecolor: THEME.border, tickfont: { color: THEME.muted }, title_font: { color: THEME.label } },
    xaxis: { gridcolor: THEME.grid, linecolor: THEME.border, tickfont: { color: THEME.muted } },
    margin: { t: 20, b: 40, l: 60, r: 20 },
    showlegend: false,
  });
  Plotly.react('thresh-bar-plot', barTraces, barLayout, { responsive: true, displayModeBar: false });
}

function renderProDataTable(filtered, xLabel, yLabel, xs, ys) {
  const expander = el('pro-table-expander');
  if (!expander || !expander.open) return;

  const thead = el('pro-thead');
  const tbody = el('pro-tbody');
  thead.innerHTML = '';
  tbody.innerHTML = '';

  const isCareer = STATE.proAggMode === 'career';
  const htr = document.createElement('tr');
  htr.innerHTML = '<th>Player</th><th>Year</th><th>Pos</th>' +
    `<th>${xLabel}</th><th>${yLabel}</th>` +
    (isCareer ? '<th>PR Snaps</th><th>Seasons</th>' : '<th>Season</th><th>Snaps</th>');
  thead.appendChild(htr);

  for (let i = 0; i < filtered.length; i++) {
    const row = filtered[i];
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row._display}</td><td>${row.year}</td><td>${row.position || row.pos_group}</td>` +
      `<td>${formatNum(xs[i], 2)}</td><td>${formatNum(ys[i], 2)}</td>` +
      (isCareer
        ? `<td>${row.total_pr_snaps}</td><td>${row.pro_seasons}</td>`
        : `<td>${row.season}</td><td>${row.pass_rush_snaps}</td>`);
    tbody.appendChild(tr);
  }
}

function renderProHeatmap() {
  const filtered  = getHmFilteredData();
  const ppmMap    = STATE.proAggMode === 'career' ? PPM : PPM_SEASON;
  const zLabel    = STATE.hmZLabel;
  const zCols     = ppmMap[zLabel];
  const zCol      = zCols ? zCols[0] : null;
  const zLower    = zCols ? zCols[1] : false;

  if (filtered.length < 5) {
    Plotly.react('pro-plot', [{
      type: 'scatter', mode: 'text',
      x: [0.5], y: [0.5], text: [t('pro_no_data').replace('{n}', filtered.length)],
      textfont: { color: THEME.muted, size: 14 },
    }], makePlotLayout(), { responsive: true, displayModeBar: false });
    ['hm-n-val','hm-cells-val','hm-meanz-val','hm-medianz-val'].forEach(id => el(id).textContent = '—');
    return;
  }

  const xs = filtered.map(r => resolveMeasurement(r, STATE.hmXLabel, STATE.hmUseProDay));
  const ys = filtered.map(r => resolveMeasurement(r, STATE.hmYLabel, STATE.hmUseProDay));
  const zs = zCol ? filtered.map(r => r[zCol]) : [];

  const result = binnedStatistic2D(xs, ys, zs, STATE.hmNBins, STATE.hmAggFunc);
  if (!result) return;

  const { zValues, xEdges, yEdges, counts } = result;

  // Flatten for heatmap: transpose to [y][x]
  const nBins = STATE.hmNBins;
  const heatZ = Array.from({ length: nBins }, (_, j) =>
    Array.from({ length: nBins }, (_, i) => zValues[i][j])
  );
  const xCenters = Array.from({ length: nBins }, (_, i) => (xEdges[i] + xEdges[i + 1]) / 2);
  const yCenters = Array.from({ length: nBins }, (_, j) => (yEdges[j] + yEdges[j + 1]) / 2);

  const allZ = heatZ.flat().filter(isFinite);
  el('hm-n-val').textContent      = filtered.length;
  el('hm-cells-val').textContent  = allZ.length;
  el('hm-meanz-val').textContent  = formatNum(nanMean(allZ), 3);
  el('hm-medianz-val').textContent= formatNum(nanMedian(allZ), 3);

  const traces = [];

  traces.push({
    type: 'heatmap',
    x: xCenters,
    y: yCenters,
    z: heatZ,
    colorscale: zLower ? 'RdYlGn_r' : 'RdYlGn',
    colorbar: {
      title: zLabel, thickness: 12, len: 0.7,
      titlefont: { color: THEME.label, size: 11 },
      tickfont: { color: THEME.muted, size: 10 },
    },
    zsmooth: false,
    hovertemplate: `${STATE.hmXLabel}: %{x:.2f}<br>${STATE.hmYLabel}: %{y:.2f}<br>${zLabel}: %{z:.3f}<extra></extra>`,
  });

  // Median crosshairs
  const xMed = nanMedian(xs), yMed = nanMedian(ys);
  traces.push({
    type: 'scatter', mode: 'lines',
    x: [xMed, xMed], y: [nanMin(ys), nanMax(ys)],
    line: { color: THEME.muted, width: 1.5, dash: 'dash' },
    showlegend: false, hoverinfo: 'skip',
  });
  traces.push({
    type: 'scatter', mode: 'lines',
    x: [nanMin(xs), nanMax(xs)], y: [yMed, yMed],
    line: { color: THEME.muted, width: 1.5, dash: 'dash' },
    showlegend: false, hoverinfo: 'skip',
  });

  // Scatter overlay
  if (STATE.hmShowScatter) {
    const snaps = filtered.map(r => r.total_pr_snaps || 0);
    traces.push({
      type: 'scatter', mode: 'markers',
      x: xs, y: ys,
      name: 'Players',
      marker: {
        color: 'rgba(255,255,255,0.5)',
        size: snaps.map(s => Math.max(4, Math.sqrt(isFinite(s) ? s : 0) * 0.4)),
        line: { width: 0.5, color: 'rgba(0,0,0,0.3)' },
      },
      hovertemplate: filtered.map((r, i) =>
        `<b>${r._display}</b><br>${STATE.hmXLabel}: ${formatNum(xs[i],2)}<br>${STATE.hmYLabel}: ${formatNum(ys[i],2)}<br>${zLabel}: ${zCol ? formatNum(r[zCol],2) : '—'}<extra></extra>`
      ),
    });
  }

  const layout = makePlotLayout({
    xaxis: {
      title: STATE.hmXLabel,
      gridcolor: THEME.grid, linecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label },
    },
    yaxis: {
      title: STATE.hmYLabel,
      gridcolor: THEME.grid, linecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 }, title_font: { color: THEME.label },
    },
  });

  Plotly.react('pro-plot', traces, layout, { responsive: true, displayModeBar: false });
}

// ─── Active Tab Renderer ───────────────────────────────────────────────────────
function renderActiveTab() {
  switch (STATE.activeTab) {
    case 'scatter':   renderScatter();   break;
    case 'histogram': renderHistogram(); break;
    case 'compare':   renderCompare();   break;
    case 'pro':       renderPro();       break;
  }
}

// ─── Multiselect Widget ───────────────────────────────────────────────────────
function buildMultiselect({ wrapId, inputId, tagsId, dropdownId, options, selected, onChange, colorFn }) {
  const input    = el(inputId);
  const tagsDiv  = el(tagsId);
  const dropdown = el(dropdownId);
  let currentSel = [...selected];

  function renderTags() {
    tagsDiv.innerHTML = '';
    for (const opt of currentSel) {
      const tag = document.createElement('span');
      tag.className = 'ms-tag';
      tag.style.backgroundColor = colorFn ? (colorFn(opt) + '33') : 'transparent';
      tag.style.borderColor      = colorFn ? colorFn(opt) : THEME.border;
      tag.innerHTML = `${opt} <span class="ms-tag-x" data-val="${opt}">×</span>`;
      tag.querySelector('.ms-tag-x').addEventListener('click', e => {
        e.stopPropagation();
        currentSel = currentSel.filter(v => v !== opt);
        onChange(currentSel);
        renderTags();
        renderDropdown();
      });
      tagsDiv.appendChild(tag);
    }
  }

  function renderDropdown() {
    dropdown.innerHTML = '';
    for (const opt of options) {
      const item = document.createElement('div');
      item.className = 'ms-item' + (currentSel.includes(opt) ? ' selected' : '');
      if (colorFn) item.style.borderLeft = `3px solid ${colorFn(opt)}`;
      item.textContent = opt;
      item.addEventListener('click', () => {
        if (currentSel.includes(opt)) {
          currentSel = currentSel.filter(v => v !== opt);
        } else {
          currentSel = [...currentSel, opt];
        }
        onChange(currentSel);
        renderTags();
        renderDropdown();
      });
      dropdown.appendChild(item);
    }
  }

  input.addEventListener('click', e => {
    e.stopPropagation();
    const isOpen = dropdown.style.display !== 'none';
    dropdown.style.display = isOpen ? 'none' : 'block';
    if (!isOpen) renderDropdown();
  });

  document.addEventListener('click', () => { dropdown.style.display = 'none'; });

  renderTags();
}

// ─── Search Dropdown ───────────────────────────────────────────────────────────
function buildSearchDropdown({ inputId, dropdownId, getOptions, onSelect }) {
  const input    = el(inputId);
  const dropdown = el(dropdownId);

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    dropdown.innerHTML = '';
    if (q.length < 1) { dropdown.style.display = 'none'; return; }
    const matches = getOptions().filter(n => n.toLowerCase().includes(q)).slice(0, 20);
    if (matches.length === 0) { dropdown.style.display = 'none'; return; }
    for (const name of matches) {
      const item = document.createElement('div');
      item.className = 'search-item';
      item.textContent = name;
      item.addEventListener('mousedown', e => {
        e.preventDefault();
        onSelect(name);
        input.value = '';
        dropdown.style.display = 'none';
      });
      dropdown.appendChild(item);
    }
    dropdown.style.display = 'block';
  });

  input.addEventListener('blur', () => {
    setTimeout(() => { dropdown.style.display = 'none'; }, 150);
  });
}

// ─── Highlighted Player Tags ───────────────────────────────────────────────────
function renderHighlightedTags() {
  const tagsDiv = el('highlighted-tags');
  tagsDiv.innerHTML = '';
  for (const name of STATE.highlightedPlayers) {
    const tag = document.createElement('span');
    tag.className = 'ms-tag';
    tag.innerHTML = `${name} <span class="ms-tag-x" data-val="${name}">×</span>`;
    tag.querySelector('.ms-tag-x').addEventListener('click', () => {
      STATE.highlightedPlayers = STATE.highlightedPlayers.filter(n => n !== name);
      renderHighlightedTags();
      renderActiveTab();
    });
    tagsDiv.appendChild(tag);
  }
}

function renderCompareTags() {
  const tagsDiv = el('cmp-tags');
  tagsDiv.innerHTML = '';
  for (const name of STATE.comparePlayers) {
    const tag = document.createElement('span');
    tag.className = 'ms-tag';
    tag.innerHTML = `${name} <span class="ms-tag-x">×</span>`;
    tag.querySelector('.ms-tag-x').addEventListener('click', () => {
      STATE.comparePlayers = STATE.comparePlayers.filter(n => n !== name);
      renderCompareTags();
      renderCompare();
    });
    tagsDiv.appendChild(tag);
  }
}

// ─── Populate Selects ──────────────────────────────────────────────────────────
function populateSelect(id, options, selected) {
  const sel = el(id);
  if (!sel) return;
  sel.innerHTML = '';
  for (const opt of options) {
    const o = document.createElement('option');
    o.value = opt;
    o.textContent = opt;
    if (opt === selected) o.selected = true;
    sel.appendChild(o);
  }
}

// ─── Download CSV ──────────────────────────────────────────────────────────────
function downloadCSV(data, filename) {
  if (!data || data.length === 0) return;
  const keys = Object.keys(data[0]).filter(k => !k.startsWith('_'));
  const header = keys.join(',');
  const rows = data.map(r =>
    keys.map(k => {
      const v = r[k];
      if (v === null || v === undefined || (typeof v === 'number' && !isFinite(v))) return '';
      if (typeof v === 'string' && v.includes(',')) return `"${v.replace(/"/g, '""')}"`;
      return v;
    }).join(',')
  );
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── UI Wiring ────────────────────────────────────────────────────────────────
function wireUI() {
  // Language
  el('lang-en').addEventListener('click', () => {
    STATE.lang = 'EN';
    el('lang-en').classList.add('active');
    el('lang-jp').classList.remove('active');
    applyTranslations();
    renderActiveTab();
  });
  el('lang-jp').addEventListener('click', () => {
    STATE.lang = 'JP';
    el('lang-jp').classList.add('active');
    el('lang-en').classList.remove('active');
    applyTranslations();
    renderActiveTab();
  });

  // Year range
  el('year-start').addEventListener('change', () => {
    STATE.yearStart = Math.min(parseInt(el('year-start').value) || 2006, STATE.yearEnd);
    el('year-caption').textContent = `${STATE.yearStart}–${STATE.yearEnd} (${STATE.yearEnd - STATE.yearStart + 1} years)`;
    renderActiveTab();
  });
  el('year-end').addEventListener('change', () => {
    STATE.yearEnd = Math.max(parseInt(el('year-end').value) || 2025, STATE.yearStart);
    el('year-caption').textContent = `${STATE.yearStart}–${STATE.yearEnd} (${STATE.yearEnd - STATE.yearStart + 1} years)`;
    renderActiveTab();
  });

  // Position multiselect
  buildMultiselect({
    wrapId: 'pos-ms-wrap', inputId: 'pos-ms-input',
    tagsId: 'pos-tags', dropdownId: 'pos-dropdown',
    options: POS_GROUP_ORDER,
    selected: STATE.selectedPos,
    colorFn: pg => POS_COLORS[pg] || THEME.muted,
    onChange: sel => {
      STATE.selectedPos = sel;
      renderActiveTab();
    },
  });

  // X/Y axis selects
  populateSelect('x-label-select', MEAS_LABELS, STATE.xLabel);
  populateSelect('y-label-select', MEAS_LABELS, STATE.yLabel);
  el('x-label-select').addEventListener('change', () => {
    STATE.xLabel = el('x-label-select').value;
    STATE.proThreshold = null;
    renderActiveTab();
  });
  el('y-label-select').addEventListener('change', () => {
    STATE.yLabel = el('y-label-select').value;
    renderActiveTab();
  });

  // Pro Day toggle
  el('use-proday-toggle').addEventListener('change', () => {
    STATE.useProDay = el('use-proday-toggle').checked;
    renderActiveTab();
  });

  // Draft filter
  document.querySelectorAll('input[name="draft-filter"]').forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.checked) {
        STATE.draftFilter = radio.value;
        renderActiveTab();
      }
    });
  });

  // Show 2026
  el('show-2026-toggle').addEventListener('change', () => {
    STATE.show2026 = el('show-2026-toggle').checked;
    renderActiveTab();
  });

  // UDFA threshold
  el('udfa-threshold').addEventListener('input', () => {
    STATE.udfaThreshold = parseInt(el('udfa-threshold').value) || 0;
    el('udfa-val').textContent = STATE.udfaThreshold;
    el('udfa-caption').textContent = STATE.udfaThreshold === 0
      ? 'Undrafted NFL highlighting is off (threshold = 0)'
      : `Players with ≥${STATE.udfaThreshold} NFL seasons shown as "Undrafted NFL"`;
    renderActiveTab();
  });

  // Color mode
  document.querySelectorAll('input[name="color-mode"]').forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.checked) { STATE.colorMode = radio.value; renderScatter(); }
    });
  });

  // Marker size
  el('marker-size').addEventListener('input', () => {
    STATE.markerSize = parseInt(el('marker-size').value) || 5;
    el('marker-size-val').textContent = STATE.markerSize;
    renderScatter();
  });

  // Opacity
  el('opacity-range').addEventListener('input', () => {
    STATE.opacity = parseFloat(el('opacity-range').value) || 0.65;
    el('opacity-val').textContent = STATE.opacity.toFixed(2);
    renderScatter();
  });

  // Show ellipse
  el('show-ellipse').addEventListener('change', () => {
    STATE.showEllipse = el('show-ellipse').checked;
    renderScatter();
  });

  // Show stats
  el('show-stats').addEventListener('change', () => {
    STATE.showStats = el('show-stats').checked;
    renderScatter();
  });

  // Player search (highlight)
  const allNames = () => [...new Set([...RAW_DATA, ...DATA_2026].map(r => r._display).filter(Boolean))].sort();
  buildSearchDropdown({
    inputId: 'player-search-input',
    dropdownId: 'player-search-dropdown',
    getOptions: allNames,
    onSelect: name => {
      if (!STATE.highlightedPlayers.includes(name)) {
        STATE.highlightedPlayers.push(name);
        renderHighlightedTags();
        renderActiveTab();
      }
    },
  });

  // Show all labels
  el('show-all-labels').addEventListener('change', () => {
    STATE.showAllLabels = el('show-all-labels').checked;
    renderScatter();
  });

  // Histogram controls
  el('hist-split').addEventListener('change', () => {
    STATE.histSplit = el('hist-split').checked;
    renderHistogram();
  });
  el('show-2026-kde').addEventListener('change', () => {
    STATE.show2026kde = el('show-2026-kde').checked;
    renderHistogram();
  });

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      STATE.activeTab = tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      el(`panel-${tab}`).classList.add('active');
      renderActiveTab();
    });
  });

  // Box plot expander
  el('boxplot-expander').addEventListener('toggle', () => {
    if (el('boxplot-expander').open) renderBoxPlot(getFilteredData().dfBase);
  });

  // Pro table expander
  el('pro-table-expander').addEventListener('toggle', () => {
    if (el('pro-table-expander').open && STATE.activeTab === 'pro') renderPro();
  });

  // Download CSV (scatter)
  el('scatter-download-csv').addEventListener('click', () => {
    const { dfBase } = getFilteredData();
    downloadCSV(dfBase, 'nfl_combine_filtered.csv');
  });

  // Download CSV (pro table)
  el('pro-table-download').addEventListener('click', () => {
    const filtered = getProFilteredData();
    downloadCSV(filtered, 'nfl_pro_filtered.csv');
  });

  // Compare: player search
  buildSearchDropdown({
    inputId: 'cmp-player-input',
    dropdownId: 'cmp-search-dropdown',
    getOptions: allNames,
    onSelect: name => {
      if (STATE.comparePlayers.length >= 4) return;
      if (!STATE.comparePlayers.includes(name)) {
        STATE.comparePlayers.push(name);
        renderCompareTags();
        renderCompare();
      }
    },
  });

  // Similar players
  buildSearchDropdown({
    inputId: 'sim-player-input',
    dropdownId: 'sim-search-dropdown',
    getOptions: allNames,
    onSelect: name => {
      STATE.simPlayer = name;
      el('sim-player-input').value = name;
      renderCompare();
    },
  });

  el('sim-n').addEventListener('input', () => {
    STATE.simN = parseInt(el('sim-n').value) || 8;
    el('sim-n-val').textContent = STATE.simN;
    renderCompare();
  });

  // ── Pro controls wiring ────────────────────────────────────────────────────

  // View mode buttons
  el('pro-view-scatter').addEventListener('click', () => {
    STATE.proViewMode = 'scatter';
    el('pro-view-scatter').classList.add('active');
    el('pro-view-heatmap').classList.remove('active');
    renderPro();
  });
  el('pro-view-heatmap').addEventListener('click', () => {
    STATE.proViewMode = 'heatmap';
    el('pro-view-heatmap').classList.add('active');
    el('pro-view-scatter').classList.remove('active');
    renderPro();
  });

  // Aggregation mode buttons
  el('pro-agg-career').addEventListener('click', () => {
    STATE.proAggMode = 'career';
    el('pro-agg-career').classList.add('active');
    el('pro-agg-season').classList.remove('active');
    // Update Y selects
    populateSelect('pro-y-select', Object.keys(PPM), STATE.proYLabel);
    populateSelect('hm-z-select', Object.keys(PPM), STATE.hmZLabel);
    renderPro();
  });
  el('pro-agg-season').addEventListener('click', () => {
    STATE.proAggMode = 'season';
    el('pro-agg-season').classList.add('active');
    el('pro-agg-career').classList.remove('active');
    // Update Y selects for season
    const firstSeasonKey = Object.keys(PPM_SEASON)[0];
    if (!PPM_SEASON[STATE.proYLabel]) STATE.proYLabel = firstSeasonKey;
    if (!PPM_SEASON[STATE.hmZLabel])  STATE.hmZLabel  = firstSeasonKey;
    populateSelect('pro-y-select', Object.keys(PPM_SEASON), STATE.proYLabel);
    populateSelect('hm-z-select', Object.keys(PPM_SEASON), STATE.hmZLabel);
    renderPro();
  });

  // Pro scatter X/Y selects
  populateSelect('pro-x-select', Object.keys(ECM), STATE.proXLabel);
  populateSelect('pro-y-select', Object.keys(PPM), STATE.proYLabel);
  el('pro-x-select').addEventListener('change', () => {
    STATE.proXLabel = el('pro-x-select').value;
    STATE.proThreshold = null;
    renderPro();
  });
  el('pro-y-select').addEventListener('change', () => {
    STATE.proYLabel = el('pro-y-select').value;
    renderPro();
  });

  // Pro use proday
  el('pro-use-pd').addEventListener('change', () => {
    STATE.proUseProDay = el('pro-use-pd').checked;
    renderPro();
  });

  // Pro min snaps
  el('pro-min-snaps').addEventListener('input', () => {
    STATE.proMinSnaps = parseInt(el('pro-min-snaps').value) || 0;
    el('pro-snaps-val').textContent = STATE.proMinSnaps;
    renderPro();
  });

  // Pro position multiselect
  buildMultiselect({
    wrapId: 'pro-pos-ms-wrap', inputId: 'pro-pos-input',
    tagsId: 'pro-pos-tags', dropdownId: 'pro-pos-dropdown',
    options: ['DE', 'OLB', 'EDGE', 'EDG'],
    selected: STATE.proPosFilter,
    colorFn: null,
    onChange: sel => { STATE.proPosFilter = sel; renderPro(); },
  });

  // Pro year range
  el('pro-year-start').addEventListener('change', () => {
    STATE.proYearStart = parseInt(el('pro-year-start').value) || 2008;
    renderPro();
  });
  el('pro-year-end').addEventListener('change', () => {
    STATE.proYearEnd = parseInt(el('pro-year-end').value) || 2022;
    renderPro();
  });

  // Pro color by
  document.querySelectorAll('input[name="pro-color-by"]').forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.checked) { STATE.proColorBy = radio.value; renderPro(); }
    });
  });

  // Threshold slider
  el('thresh-slider').addEventListener('input', () => {
    STATE.proThreshold = parseFloat(el('thresh-slider').value);
    el('thresh-val').textContent = formatNum(STATE.proThreshold, 2);
    const filtered = getProFilteredData();
    const xLabel = STATE.proXLabel;
    const yLabel = STATE.proYLabel;
    const ppmMap = STATE.proAggMode === 'career' ? PPM : PPM_SEASON;
    const yCols  = ppmMap[yLabel];
    const yCol   = yCols ? yCols[0] : null;
    const yLower = yCols ? yCols[1] : false;
    const xs = filtered.map(r => resolveMeasurement(r, xLabel, STATE.proUseProDay));
    const ys = yCol ? filtered.map(r => r[yCol]) : [];
    renderThresholdAnalysis(filtered, xs, ys, xLabel, yLabel, yLower);
  });

  // Heatmap controls
  populateSelect('hm-x-select', Object.keys(ECM), STATE.hmXLabel);
  populateSelect('hm-y-select', Object.keys(ECM), STATE.hmYLabel);
  populateSelect('hm-z-select', Object.keys(PPM), STATE.hmZLabel);
  el('hm-x-select').addEventListener('change', () => { STATE.hmXLabel = el('hm-x-select').value; renderPro(); });
  el('hm-y-select').addEventListener('change', () => { STATE.hmYLabel = el('hm-y-select').value; renderPro(); });
  el('hm-z-select').addEventListener('change', () => { STATE.hmZLabel = el('hm-z-select').value; renderPro(); });
  el('hm-use-pd').addEventListener('change', () => { STATE.hmUseProDay = el('hm-use-pd').checked; renderPro(); });
  el('hm-min-snaps').addEventListener('input', () => {
    STATE.hmMinSnaps = parseInt(el('hm-min-snaps').value) || 0;
    el('hm-snaps-val').textContent = STATE.hmMinSnaps;
    renderPro();
  });
  buildMultiselect({
    wrapId: 'hm-pos-ms-wrap', inputId: 'hm-pos-input',
    tagsId: 'hm-pos-tags', dropdownId: 'hm-pos-dropdown',
    options: ['DE', 'OLB', 'EDGE', 'EDG'],
    selected: STATE.hmPosFilter,
    colorFn: null,
    onChange: sel => { STATE.hmPosFilter = sel; renderPro(); },
  });
  el('hm-year-start').addEventListener('change', () => { STATE.hmYearStart = parseInt(el('hm-year-start').value) || 2008; renderPro(); });
  el('hm-year-end').addEventListener('change', () => { STATE.hmYearEnd = parseInt(el('hm-year-end').value) || 2022; renderPro(); });
  el('hm-bins').addEventListener('input', () => {
    STATE.hmNBins = parseInt(el('hm-bins').value) || 12;
    el('hm-bins-val').textContent = STATE.hmNBins;
    renderPro();
  });
  document.querySelectorAll('input[name="hm-agg"]').forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.checked) { STATE.hmAggFunc = radio.value; renderPro(); }
    });
  });
  el('hm-show-scatter').addEventListener('change', () => {
    STATE.hmShowScatter = el('hm-show-scatter').checked;
    renderPro();
  });

  // Mobile sidebar
  const sidebarToggleBtn = el('sidebar-toggle-btn');
  const sidebar          = el('sidebar');
  const sidebarOverlay   = el('sidebar-overlay');
  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      sidebarOverlay.classList.toggle('active');
    });
    sidebarOverlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('active');
    });
  }

  // Window resize
  window.addEventListener('resize', () => {
    for (const id of ['scatter-plot', 'histogram-plot', 'radar-plot', 'pro-plot', 'boxplot-plot', 'thresh-bar-plot']) {
      const node = el(id);
      if (node && node._fullLayout) Plotly.Plots.resize(node);
    }
  });
}

// ─── Data Loading ─────────────────────────────────────────────────────────────
async function loadCSV(url) {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      skipEmptyLines: true,
      complete: results => resolve(results.data),
      error: err => reject(err),
    });
  });
}

async function loadData() {
  const overlay   = el('loading-overlay');
  const loadText  = overlay.querySelector('.loading-text');

  try {
    // Try primary combine CSV, fallback to alternate
    loadText.textContent = 'Loading combine data…';
    let combineData;
    try {
      combineData = await loadCSV('combine_with_career.csv');
    } catch {
      loadText.textContent = 'Trying fallback CSV…';
      combineData = await loadCSV('combine_with_draft.csv');
    }

    // Preprocess
    buildPosToGroup();
    for (const row of combineData) {
      preprocessRow(row);
      applyDraftedLabel(row, STATE.udfaThreshold);
    }

    // Split 2026 pre-draft vs historical
    for (const row of combineData) {
      if (row.year === 2026) {
        DATA_2026.push(row);
      } else {
        RAW_DATA.push(row);
      }
    }

    // Compute percentiles for compare tab
    loadText.textContent = 'Computing percentiles…';
    computeAllPosPercentiles();

    // Load pass rush data
    loadText.textContent = 'Loading Pro Stats…';
    try {
      const prData = await loadCSV('Pro_Stats/nflpro_passrush_all.csv');
      for (const row of prData) {
        PASSRUSH_RAW.push(preprocessPassrushRow(row));
      }
      loadText.textContent = 'Building merged dataset…';
      buildMergedEdgeData();
      buildMergedEdgeSeasonData();
    } catch (e) {
      console.warn('Pass Rush data not found:', e);
    }

    // Hide loading overlay
    overlay.style.opacity = '0';
    setTimeout(() => { overlay.style.display = 'none'; }, 300);

    // Initial render
    renderActiveTab();

  } catch (err) {
    loadText.textContent = `Error loading data: ${err.message || err}`;
    loadText.style.color = '#FF7B72';
    console.error('Data load error:', err);
  }
}

// ─── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  buildPosToGroup();
  wireUI();
  applyTranslations();
  loadData();
});
