/**
 * app.js — NFL Combine & Pro Day Explorer
 * Main application logic: data loading, preprocessing, rendering, and UI wiring.
 */

'use strict';

// ─── Global Data ───────────────────────────────────────────────────────────────
let RAW_DATA      = [];   // All rows from combine CSV (year < 2026)
let DATA_2026     = [];   // Rows with year === 2026
let POS_TO_GROUP  = {};   // position -> pos_group
let POS_PERCENTILES = {}; // { pos_group: { label: [sorted drafted values] } }

// ─── Application State ─────────────────────────────────────────────────────────
const STATE = {
  lang:              'EN',
  yearStart:         2006,
  yearEnd:           2026,
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
};

// ─── DOM Helper ────────────────────────────────────────────────────────────────
const el = id => document.getElementById(id);

// ─── Color Helpers ─────────────────────────────────────────────────────────────
function hexToRgba(hex, alpha) {
  const h = hex.replace('#', '');
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

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
    height: 660,
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
    height: 520,
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
        fillcolor: hexToRgba(radarColors[i % radarColors.length], 0.15),
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


// ─── Active Tab Renderer ───────────────────────────────────────────────────────
function renderActiveTab() {
  switch (STATE.activeTab) {
    case 'scatter':   renderScatter();   break;
    case 'histogram': renderHistogram(); break;
    case 'compare':   renderCompare();   break;
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
    STATE.yearEnd = Math.max(parseInt(el('year-end').value) || 2026, STATE.yearStart);
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

  // Download CSV (scatter)
  el('scatter-download-csv').addEventListener('click', () => {
    const { dfBase } = getFilteredData();
    downloadCSV(dfBase, 'nfl_combine_filtered.csv');
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
    for (const id of ['scatter-plot', 'histogram-plot', 'radar-plot', 'boxplot-plot']) {
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
