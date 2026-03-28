/**
 * stats.js — Statistical utility functions for NFL Combine Explorer
 * Pure JavaScript implementations of scipy/numpy equivalents.
 */

'use strict';

// ─── Array helpers ─────────────────────────────────────────────────────────────

/** Filter NaN values from array */
function validValues(arr) {
  return arr.filter(v => v !== null && v !== undefined && !Number.isNaN(v) && isFinite(v));
}

/** Compute mean, ignoring NaN/null */
function nanMean(arr) {
  const v = validValues(arr);
  if (v.length === 0) return NaN;
  return v.reduce((a, b) => a + b, 0) / v.length;
}

/** Compute standard deviation (sample), ignoring NaN/null */
function nanStd(arr) {
  const v = validValues(arr);
  if (v.length < 2) return NaN;
  const m = nanMean(v);
  const sq = v.reduce((acc, x) => acc + (x - m) ** 2, 0);
  return Math.sqrt(sq / (v.length - 1));
}

/** Compute median, ignoring NaN/null */
function nanMedian(arr) {
  const v = validValues(arr).slice().sort((a, b) => a - b);
  if (v.length === 0) return NaN;
  const mid = Math.floor(v.length / 2);
  return v.length % 2 === 0 ? (v[mid - 1] + v[mid]) / 2 : v[mid];
}

/** Min of valid values */
function nanMin(arr) {
  const v = validValues(arr);
  if (v.length === 0) return NaN;
  return Math.min(...v);
}

/** Max of valid values */
function nanMax(arr) {
  const v = validValues(arr);
  if (v.length === 0) return NaN;
  return Math.max(...v);
}

// ─── Normal CDF ────────────────────────────────────────────────────────────────

/**
 * Normal CDF approximation using Abramowitz & Stegun rational approximation.
 * Maximum error: 7.5e-8
 */
function normalCDF(z) {
  const sign = z < 0 ? -1 : 1;
  const x = Math.abs(z) / Math.SQRT2;
  // erfc approximation
  const t = 1 / (1 + 0.3275911 * x);
  const poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  const erfc = poly * Math.exp(-x * x);
  return 0.5 * (1 + sign * (1 - erfc));
}

// ─── t-distribution CDF ────────────────────────────────────────────────────────

/**
 * Regularized incomplete beta function using continued fraction (Lentz's method).
 * Used for t-distribution CDF.
 */
function incompleteBeta(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  // For stability, use the reflection formula when x > (a+1)/(a+b+2)
  if (x > (a + 1) / (a + b + 2)) {
    return 1 - incompleteBeta(1 - x, b, a);
  }
  const lbeta = logGamma(a + b) - logGamma(a) - logGamma(b);
  const front = Math.exp(Math.log(x) * a + Math.log(1 - x) * b - lbeta) / a;
  // Lentz continued fraction
  const MAXITER = 200;
  const EPS = 3e-7;
  let h = 1, c = 1, d = 1 - (a + b) * x / (a + 1);
  if (Math.abs(d) < 1e-30) d = 1e-30;
  d = 1 / d;
  h = d;
  for (let m = 1; m <= MAXITER; m++) {
    // Even step
    let num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m));
    d = 1 + num * d;
    if (Math.abs(d) < 1e-30) d = 1e-30;
    c = 1 + num / c;
    if (Math.abs(c) < 1e-30) c = 1e-30;
    d = 1 / d;
    h *= d * c;
    // Odd step
    num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1));
    d = 1 + num * d;
    if (Math.abs(d) < 1e-30) d = 1e-30;
    c = 1 + num / c;
    if (Math.abs(c) < 1e-30) c = 1e-30;
    d = 1 / d;
    const delta = d * c;
    h *= delta;
    if (Math.abs(delta - 1) < EPS) break;
  }
  return front * h;
}

/** Log Gamma function (Lanczos approximation) */
function logGamma(z) {
  const g = 7;
  const c = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
  ];
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - logGamma(1 - z);
  z -= 1;
  let x = c[0];
  for (let i = 1; i < g + 2; i++) x += c[i] / (z + i);
  const t = z + g + 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

/**
 * Two-tailed p-value for Student's t-distribution with df degrees of freedom.
 */
function tCDF(t, df) {
  // p-value (two-tailed)
  const x = df / (df + t * t);
  const p = incompleteBeta(x, df / 2, 0.5);
  return Math.min(p, 1);
}

// ─── Percentile of score ────────────────────────────────────────────────────────

/**
 * Equivalent to scipy.stats.percentileofscore(arr, value, kind='mean').
 * Returns the percentile (0-100) of value in arr.
 */
function percentileOfScore(arr, value) {
  const v = validValues(arr).slice().sort((a, b) => a - b);
  if (v.length === 0) return NaN;
  let below = 0, equal = 0;
  for (const x of v) {
    if (x < value) below++;
    else if (x === value) equal++;
  }
  // kind='mean': average of left and right percentiles
  const left  = (below / v.length) * 100;
  const right = ((below + equal) / v.length) * 100;
  return (left + right) / 2;
}

// ─── Mann-Whitney U test ────────────────────────────────────────────────────────

/**
 * Mann-Whitney U test (two-sided, normal approximation with continuity correction).
 * Returns p-value, or null if either sample has fewer than 5 elements.
 * Equivalent to scipy.stats.mannwhitneyu(a, b, alternative='two-sided').
 */
function mannWhitneyU(a, b) {
  const va = validValues(a);
  const vb = validValues(b);
  if (va.length < 5 || vb.length < 5) return null;

  const n1 = va.length, n2 = vb.length;
  const n  = n1 + n2;

  // Rank all values together
  const combined = [...va.map(v => ({ v, grp: 0 })), ...vb.map(v => ({ v, grp: 1 }))];
  combined.sort((a, b) => a.v - b.v);

  // Assign ranks (average for ties)
  const ranks = new Array(n);
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n - 1 && combined[j + 1].v === combined[i].v) j++;
    const avgRank = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) ranks[k] = avgRank;
    i = j + 1;
  }

  // Compute U statistic for group 0
  let R1 = 0;
  for (let k = 0; k < n; k++) if (combined[k].grp === 0) R1 += ranks[k];

  const U1 = R1 - n1 * (n1 + 1) / 2;
  const U2 = n1 * n2 - U1;
  const U  = Math.min(U1, U2);

  // Tie correction
  const tieGroups = {};
  for (const r of ranks) tieGroups[r] = (tieGroups[r] || 0) + 1;
  let tieCorrection = 0;
  for (const cnt of Object.values(tieGroups)) {
    if (cnt > 1) tieCorrection += (cnt ** 3 - cnt);
  }
  const varU = (n1 * n2 / 12) * (n + 1 - tieCorrection / (n * (n - 1)));
  if (varU <= 0) return 1;

  // Normal approximation with continuity correction
  const z = (U - n1 * n2 / 2 + 0.5) / Math.sqrt(varU);
  return 2 * normalCDF(-Math.abs(z));
}

// ─── Pearson correlation ────────────────────────────────────────────────────────

/**
 * Pearson r correlation coefficient with two-tailed p-value.
 * Returns { r, pvalue } or null if fewer than 3 valid pairs.
 */
function pearsonR(x, y) {
  // Filter to pairs where both are valid
  const pairs = [];
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const xi = parseFloat(x[i]), yi = parseFloat(y[i]);
    if (isFinite(xi) && isFinite(yi)) pairs.push([xi, yi]);
  }
  const n = pairs.length;
  if (n < 3) return { r: NaN, pvalue: NaN };

  const mx = pairs.reduce((s, p) => s + p[0], 0) / n;
  const my = pairs.reduce((s, p) => s + p[1], 0) / n;

  let sxy = 0, sxx = 0, syy = 0;
  for (const [xi, yi] of pairs) {
    const dx = xi - mx, dy = yi - my;
    sxy += dx * dy;
    sxx += dx * dx;
    syy += dy * dy;
  }

  if (sxx === 0 || syy === 0) return { r: 0, pvalue: 1 };

  const r = sxy / Math.sqrt(sxx * syy);
  // Two-tailed t-test
  const df = n - 2;
  const t  = r * Math.sqrt(df / (1 - r * r + 1e-15));
  const pvalue = tCDF(Math.abs(t), df);

  return { r: Math.max(-1, Math.min(1, r)), pvalue };
}

// ─── OLS Linear Regression ─────────────────────────────────────────────────────

/**
 * Ordinary Least Squares linear regression.
 * Returns { slope, intercept, r, pvalue, stderr } or null if < 3 pairs.
 * Equivalent to scipy.stats.linregress(x, y).
 */
function linregress(x, y) {
  const pairs = [];
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const xi = parseFloat(x[i]), yi = parseFloat(y[i]);
    if (isFinite(xi) && isFinite(yi)) pairs.push([xi, yi]);
  }
  const n = pairs.length;
  if (n < 3) return null;

  const mx = pairs.reduce((s, p) => s + p[0], 0) / n;
  const my = pairs.reduce((s, p) => s + p[1], 0) / n;

  let sxx = 0, sxy = 0, syy = 0;
  for (const [xi, yi] of pairs) {
    sxx += (xi - mx) ** 2;
    sxy += (xi - mx) * (yi - my);
    syy += (yi - my) ** 2;
  }

  if (sxx === 0) return null;

  const slope     = sxy / sxx;
  const intercept = my - slope * mx;
  const r         = sxy / Math.sqrt(sxx * syy + 1e-20);
  const r2        = r * r;

  // Residual standard error
  let sse = 0;
  for (const [xi, yi] of pairs) sse += (yi - (slope * xi + intercept)) ** 2;
  const mse    = sse / (n - 2);
  const stderr = Math.sqrt(mse / sxx);

  // p-value for slope
  const df   = n - 2;
  const tStat = slope / (stderr + 1e-20);
  const pvalue = tCDF(Math.abs(tStat), df);

  return {
    slope, intercept,
    r: Math.max(-1, Math.min(1, r)),
    r2, pvalue, stderr,
  };
}

// ─── Gaussian KDE ──────────────────────────────────────────────────────────────

/**
 * Gaussian Kernel Density Estimation.
 * bwMethod: bandwidth multiplier (default 0.5, matching Python app).
 * Equivalent to scipy.stats.gaussian_kde(values, bw_method=bwMethod).
 * Returns an array of density values at evalPoints.
 */
function gaussianKDE(values, evalPoints, bwMethod = 0.5) {
  const v = validValues(values);
  if (v.length < 2) return evalPoints.map(() => 0);

  // Scott's rule then scaled by bwMethod
  const n   = v.length;
  const std = nanStd(v);
  if (std === 0 || isNaN(std)) return evalPoints.map(() => 0);

  // Silverman's rule: h = 1.06 * std * n^(-1/5)
  const h = bwMethod * 1.06 * std * Math.pow(n, -0.2);
  const h2 = h * h * 2;

  return evalPoints.map(x => {
    let sum = 0;
    for (const xi of v) {
      const d = x - xi;
      sum += Math.exp(-(d * d) / h2);
    }
    return sum / (n * h * Math.sqrt(2 * Math.PI));
  });
}

// ─── Confidence Ellipse ────────────────────────────────────────────────────────

/**
 * Compute 95% confidence ellipse for 2D data.
 * Analytically computes eigenvalues/eigenvectors of 2×2 covariance matrix.
 * Returns { x: [], y: [] } with nPoints tracing the ellipse boundary.
 * scale = sqrt(5.991) gives 95% coverage (chi-squared, 2 dof).
 */
function confidenceEllipse(xs, ys, scale = Math.sqrt(5.991), nPoints = 100) {
  const pairs = [];
  for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
    const xi = parseFloat(xs[i]), yi = parseFloat(ys[i]);
    if (isFinite(xi) && isFinite(yi)) pairs.push([xi, yi]);
  }
  if (pairs.length < 3) return { x: [], y: [] };

  const n  = pairs.length;
  const mx = pairs.reduce((s, p) => s + p[0], 0) / n;
  const my = pairs.reduce((s, p) => s + p[1], 0) / n;

  let sxx = 0, sxy = 0, syy = 0;
  for (const [xi, yi] of pairs) {
    sxx += (xi - mx) ** 2;
    sxy += (xi - mx) * (yi - my);
    syy += (yi - my) ** 2;
  }
  sxx /= (n - 1);
  sxy /= (n - 1);
  syy /= (n - 1);

  // Analytical eigenvalues for 2×2 symmetric matrix [[sxx, sxy], [sxy, syy]]
  const trace  = sxx + syy;
  const det    = sxx * syy - sxy * sxy;
  const disc   = Math.sqrt(Math.max(0, (trace / 2) ** 2 - det));
  const lam1   = trace / 2 + disc;  // larger eigenvalue
  const lam2   = trace / 2 - disc;  // smaller eigenvalue

  // Eigenvector for lam1
  let ex, ey;
  if (Math.abs(sxy) > 1e-10) {
    ex = lam1 - syy;
    ey = sxy;
  } else if (sxx >= syy) {
    ex = 1; ey = 0;
  } else {
    ex = 0; ey = 1;
  }
  const eLen = Math.sqrt(ex * ex + ey * ey);
  ex /= eLen; ey /= eLen;

  // Semi-axes
  const a = scale * Math.sqrt(Math.max(0, lam1));
  const b = scale * Math.sqrt(Math.max(0, lam2));

  // Parametric ellipse
  const ellX = [], ellY = [];
  for (let i = 0; i <= nPoints; i++) {
    const theta = (i / nPoints) * 2 * Math.PI;
    const ct = Math.cos(theta), st = Math.sin(theta);
    // Rotate by eigenvector angle
    const px = a * ct * ex - b * st * ey;
    const py = a * ct * ey + b * st * ex;
    ellX.push(mx + px);
    ellY.push(my + py);
  }

  return { x: ellX, y: ellY };
}

// ─── 2D Binned Statistic ────────────────────────────────────────────────────────

/**
 * Compute a 2D binned statistic (mean or median).
 * Returns { zValues: Float64Array (nBins × nBins), xEdges, yEdges, counts }.
 * zValues[i][j] corresponds to x in [xEdges[i], xEdges[i+1]) and y in [yEdges[j], yEdges[j+1]).
 */
function binnedStatistic2D(xs, ys, zs, nBins, statFunc = 'mean') {
  const xMin = nanMin(xs), xMax = nanMax(xs);
  const yMin = nanMin(ys), yMax = nanMax(ys);
  if (!isFinite(xMin) || !isFinite(yMin)) return null;

  const xRange = xMax - xMin || 1;
  const yRange = yMax - yMin || 1;

  // Build edges with small epsilon on max end to include boundary
  const xEdges = Array.from({ length: nBins + 1 }, (_, i) => xMin + (i / nBins) * xRange);
  const yEdges = Array.from({ length: nBins + 1 }, (_, i) => yMin + (i / nBins) * yRange);
  xEdges[nBins] += 1e-10;
  yEdges[nBins] += 1e-10;

  // Initialize bins
  const bins = Array.from({ length: nBins }, () =>
    Array.from({ length: nBins }, () => [])
  );

  for (let k = 0; k < xs.length; k++) {
    const xv = parseFloat(xs[k]), yv = parseFloat(ys[k]), zv = parseFloat(zs[k]);
    if (!isFinite(xv) || !isFinite(yv) || !isFinite(zv)) continue;
    // Binary search for bin index
    let xi = Math.floor((xv - xMin) / xRange * nBins);
    let yi = Math.floor((yv - yMin) / yRange * nBins);
    xi = Math.max(0, Math.min(nBins - 1, xi));
    yi = Math.max(0, Math.min(nBins - 1, yi));
    bins[xi][yi].push(zv);
  }

  // Compute statistic per bin
  const zValues = Array.from({ length: nBins }, (_, i) =>
    Array.from({ length: nBins }, (_, j) => {
      const cell = bins[i][j];
      if (cell.length === 0) return NaN;
      if (statFunc === 'median') return nanMedian(cell);
      return nanMean(cell);
    })
  );
  const counts = Array.from({ length: nBins }, (_, i) =>
    Array.from({ length: nBins }, (_, j) => bins[i][j].length)
  );

  return { zValues, xEdges, yEdges, counts };
}
