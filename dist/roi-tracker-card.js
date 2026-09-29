/**
 * ROI Tracker Card  v0.4.1
 *
 *   type: custom:roi-tracker-card
 *   device: <device_id>            # ROI-Tracker-Anlage
 *   variant: standard              # mini | compact | standard | full
 *   title: "PV-Anlage"             # optional
 *
 * Ein Klick auf die Karte öffnet ein Popup mit allen Details:
 * Übersicht, Monats-/Jahresstatistik (inkl. Tageswerte) und Prognose.
 * Daten kommen über die WebSocket-API `roi_tracker/data`.
 */

const VERSION = "0.4.1";
const REFRESH_MS = 5 * 60 * 1000;
const VARIANTS = ["mini", "compact", "standard", "full"];

// Validierte Serienfarben (CVD-sicher, hell/dunkel getrennt gestuft)
const PALETTE = {
  light: { savings: "#2a78d6", revenue: "#eb6834" },
  dark: { savings: "#3987e5", revenue: "#d95926" },
};

const TXT = {
  de: {
    total_return: "Gesamtertrag", savings: "Ersparnis", revenue: "Einspeisung",
    revenue_long: "Einspeiseertrag", investment: "Investition", remaining: "Offen",
    amortization: "Amortisiert", roi: "ROI", this_month: "Dieser Monat",
    month_forecast: "Prognose Monat", yearly: "Prognose / Jahr", breakeven: "Break-Even",
    today: "Heute", daily: "Ø pro Tag", paid_off: "abbezahlt", provisional: "vorläufig",
    self_kwh: "Eigenverbrauch", export_kwh: "Einspeisung", avg_price: "Ø Strompreis",
    feed_in: "Einspeisevergütung", price_source: "Preisquelle",
    price_sensor: "dynamisch (Sensor)", price_fixed: "Festpreis",
    data_since: "Daten seit", tab_overview: "Übersicht", tab_months: "Monate",
    tab_forecast: "Prognose", month: "Monat", day: "Tag", sum: "Summe", year: "Jahr",
    years_title: "Jahre", months_of: "Monate", days_of: "Tage im", back: "← zurück zu",
    no_device: "Bitte im Karten-Editor eine Anlage auswählen.",
    loading: "Lade Daten…", error: "Daten konnten nicht geladen werden",
    no_data: "Noch keine Daten – die Werte erscheinen, sobald Home Assistant die erste Stunde kompiliert hat.",
    close: "Schließen", details: "Details anzeigen",
    fc_intro: (rate, date, yrs) =>
      `Beim aktuellen Tempo von <b>${rate}</b> pro Jahr ist die Anlage voraussichtlich <b>${date}</b> abbezahlt${yrs ? ` – in etwa <b>${yrs}</b>` : ""}.`,
    fc_done: (date) => `Die Anlage hat sich am <b>${date}</b> bezahlt gemacht. Alles darüber ist Gewinn.`,
    fc_none: "Für eine Prognose sind noch zu wenig Daten vorhanden.",
    fc_prov: (days) =>
      `Vorläufige Hochrechnung aus ${days} Tagen – Sommer und Winter gleichen sich erst nach 12 Monaten aus.`,
    fc_seasonal: "Hochrechnung aus den tatsächlichen Erträgen der letzten 12 Monate.",
    years_unit: (n) => `${n} ${n === 1 ? "Jahr" : "Jahren"}`,
    months_unit: (n) => `${n} ${n === 1 ? "Monat" : "Monaten"}`,
    time_left: (yrs, f) => yrs < 1
      ? `noch ${Math.max(1, Math.round(yrs * 12))} Monate`
      : `noch ${f.num(yrs, 1)} Jahre`,
    actual: "Erreicht", projected: "Prognose",
    missing_prices: (n) => `Für ${n} Stunden lagen keine Preisdaten vor – dort wurde der letzte bekannte Preis bzw. der Festpreis verwendet.`,
    editor_device: "Anlage", editor_variant: "Darstellung", editor_title: "Titel (optional)",
    editor_none: "— Anlage wählen —", editor_no_dev: "Keine ROI-Tracker-Anlage gefunden – zuerst die Integration einrichten.",
    v_mini: "Mini – eine Zeile", v_compact: "Kompakt – Ertrag & Amortisation",
    v_standard: "Standard – mit Kennzahlen", v_full: "Voll – mit Monatsdiagramm",
    last_12: "Letzte 12 Monate", click_hint: "Tippen für Details",
  },
  en: {
    total_return: "Total return", savings: "Savings", revenue: "Feed-in",
    revenue_long: "Feed-in revenue", investment: "Investment", remaining: "Remaining",
    amortization: "Paid off", roi: "ROI", this_month: "This month",
    month_forecast: "Month forecast", yearly: "Forecast / year", breakeven: "Break-even",
    today: "Today", daily: "Avg. per day", paid_off: "paid off", provisional: "provisional",
    self_kwh: "Self-consumption", export_kwh: "Export", avg_price: "Avg. price",
    feed_in: "Feed-in tariff", price_source: "Price source",
    price_sensor: "dynamic (sensor)", price_fixed: "fixed price",
    data_since: "Data since", tab_overview: "Overview", tab_months: "Months",
    tab_forecast: "Forecast", month: "Month", day: "Day", sum: "Total", year: "Year",
    years_title: "Years", months_of: "Months", days_of: "Days in", back: "← back to",
    no_device: "Please select a system in the card editor.",
    loading: "Loading…", error: "Could not load data",
    no_data: "No data yet – values appear once Home Assistant has compiled the first hour.",
    close: "Close", details: "Show details",
    fc_intro: (rate, date, yrs) =>
      `At the current pace of <b>${rate}</b> per year the system is expected to be paid off <b>${date}</b>${yrs ? ` – in about <b>${yrs}</b>` : ""}.`,
    fc_done: (date) => `The system paid for itself on <b>${date}</b>. Everything beyond is profit.`,
    fc_none: "Not enough data for a forecast yet.",
    fc_prov: (days) =>
      `Provisional projection from ${days} days – summer and winter only balance out after 12 months.`,
    fc_seasonal: "Projection based on the actual returns of the last 12 months.",
    years_unit: (n) => `${n} ${n === 1 ? "year" : "years"}`,
    months_unit: (n) => `${n} ${n === 1 ? "month" : "months"}`,
    time_left: (yrs, f) => yrs < 1
      ? `${Math.max(1, Math.round(yrs * 12))} months left`
      : `${f.num(yrs, 1)} years left`,
    actual: "Actual", projected: "Forecast",
    missing_prices: (n) => `No price data for ${n} hours – the last known price or the fixed price was used there.`,
    editor_device: "System", editor_variant: "Layout", editor_title: "Title (optional)",
    editor_none: "— select system —", editor_no_dev: "No ROI Tracker system found – set up the integration first.",
    v_mini: "Mini – single line", v_compact: "Compact – return & amortization",
    v_standard: "Standard – with key figures", v_full: "Full – with monthly chart",
    last_12: "Last 12 months", click_hint: "Tap for details",
  },
};

// ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function langOf(hass, cfg) {
  const l = (cfg && cfg.language) || (hass && hass.language) || "de";
  return l.startsWith("de") ? "de" : "en";
}

/** Formatierer für eine Sprache/Währung. */
function makeFmt(lang, currency) {
  const locale = lang === "de" ? "de-DE" : "en-US";
  const cur = currency || "EUR";
  const moneyCache = {};
  const money = (v, dec = 2) => {
    if (v == null || !Number.isFinite(v)) return "–";
    if (!moneyCache[dec]) {
      try {
        moneyCache[dec] = new Intl.NumberFormat(locale, {
          style: "currency", currency: cur, minimumFractionDigits: dec, maximumFractionDigits: dec,
        });
      } catch (e) {
        moneyCache[dec] = new Intl.NumberFormat(locale, { minimumFractionDigits: dec, maximumFractionDigits: dec });
      }
    }
    return moneyCache[dec].format(v);
  };
  const num = (v, dec = 1) =>
    v == null || !Number.isFinite(v) ? "–"
      : new Intl.NumberFormat(locale, { minimumFractionDigits: dec, maximumFractionDigits: dec }).format(v);
  const date = (iso, opts = { day: "2-digit", month: "2-digit", year: "numeric" }) => {
    if (!iso) return "–";
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, (m || 1) - 1, d || 1).toLocaleDateString(locale, opts);
  };
  const month = (key, style = "short") => {
    const [y, m] = key.split("-").map(Number);
    return new Date(y, m - 1, 1).toLocaleDateString(locale, { month: style });
  };
  const monthYear = (key) => {
    const [y, m] = key.split("-").map(Number);
    return new Date(y, m - 1, 1).toLocaleDateString(locale, { month: "long", year: "numeric" });
  };
  const compact = (v) =>
    new Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 1 }).format(v);
  return { money, num, date, month, monthYear, compact, currency: cur, locale };
}

/** Runde Achsenskala: höchstens 5 Teilstriche mit glatten Schritten (1, 2, 2,5, 5 × 10^n). */
function niceScale(v) {
  const max = v > 0 ? v : 1;
  const raw = max / 4;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * pow).find((s) => s >= raw);
  return { top: Math.ceil(max / step - 1e-9) * step, step };
}

function axisLabel(fmt, v, step) {
  if (v >= 100000) return fmt.compact(v);
  return fmt.num(v, step < 1 ? 2 : 0);
}

/** Tooltip neben (nicht über) die Markierung setzen. */
function placeTip(tip, chartBox, x) {
  const w = tip.offsetWidth;
  const left = x + 12 + w <= chartBox.width ? x + 12 : Math.max(x - 12 - w, 0);
  tip.style.left = `${left}px`;
  tip.style.top = "0px";
}

/** Rechteck mit abgerundeten oberen Ecken (Daten-Ende), unten bündig an der Basis. */
function topRoundedBar(x, y, w, h, r = 4) {
  if (h <= 0) return "";
  r = Math.min(r, h, w / 2);
  return `M${x},${y + h}L${x},${y + r}Q${x},${y} ${x + r},${y}L${x + w - r},${y}Q${x + w},${y} ${x + w},${y + r}L${x + w},${y + h}Z`;
}

function palette(hass) {
  return hass && hass.themes && hass.themes.darkMode ? PALETTE.dark : PALETTE.light;
}

/** Teilt die Datenabfrage zwischen Karte und Popup. */
function fetchData(hass, deviceId, month) {
  const msg = { type: "roi_tracker/data", device_id: deviceId };
  if (month) msg.month = month;
  return hass.callWS(msg);
}

// ─── Diagramme (SVG) ──────────────────────────────────────────────────────────

/**
 * Gestapeltes Balkendiagramm Ersparnis + Einspeisung.
 * rows: [{label, tip, savings, revenue, total}]
 */
function stackedBars(rows, { width, height, colors, fmt, t, clickable }) {
  const left = 46, right = 6, top = 8, bottom = 22;
  const plotW = Math.max(width - left - right, 40);
  const plotH = height - top - bottom;
  const scale = niceScale(Math.max(...rows.map((r) => Math.max(r.savings, 0) + Math.max(r.revenue, 0)), 0));
  const maxV = scale.top;
  const y0 = top + plotH;
  const band = plotW / Math.max(rows.length, 1);
  const barW = Math.max(Math.min(28, band * 0.64), 2);
  const labelEvery = Math.max(1, Math.ceil(rows.length / Math.max(Math.floor(plotW / 30), 1)));

  let grid = "";
  for (let v = 0; v <= maxV + 1e-9; v += scale.step) {
    const y = y0 - (v / maxV) * plotH;
    grid += `<line x1="${left}" x2="${left + plotW}" y1="${y}" y2="${y}" class="${v === 0 ? "axis" : "grid"}"/>`;
    grid += `<text x="${left - 6}" y="${y + 3.5}" text-anchor="end" class="tick">${esc(axisLabel(fmt, v, scale.step))}</text>`;
  }

  let bars = "";
  rows.forEach((r, i) => {
    const x = left + i * band + (band - barW) / 2;
    const s = Math.max(r.savings, 0), rv = Math.max(r.revenue, 0);
    const hs = (s / maxV) * plotH, hr = (rv / maxV) * plotH;
    const gap = hs > 0 && hr > 0 ? 2 : 0;
    if (hs > 0) {
      bars += hr > 0
        ? `<rect x="${x}" y="${y0 - hs}" width="${barW}" height="${hs}" fill="${colors.savings}"/>`
        : `<path d="${topRoundedBar(x, y0 - hs, barW, hs)}" fill="${colors.savings}"/>`;
    }
    if (hr > 0) bars += `<path d="${topRoundedBar(x, y0 - hs - gap - hr, barW, hr)}" fill="${colors.revenue}"/>`;
    if (i % labelEvery === 0) {
      bars += `<text x="${x + barW / 2}" y="${y0 + 14}" text-anchor="middle" class="tick">${esc(r.label)}</text>`;
    }
    bars += `<rect class="hit${clickable ? " clickable" : ""}" data-i="${i}" x="${left + i * band}" y="${top}" width="${band}" height="${plotH}" fill="transparent"/>`;
  });

  return `<div class="chart" data-kind="bars">
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img">${grid}${bars}</svg>
    <div class="tooltip" hidden></div>
  </div>`;
}

function bindBarTooltips(root, rows, { fmt, t, colors, onClick }) {
  root.querySelectorAll('.chart[data-kind="bars"]').forEach((chart) => {
    const tip = chart.querySelector(".tooltip");
    chart.querySelectorAll(".hit").forEach((hit) => {
      const r = rows[Number(hit.dataset.i)];
      hit.addEventListener("pointerenter", () => {
        tip.innerHTML = `<div class="tt-title">${esc(r.tip)}</div>
          <div class="tt-row"><span class="sw" style="background:${colors.savings}"></span>${t.savings}<b>${fmt.money(r.savings)}</b></div>
          <div class="tt-row"><span class="sw" style="background:${colors.revenue}"></span>${t.revenue}<b>${fmt.money(r.revenue)}</b></div>
          <div class="tt-row tt-sum">${t.sum}<b>${fmt.money(r.total)}</b></div>`;
        tip.hidden = false;
        const box = chart.getBoundingClientRect(), hb = hit.getBoundingClientRect();
        placeTip(tip, box, hb.left - box.left + hb.width / 2);
      });
      hit.addEventListener("pointerleave", () => { tip.hidden = true; });
      if (onClick) hit.addEventListener("click", (e) => { e.stopPropagation(); onClick(r); });
    });
  });
}

/** Kumulierter Ertrag (erreicht + Prognose) gegen die Investition. */
function forecastChart(points, { width, height, investment, color, fmt, t }) {
  const left = 52, right = 10, top = 14, bottom = 24;
  const plotW = Math.max(width - left - right, 40);
  const plotH = height - top - bottom;
  const scale = niceScale(Math.max(investment * 1.08, ...points.map((p) => p.value), 1));
  const maxV = scale.top;
  const n = points.length;
  const X = (i) => left + (n <= 1 ? plotW / 2 : (i / (n - 1)) * plotW);
  const Y = (v) => top + plotH - (Math.max(v, 0) / maxV) * plotH;

  let grid = "";
  for (let v = 0; v <= maxV + 1e-9; v += scale.step) {
    grid += `<line x1="${left}" x2="${left + plotW}" y1="${Y(v)}" y2="${Y(v)}" class="${v === 0 ? "axis" : "grid"}"/>`;
    grid += `<text x="${left - 6}" y="${Y(v) + 3.5}" text-anchor="end" class="tick">${esc(axisLabel(fmt, v, scale.step))}</text>`;
  }
  // x-Beschriftung: Monate bei kurzer Spanne, sonst jeder n-te Januar
  let xl = "";
  const yearly = n > 18;
  const maxLabels = Math.max(Math.floor(plotW / 44), 1);
  const every = Math.max(1, Math.ceil(n / maxLabels));
  const yearEvery = Math.max(1, Math.ceil(n / 12 / maxLabels));
  points.forEach((p, i) => {
    const show = yearly
      ? p.key.endsWith("-01") && Number(p.key.slice(0, 4)) % yearEvery === 0
      : i % every === 0;
    if (show) {
      xl += `<text x="${X(i)}" y="${top + plotH + 15}" text-anchor="middle" class="tick">${esc(yearly ? p.key.slice(0, 4) : fmt.month(p.key))}</text>`;
    }
  });

  const path = (pts) => pts.map((p, j) => `${j ? "L" : "M"}${X(p.i).toFixed(1)},${Y(p.value).toFixed(1)}`).join("");
  const idx = points.map((p, i) => ({ ...p, i }));
  const actual = idx.filter((p) => !p.projected);
  const lastActual = actual[actual.length - 1];
  const projected = idx.filter((p) => p.projected);
  const projPath = projected.length && lastActual ? path([lastActual, ...projected]) : "";

  const invY = Y(investment);
  let marker = "";
  const beIdx = idx.findIndex((p) => p.value >= investment && investment > 0);
  if (beIdx >= 0) {
    const p = idx[beIdx];
    const anchor = X(beIdx) > left + plotW - 60 ? "end" : "middle";
    marker = `<circle cx="${X(beIdx)}" cy="${Y(p.value)}" r="5" fill="${color}" class="ring"/>
      <text x="${X(beIdx)}" y="${Y(p.value) - 10}" text-anchor="${anchor}" class="label">${esc(fmt.monthYear(p.key))}</text>`;
  }

  return `<div class="chart" data-kind="line">
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img">
      ${grid}${xl}
      <line x1="${left}" x2="${left + plotW}" y1="${invY}" y2="${invY}" class="ref"/>
      <text x="${left + 4}" y="${invY - 5}" class="label muted">${esc(t.investment)} ${esc(fmt.money(investment, 0))}</text>
      ${actual.length ? `<path d="${path(actual)}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>` : ""}
      ${projPath ? `<path d="${projPath}" fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="5 4" stroke-linecap="round"/>` : ""}
      ${marker}
      <line class="cross" x1="0" x2="0" y1="${top}" y2="${top + plotH}" visibility="hidden"/>
      <circle class="cross-dot ring" r="4" fill="${color}" visibility="hidden"/>
      <rect class="overlay" x="${left}" y="${top}" width="${plotW}" height="${plotH}" fill="transparent"/>
    </svg>
    <div class="tooltip" hidden></div>
  </div>`;
}

function bindLineTooltip(root, points, { width, investment, fmt, t }) {
  const chart = root.querySelector('.chart[data-kind="line"]');
  if (!chart || !points.length) return;
  const svg = chart.querySelector("svg");
  const overlay = chart.querySelector(".overlay");
  const cross = chart.querySelector(".cross");
  const dot = chart.querySelector(".cross-dot");
  const tip = chart.querySelector(".tooltip");
  const left = Number(overlay.getAttribute("x")), plotW = Number(overlay.getAttribute("width"));
  const top = Number(overlay.getAttribute("y")), plotH = Number(overlay.getAttribute("height"));
  const n = points.length;
  // gleiche Skala wie in forecastChart
  const maxV = niceScale(Math.max(investment * 1.08, ...points.map((p) => p.value), 1)).top;
  const move = (ev) => {
    const box = svg.getBoundingClientRect();
    const scale = width / box.width;
    const x = (ev.clientX - box.left) * scale;
    const i = n <= 1 ? 0 : Math.round(((x - left) / plotW) * (n - 1));
    const p = points[Math.min(Math.max(i, 0), n - 1)];
    const px = n <= 1 ? left + plotW / 2 : left + (Math.min(Math.max(i, 0), n - 1) / (n - 1)) * plotW;
    const py = top + plotH - (Math.max(p.value, 0) / maxV) * plotH;
    cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
    dot.setAttribute("cx", px); dot.setAttribute("cy", py); dot.setAttribute("visibility", "visible");
    tip.innerHTML = `<div class="tt-title">${esc(fmt.monthYear(p.key))}</div>
      <div class="tt-row">${p.projected ? t.projected : t.actual}<b>${fmt.money(p.value, 0)}</b></div>`;
    tip.hidden = false;
    placeTip(tip, box, px / scale);
  };
  overlay.addEventListener("pointermove", move);
  overlay.addEventListener("pointerdown", move);
  overlay.addEventListener("pointerleave", () => {
    tip.hidden = true;
    cross.setAttribute("visibility", "hidden");
    dot.setAttribute("visibility", "hidden");
  });
}

/**
 * Punkte für das Prognose-Diagramm. Jeder Punkt = kumulierter Ertrag am
 * Monatsende (laufender Monat: Stand heute), danach Hochrechnung.
 */
function forecastPoints(data) {
  const k = data.kpis || {};
  const pts = [];
  let cum = 0;
  for (const m of data.months || []) {
    cum += m.total;
    pts.push({ key: m.period, value: cum, projected: false });
  }
  const rate = (k.yearly_estimate || 0) / 12;
  if (!pts.length || rate <= 0) return pts;
  const inv = k.investment || 0;
  // Stand am Ende des laufenden Monats (noch nicht als eigener Punkt)
  let value = cum + Math.max((k.month_forecast || 0) - ((k.month || {}).total || 0), 0);
  let [y, m] = pts[pts.length - 1].key.split("-").map(Number);
  // Schon abbezahlt: 12 Monate zeigen. Sonst bis zum Break-Even + 2 Monate.
  let extra = value >= inv ? 12 : null;
  for (let i = 0; i < 360; i++) {
    m += 1;
    if (m > 12) { m = 1; y += 1; }
    value += rate;
    pts.push({ key: `${y}-${String(m).padStart(2, "0")}`, value, projected: true });
    if (extra === null && value >= inv) extra = 3;
    if (extra !== null && --extra <= 0) break;
  }
  return pts;
}

// ─── Gemeinsame Styles ───────────────────────────────────────────────────────

const BASE_CSS = `
  :host { display:block; }
  .muted { color: var(--secondary-text-color); }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  .chart { position:relative; width:100%; overflow:hidden; }
  .chart svg { display:block; max-width:100%; height:auto; overflow:visible; }
  .chart .tick { font-size:10px; fill: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
  .chart .label { font-size:11px; fill: var(--primary-text-color); font-weight:500; }
  .chart .label.muted { fill: var(--secondary-text-color); font-weight:400; }
  .chart .grid { stroke: var(--divider-color, #e1e0d9); stroke-width:1; opacity:.6; }
  .chart .axis { stroke: var(--divider-color, #c3c2b7); stroke-width:1; }
  .chart .ref { stroke: var(--secondary-text-color); stroke-width:1; stroke-dasharray:3 3; opacity:.8; }
  .chart .cross { stroke: var(--secondary-text-color); stroke-width:1; opacity:.6; }
  .chart .ring { stroke: var(--card-background-color, var(--ha-card-background, #fff)); stroke-width:2; }
  .chart .hit.clickable { cursor:pointer; }
  .chart .hit:hover { fill: var(--primary-text-color); fill-opacity:.05; }
  .tooltip { position:absolute; pointer-events:none; z-index:2; min-width:150px;
    background: var(--card-background-color, var(--ha-card-background, #fff)); color: var(--primary-text-color);
    border:1px solid var(--divider-color, rgba(0,0,0,.12)); border-radius:8px; padding:6px 10px;
    box-shadow:0 2px 8px rgba(0,0,0,.15); font-size:12px; }
  .tt-title { font-weight:600; margin-bottom:4px; }
  .tt-row { display:flex; align-items:center; gap:6px; }
  .tt-row b { margin-left:auto; font-weight:600; padding-left:12px; font-variant-numeric: tabular-nums; }
  .tt-sum { border-top:1px solid var(--divider-color, #e0e0e0); margin-top:3px; padding-top:3px; }
  .sw { width:10px; height:10px; border-radius:2px; display:inline-block; }
  .legend { display:flex; gap:14px; flex-wrap:wrap; font-size:12px; color: var(--secondary-text-color); margin:4px 0 6px; }
  .legend span { display:flex; align-items:center; gap:5px; }
  .bar-track { height:6px; border-radius:3px; background: var(--divider-color, #e0e0e0); overflow:hidden; }
  .bar-fill { height:100%; border-radius:3px; transition:width .6s ease; }
`;

// ─── Karte ────────────────────────────────────────────────────────────────────

class RoiTrackerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._data = null;
    this._error = null;
    this._loading = false;
    this._fetchedAt = 0;
    this._dialog = null;
    this._dark = null;
    this._width = 0;
  }

  static getConfigElement() { return document.createElement("roi-tracker-card-editor"); }
  static getStubConfig() { return { type: "custom:roi-tracker-card", device: "", variant: "standard" }; }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    const deviceChanged = config.device !== this._config.device;
    this._config = { variant: "standard", ...config };
    if (deviceChanged) { this._data = null; this._fetchedAt = 0; }
    this._render();
    this._maybeFetch();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._dialog) this._dialog.hass = hass;
    const dark = !!(hass.themes && hass.themes.darkMode);
    if (dark !== this._dark) { this._dark = dark; this._render(); }
    this._maybeFetch();
  }

  connectedCallback() {
    if (!this._ro && window.ResizeObserver) {
      this._ro = new ResizeObserver(() => {
        const w = Math.round(this.clientWidth);
        if (Math.abs(w - this._width) > 8) { this._width = w; if (this._variant() === "full") this._render(); }
      });
    }
    if (this._ro) this._ro.observe(this);
  }

  disconnectedCallback() { if (this._ro) this._ro.disconnect(); }

  getCardSize() { return { mini: 1, compact: 3, standard: 4, full: 7 }[this._variant()] || 4; }

  getGridOptions() {
    return this._variant() === "mini" ? { columns: 6, min_columns: 3 } : { columns: 12, min_columns: 6 };
  }

  _variant() { return VARIANTS.includes(this._config.variant) ? this._config.variant : "standard"; }
  _t() { return TXT[langOf(this._hass, this._config)]; }
  _fmt() { return makeFmt(langOf(this._hass, this._config), this._data && this._data.currency); }

  _maybeFetch() {
    if (!this._hass || !this._config.device || this._loading) return;
    if (Date.now() - this._fetchedAt < REFRESH_MS) return;
    this._loading = true;
    fetchData(this._hass, this._config.device)
      .then((d) => { this._data = d; this._error = null; this._fetchedAt = Date.now(); })
      .catch((e) => {
        this._error = (e && e.message) || String(e);
        this._fetchedAt = Date.now() - REFRESH_MS + 30000; // in 30 s erneut versuchen
      })
      .finally(() => {
        this._loading = false;
        this._render();
        if (this._dialog) this._dialog.data = this._data;
      });
  }

  _openDialog() {
    if (!this._data || this._dialog) return;
    const dlg = document.createElement("roi-tracker-dialog");
    dlg.setup(this, this._hass, this._config, this._data);
    this._dialog = dlg;
  }

  // ── Rendern ────────────────────────────────────────────────────────────────

  _render() {
    if (!this.shadowRoot) return;
    const t = this._t();
    const title = (this._config.title || "").trim();
    const header = title ? `<div class="card-header">${esc(title)}</div>` : "";
    let body;
    if (!this._config.device) body = `<div class="msg">${t.no_device}</div>`;
    else if (!this._data && this._error) body = `<div class="msg">${t.error}: ${esc(this._error)}</div>`;
    else if (!this._data) body = `<div class="msg">${t.loading}</div>`;
    else body = this[`_render_${this._variant()}`]();

    const clickable = !!this._data;
    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${CARD_CSS}</style>
      <ha-card class="${clickable ? "clickable" : ""} v-${this._variant()}" ${clickable ? `tabindex="0" role="button" aria-label="${esc(t.details)}"` : ""}>
        ${header}
        <div class="content${title ? "" : " no-title"}">${body}</div>
      </ha-card>`;

    if (clickable) {
      const card = this.shadowRoot.querySelector("ha-card");
      card.addEventListener("click", () => this._openDialog());
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this._openDialog(); }
      });
      if (this._variant() === "full") {
        const colors = palette(this._hass);
        bindBarTooltips(this.shadowRoot, this._chartRows, { fmt: this._fmt(), t, colors });
      }
    }
  }

  _k() { return (this._data && this._data.kpis) || {}; }

  _amortPct() { return Math.max(0, Math.min(this._k().amortization || 0, 100)); }

  _render_mini() {
    const t = this._t(), f = this._fmt(), k = this._k(), c = palette(this._hass);
    const pct = this._amortPct();
    return `<div class="mini">
      <div class="mini-row">
        <span class="mini-label">${t.total_return}</span>
        <span class="mini-value">${f.money(k.total_return, 0)}</span>
        <span class="mini-pct">${k.breakeven_reached ? "✓ " + t.paid_off : f.num(k.amortization, 0) + " %"}</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${c.savings}"></div></div>
    </div>`;
  }

  _donut(pct, color) {
    const t = this._t(), k = this._k();
    const r = 38, circ = 2 * Math.PI * r, filled = (circ * pct) / 100;
    const label = k.breakeven_reached ? "✓" : `${Math.round(k.amortization || 0)}%`;
    return `<svg viewBox="0 0 100 100" class="donut" aria-hidden="true">
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="var(--divider-color,#e0e0e0)" stroke-width="10"/>
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round"
        stroke-dasharray="${filled} ${circ - filled}" stroke-dashoffset="${circ * 0.25}"/>
      <text x="50" y="49" text-anchor="middle" font-size="18" font-weight="700" fill="var(--primary-text-color)">${label}</text>
      <text x="50" y="63" text-anchor="middle" font-size="9" fill="var(--secondary-text-color)">${k.breakeven_reached ? t.paid_off : t.amortization}</text>
    </svg>`;
  }

  _render_compact() {
    const t = this._t(), f = this._fmt(), k = this._k(), c = palette(this._hass);
    return `<div class="hero">
      ${this._donut(this._amortPct(), c.savings)}
      <div class="hero-text">
        <div class="hero-label">${t.total_return}</div>
        <div class="hero-total">${f.money(k.total_return)}</div>
        <div class="hero-split">
          <span><i class="dot" style="background:${c.savings}"></i>${t.savings} ${f.money(k.savings, 0)}</span>
          <span><i class="dot" style="background:${c.revenue}"></i>${t.revenue} ${f.money(k.revenue, 0)}</span>
        </div>
        <div class="hero-sub">${t.investment} ${f.money(k.investment, 0)}${k.remaining > 0 ? ` · ${t.remaining} ${f.money(k.remaining, 0)}` : ""}</div>
      </div>
    </div>`;
  }

  _tiles() {
    const t = this._t(), f = this._fmt(), k = this._k();
    const be = k.breakeven_reached
      ? `✓ ${f.date(k.breakeven_date, { month: "short", year: "numeric" })}`
      : k.breakeven_date ? f.date(k.breakeven_date, { month: "short", year: "numeric" }) : "–";
    const tiles = [
      [t.this_month, f.money((k.month || {}).total, 0), `${t.month_forecast} ${f.money(k.month_forecast, 0)}`],
      [t.yearly, f.money(k.yearly_estimate, 0), k.projection_provisional ? t.provisional : ""],
      [t.breakeven, be, !k.breakeven_reached && k.years_to_breakeven != null ? t.time_left(k.years_to_breakeven, f) : ""],
      [t.roi, `${f.num(k.roi, 1)} %`, `${t.today} ${f.money((k.today || {}).total)}`],
    ];
    return `<div class="tiles">${tiles.map(([lbl, val, sub]) => `
      <div class="tile"><div class="tile-lbl">${lbl}</div><div class="tile-val">${val}</div>
      <div class="tile-sub">${sub || "&nbsp;"}</div></div>`).join("")}</div>`;
  }

  _render_standard() { return this._render_compact() + this._tiles(); }

  _render_full() {
    const t = this._t(), f = this._fmt(), c = palette(this._hass);
    const months = (this._data.months || []).slice(-12);
    this._chartRows = months.map((m) => ({
      label: f.month(m.period), tip: f.monthYear(m.period),
      savings: m.savings, revenue: m.revenue, total: m.total,
    }));
    const width = Math.max((this.clientWidth || 360) - 32, 240);
    const chart = months.length
      ? stackedBars(this._chartRows, { width, height: 150, colors: c, fmt: f, t })
      : `<div class="msg">${t.no_data}</div>`;
    return `${this._render_standard()}
      <div class="section-title">${t.last_12}</div>
      <div class="legend"><span><i class="sw" style="background:${c.savings}"></i>${t.savings}</span>
        <span><i class="sw" style="background:${c.revenue}"></i>${t.revenue}</span></div>
      ${chart}`;
  }
}

const CARD_CSS = `
  ha-card { overflow:hidden; }
  ha-card.clickable { cursor:pointer; }
  ha-card.clickable:focus-visible { outline:2px solid var(--primary-color); outline-offset:2px; }
  .card-header { padding:12px 16px 0; font-size:1.1em; font-weight:600; color: var(--ha-card-header-color, var(--primary-text-color)); }
  .content { padding:8px 16px 16px; }
  .content.no-title { padding-top:14px; }
  .v-mini .content { padding:12px 16px; }
  .msg { padding:12px 0; text-align:center; color: var(--secondary-text-color); font-size:.9em; }
  .mini-row { display:flex; align-items:baseline; gap:8px; margin-bottom:8px; }
  .mini-label { color: var(--secondary-text-color); font-size:.9em; }
  .mini-value { font-weight:700; font-size:1.25em; margin-left:auto; color: var(--primary-text-color); }
  .mini-pct { font-size:.85em; color: var(--secondary-text-color); min-width:3.5em; text-align:right; }
  .hero { display:flex; align-items:center; gap:16px; }
  .donut { width:92px; height:92px; flex-shrink:0; }
  .hero-text { flex:1; min-width:0; }
  .hero-label { font-size:.8em; color: var(--secondary-text-color); }
  .hero-total { font-size:1.9em; font-weight:700; color: var(--primary-text-color); line-height:1.2; white-space:nowrap; }
  .hero-split { display:flex; flex-wrap:wrap; gap:4px 12px; font-size:.85em; color: var(--primary-text-color); margin:4px 0 2px; }
  .hero-split span { display:flex; align-items:center; gap:5px; }
  .hero-sub { font-size:.8em; color: var(--secondary-text-color); }
  .tiles { display:grid; grid-template-columns:repeat(2, 1fr); gap:8px; margin-top:14px; }
  @container (min-width: 420px) { .tiles { grid-template-columns:repeat(4, 1fr); } }
  .content { container-type:inline-size; }
  .tile { background: var(--secondary-background-color, rgba(127,127,127,.08)); border-radius:10px; padding:8px 10px; }
  .tile-lbl { font-size:.72em; color: var(--secondary-text-color); }
  .tile-val { font-size:1.05em; font-weight:600; color: var(--primary-text-color); margin-top:2px; white-space:nowrap; }
  .tile-sub { font-size:.7em; color: var(--secondary-text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .section-title { font-size:.75em; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color: var(--secondary-text-color); margin:16px 0 2px; }
`;

// ─── Popup ────────────────────────────────────────────────────────────────────

class RoiTrackerDialog extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "overview";
    this._year = null;
    this._month = null; // ausgewählter Monat → Tagesansicht
    this._monthData = null;
    this._onKey = (e) => { if (e.key === "Escape") this.close(); };
  }

  setup(card, hass, config, data) {
    this._card = card;
    this._hass = hass;
    this._config = config;
    this._data = data;
    document.body.appendChild(this);
    document.addEventListener("keydown", this._onKey);
    this._render();
    const closeBtn = this.shadowRoot.querySelector(".close");
    if (closeBtn) closeBtn.focus();
  }

  set hass(h) { this._hass = h; }
  set data(d) { if (d) { this._data = d; this._render(); } }

  close() {
    document.removeEventListener("keydown", this._onKey);
    this.remove();
    if (this._card) this._card._dialog = null;
  }

  _t() { return TXT[langOf(this._hass, this._config)]; }
  _fmt() { return makeFmt(langOf(this._hass, this._config), this._data.currency); }
  _width() {
    const panel = this.shadowRoot.querySelector(".body");
    const w = panel ? panel.clientWidth : Math.min(window.innerWidth - 16, 760);
    return Math.max(w - 8, 260);
  }

  _render() {
    const t = this._t();
    const title = (this._config.title || "").trim() || this._data.name || "ROI Tracker";
    const tabs = [["overview", t.tab_overview], ["months", t.tab_months], ["forecast", t.tab_forecast]];
    const scroll = this.shadowRoot.querySelector(".body");
    const scrollTop = scroll ? scroll.scrollTop : 0;
    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${DIALOG_CSS}</style>
      <div class="backdrop"></div>
      <div class="panel" role="dialog" aria-modal="true" aria-label="${esc(title)}">
        <div class="head">
          <div class="title">${esc(title)}</div>
          <button class="close" aria-label="${t.close}">✕</button>
        </div>
        <div class="tabs" role="tablist">
          ${tabs.map(([id, label]) => `<button role="tab" data-tab="${id}" aria-selected="${this._tab === id}" class="${this._tab === id ? "active" : ""}">${label}</button>`).join("")}
        </div>
        <div class="body"></div>
      </div>`;
    const root = this.shadowRoot;
    root.querySelector(".backdrop").addEventListener("click", () => this.close());
    root.querySelector(".close").addEventListener("click", () => this.close());
    root.querySelectorAll(".tabs button").forEach((b) =>
      b.addEventListener("click", () => { this._tab = b.dataset.tab; this._month = null; this._render(); }));
    const body = root.querySelector(".body");
    body.innerHTML = this[`_tab_${this._tab}`]();
    this[`_bind_${this._tab}`] && this[`_bind_${this._tab}`](body);
    body.scrollTop = scrollTop;
  }

  // ── Übersicht ──────────────────────────────────────────────────────────────

  _tab_overview() {
    const t = this._t(), f = this._fmt(), d = this._data, k = d.kpis || {};
    const c = palette(this._hass);
    if (!k.data_since) return `<div class="msg">${t.no_data}</div>`;
    const pct = Math.max(0, Math.min(k.amortization || 0, 100));
    const stat = (label, value, sub = "") =>
      `<div class="stat"><div class="stat-lbl">${label}</div><div class="stat-val">${value}</div>${sub ? `<div class="stat-sub">${sub}</div>` : ""}</div>`;
    const be = k.breakeven_reached
      ? `✓ ${f.date(k.breakeven_date)}`
      : k.breakeven_date ? f.date(k.breakeven_date) : "–";
    return `
      <div class="big">
        <div class="stat-lbl">${t.total_return}</div>
        <div class="big-val">${f.money(k.total_return)}</div>
        <div class="bar-track big-bar"><div class="bar-fill" style="width:${pct}%;background:${c.savings}"></div></div>
        <div class="stat-sub">${f.num(k.amortization, 1)} % ${t.amortization.toLowerCase()} · ${t.investment} ${f.money(k.investment, 0)}${k.remaining > 0 ? ` · ${t.remaining} ${f.money(k.remaining, 0)}` : ""}</div>
      </div>
      <div class="stats">
        ${stat(`<i class="dot" style="background:${c.savings}"></i> ${t.savings}`, f.money(k.savings), `${f.num(k.self_kwh, 0)} kWh · ${t.avg_price} ${k.avg_price != null ? f.money(k.avg_price, 3) : "–"}`)}
        ${stat(`<i class="dot" style="background:${c.revenue}"></i> ${t.revenue_long}`, f.money(k.revenue), `${f.num(k.export_kwh, 0)} kWh · ${f.money(d.feed_in_tariff, 3)}/kWh`)}
        ${stat(t.roi, `${f.num(k.roi, 1)} %`)}
        ${stat(t.breakeven, be, !k.breakeven_reached && k.years_to_breakeven != null ? t.time_left(k.years_to_breakeven, f) : "")}
        ${stat(t.today, f.money((k.today || {}).total), `${f.num((k.today || {}).self_kwh, 1)} kWh ${t.self_kwh}`)}
        ${stat(t.this_month, f.money((k.month || {}).total), `${t.month_forecast} ${f.money(k.month_forecast, 0)}`)}
        ${stat(t.yearly, f.money(k.yearly_estimate, 0), k.projection_provisional ? t.provisional : "")}
        ${stat(t.daily, f.money(k.daily_average))}
      </div>
      <div class="facts">
        <div><span>${t.price_source}</span><b>${d.price_source === "sensor" ? t.price_sensor : t.price_fixed}${d.current_price != null ? ` · ${f.money(d.current_price, 3)}/kWh` : ""}</b></div>
        <div><span>${t.data_since}</span><b>${f.date(k.data_since)}</b></div>
      </div>
      ${d.missing_price_hours > 0 ? `<div class="note">${t.missing_prices(d.missing_price_hours)}</div>` : ""}`;
  }

  // ── Monate / Tage ──────────────────────────────────────────────────────────

  _years() {
    return [...new Set((this._data.months || []).map((m) => m.period.slice(0, 4)))].sort();
  }

  _tab_months() {
    const t = this._t(), f = this._fmt(), c = palette(this._hass);
    if (!(this._data.months || []).length) return `<div class="msg">${t.no_data}</div>`;
    if (this._month) return this._daysView();

    const years = this._years();
    if (!this._year || !years.includes(this._year)) this._year = years[years.length - 1];
    const byKey = Object.fromEntries(this._data.months.map((m) => [m.period, m]));
    const empty = { savings: 0, revenue: 0, total: 0, self_kwh: 0, export_kwh: 0, avg_price: null };
    const months = Array.from({ length: 12 }, (_, i) => {
      const key = `${this._year}-${String(i + 1).padStart(2, "0")}`;
      return { key, ...(byKey[key] || empty), has: !!byKey[key] };
    });
    this._rows = months.map((m) => ({
      key: m.key, label: f.month(m.key, "narrow"), tip: f.monthYear(m.key),
      savings: m.savings, revenue: m.revenue, total: m.total, has: m.has,
    }));
    const year = (this._data.years || []).find((y) => y.period === this._year) || empty;

    return `
      <div class="chips">${years.map((y) => `<button class="chip${y === this._year ? " active" : ""}" data-year="${y}">${y}</button>`).join("")}</div>
      <div class="legend"><span><i class="sw" style="background:${c.savings}"></i>${t.savings}</span>
        <span><i class="sw" style="background:${c.revenue}"></i>${t.revenue}</span></div>
      ${stackedBars(this._rows, { width: this._width(), height: 190, colors: c, fmt: f, t, clickable: true })}
      <div class="table-wrap"><table>
        <thead><tr><th>${t.month}</th><th>${t.self_kwh}</th><th>${t.export_kwh}</th><th>${t.savings}</th><th>${t.revenue}</th><th>${t.sum}</th><th>${t.avg_price}</th></tr></thead>
        <tbody>${months.filter((m) => m.has).map((m) => `
          <tr class="clickable" data-month="${m.key}">
            <td>${esc(f.month(m.key, "long"))}</td><td>${f.num(m.self_kwh, 0)} kWh</td><td>${f.num(m.export_kwh, 0)} kWh</td>
            <td>${f.money(m.savings)}</td><td>${f.money(m.revenue)}</td><td><b>${f.money(m.total)}</b></td>
            <td>${m.avg_price != null ? f.money(m.avg_price, 3) : "–"}</td></tr>`).join("")}
        </tbody>
        <tfoot><tr><td>${this._year}</td><td>${f.num(year.self_kwh, 0)} kWh</td><td>${f.num(year.export_kwh, 0)} kWh</td>
          <td>${f.money(year.savings)}</td><td>${f.money(year.revenue)}</td><td><b>${f.money(year.total)}</b></td>
          <td>${year.avg_price != null ? f.money(year.avg_price, 3) : "–"}</td></tr></tfoot>
      </table></div>
      ${years.length > 1 ? this._yearsTable() : ""}`;
  }

  _yearsTable() {
    const t = this._t(), f = this._fmt();
    return `<div class="section-title">${t.years_title}</div>
      <div class="table-wrap"><table>
        <thead><tr><th>${t.year}</th><th>${t.self_kwh}</th><th>${t.export_kwh}</th><th>${t.savings}</th><th>${t.revenue}</th><th>${t.sum}</th></tr></thead>
        <tbody>${this._data.years.map((y) => `<tr><td>${y.period}</td><td>${f.num(y.self_kwh, 0)} kWh</td>
          <td>${f.num(y.export_kwh, 0)} kWh</td><td>${f.money(y.savings)}</td><td>${f.money(y.revenue)}</td>
          <td><b>${f.money(y.total)}</b></td></tr>`).join("")}</tbody>
      </table></div>`;
  }

  _openMonth(key) {
    this._month = key;
    this._monthData = null;
    this._render();
    fetchData(this._hass, this._config.device, key)
      .then((d) => { if (this._month === key) { this._monthData = d.days || []; this._render(); } })
      .catch(() => { if (this._month === key) { this._monthData = []; this._render(); } });
  }

  _daysView() {
    const t = this._t(), f = this._fmt(), c = palette(this._hass);
    const back = `<button class="link back">${t.back} ${this._year}</button>`;
    const title = `<div class="section-title">${t.days_of} ${esc(f.monthYear(this._month))}</div>`;
    if (!this._monthData) return `${back}${title}<div class="msg">${t.loading}</div>`;
    const [y, m] = this._month.split("-").map(Number);
    const nDays = new Date(y, m, 0).getDate();
    const byKey = Object.fromEntries(this._monthData.map((d) => [d.period, d]));
    this._rows = Array.from({ length: nDays }, (_, i) => {
      const key = `${this._month}-${String(i + 1).padStart(2, "0")}`;
      const d = byKey[key] || { savings: 0, revenue: 0, total: 0 };
      return { key, label: String(i + 1), tip: f.date(key, { weekday: "short", day: "2-digit", month: "long" }), savings: d.savings, revenue: d.revenue, total: d.total };
    });
    return `${back}${title}
      <div class="legend"><span><i class="sw" style="background:${c.savings}"></i>${t.savings}</span>
        <span><i class="sw" style="background:${c.revenue}"></i>${t.revenue}</span></div>
      ${stackedBars(this._rows, { width: this._width(), height: 190, colors: c, fmt: f, t })}
      <div class="table-wrap"><table>
        <thead><tr><th>${t.day}</th><th>${t.self_kwh}</th><th>${t.export_kwh}</th><th>${t.savings}</th><th>${t.revenue}</th><th>${t.sum}</th></tr></thead>
        <tbody>${this._monthData.map((d) => `<tr><td>${esc(f.date(d.period, { weekday: "short", day: "2-digit", month: "2-digit" }))}</td>
          <td>${f.num(d.self_kwh, 1)} kWh</td><td>${f.num(d.export_kwh, 1)} kWh</td><td>${f.money(d.savings)}</td>
          <td>${f.money(d.revenue)}</td><td><b>${f.money(d.total)}</b></td></tr>`).join("")}</tbody>
      </table></div>`;
  }

  _bind_months(body) {
    const f = this._fmt(), t = this._t(), c = palette(this._hass);
    body.querySelectorAll(".chip").forEach((b) =>
      b.addEventListener("click", () => { this._year = b.dataset.year; this._render(); }));
    body.querySelectorAll("tr[data-month]").forEach((tr) =>
      tr.addEventListener("click", () => this._openMonth(tr.dataset.month)));
    const back = body.querySelector(".back");
    if (back) back.addEventListener("click", () => { this._month = null; this._render(); });
    if (this._rows) {
      bindBarTooltips(body, this._rows, {
        fmt: f, t, colors: c,
        onClick: this._month ? null : (r) => { if (r.has) this._openMonth(r.key); },
      });
    }
  }

  // ── Prognose ───────────────────────────────────────────────────────────────

  _tab_forecast() {
    const t = this._t(), f = this._fmt(), k = this._data.kpis || {}, c = palette(this._hass);
    if (!k.data_since) return `<div class="msg">${t.no_data}</div>`;
    this._points = forecastPoints(this._data);
    let text;
    if (k.breakeven_reached) text = t.fc_done(f.date(k.breakeven_date));
    else if (k.breakeven_date) {
      const yrs = k.years_to_breakeven;
      const span = yrs == null ? "" : yrs < 1 ? t.months_unit(Math.max(1, Math.round(yrs * 12))) : t.years_unit(f.num(yrs, 1));
      text = t.fc_intro(f.money(k.yearly_estimate, 0), f.monthYear(k.breakeven_date.slice(0, 7)), span);
    } else text = t.fc_none;
    const days = Math.max(1, Math.round((Date.now() - new Date(k.data_since).getTime()) / 86400000));
    const width = this._width();
    return `<p class="lead">${text}</p>
      <div class="legend"><span><svg width="22" height="8"><line x1="0" x2="22" y1="4" y2="4" stroke="${c.savings}" stroke-width="2"/></svg>${t.actual}</span>
        <span><svg width="22" height="8"><line x1="0" x2="22" y1="4" y2="4" stroke="${c.savings}" stroke-width="2" stroke-dasharray="5 4"/></svg>${t.projected}</span>
        <span><svg width="22" height="8"><line x1="0" x2="22" y1="4" y2="4" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/></svg>${t.investment}</span></div>
      ${this._points.length ? forecastChart(this._points, { width, height: 230, investment: k.investment || 0, color: c.savings, fmt: f, t }) : ""}
      <div class="stats">
        <div class="stat"><div class="stat-lbl">${t.yearly}</div><div class="stat-val">${f.money(k.yearly_estimate, 0)}</div></div>
        <div class="stat"><div class="stat-lbl">${t.daily}</div><div class="stat-val">${f.money(k.daily_average)}</div></div>
        <div class="stat"><div class="stat-lbl">${t.remaining}</div><div class="stat-val">${f.money(k.remaining, 0)}</div></div>
        <div class="stat"><div class="stat-lbl">${t.roi}</div><div class="stat-val">${f.num(k.roi, 1)} %</div></div>
      </div>
      <div class="note">${k.projection_provisional ? t.fc_prov(days) : t.fc_seasonal}</div>`;
  }

  _bind_forecast(body) {
    bindLineTooltip(body, this._points || [], {
      width: this._width(),
      investment: (this._data.kpis || {}).investment || 0,
      fmt: this._fmt(),
      t: this._t(),
    });
  }
}

const DIALOG_CSS = `
  :host { position:fixed; inset:0; z-index:9999; display:flex; align-items:center; justify-content:center; }
  .backdrop { position:absolute; inset:0; background:rgba(0,0,0,.45); }
  .panel { position:relative; width:min(780px, calc(100vw - 16px)); max-height:calc(100vh - 32px);
    display:flex; flex-direction:column; border-radius:16px; overflow:hidden;
    background: var(--card-background-color, var(--ha-card-background, #fff)); color: var(--primary-text-color);
    box-shadow:0 10px 40px rgba(0,0,0,.35); font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif); }
  @media (max-width: 600px) { :host { align-items:flex-end; } .panel { width:100vw; max-height:92vh; border-radius:16px 16px 0 0; } }
  .head { display:flex; align-items:center; padding:14px 16px 6px; }
  .title { font-size:1.15em; font-weight:600; flex:1; }
  .close { background:none; border:none; font-size:1.1em; cursor:pointer; color: var(--secondary-text-color); padding:6px 8px; border-radius:8px; }
  .close:hover { background: var(--secondary-background-color, rgba(127,127,127,.12)); }
  .tabs { display:flex; gap:4px; padding:0 12px; border-bottom:1px solid var(--divider-color, #e0e0e0); }
  .tabs button { background:none; border:none; padding:10px 12px; cursor:pointer; font-size:.95em;
    color: var(--secondary-text-color); border-bottom:2px solid transparent; margin-bottom:-1px; }
  .tabs button.active { color: var(--primary-text-color); border-bottom-color: var(--primary-color, #03a9f4); font-weight:600; }
  .body { padding:14px 16px 20px; overflow-y:auto; }
  .msg { padding:24px 0; text-align:center; color: var(--secondary-text-color); }
  .big { margin-bottom:14px; }
  .big-val { font-size:2.1em; font-weight:700; line-height:1.15; }
  .big-bar { height:8px; border-radius:4px; margin:8px 0 6px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:8px; margin:10px 0; }
  .stat { background: var(--secondary-background-color, rgba(127,127,127,.08)); border-radius:10px; padding:10px 12px; }
  .stat-lbl { font-size:.78em; color: var(--secondary-text-color); display:flex; align-items:center; gap:5px; }
  .stat-val { font-size:1.15em; font-weight:600; margin-top:2px; }
  .stat-sub { font-size:.75em; color: var(--secondary-text-color); margin-top:2px; }
  .facts { font-size:.85em; margin-top:8px; }
  .facts div { display:flex; justify-content:space-between; gap:12px; padding:6px 0; border-bottom:1px solid var(--divider-color, #e0e0e0); }
  .facts span { color: var(--secondary-text-color); }
  .note { font-size:.8em; color: var(--secondary-text-color); margin-top:10px; }
  .lead { margin:4px 0 10px; line-height:1.45; }
  .chips { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px; }
  .chip { border:1px solid var(--divider-color, #ccc); background:none; color: var(--primary-text-color);
    border-radius:16px; padding:4px 12px; cursor:pointer; font-size:.85em; }
  .chip.active { background: var(--primary-color, #03a9f4); border-color: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff); }
  .link { background:none; border:none; color: var(--primary-color, #03a9f4); cursor:pointer; padding:0; font-size:.9em; }
  .section-title { font-size:.75em; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color: var(--secondary-text-color); margin:18px 0 6px; }
  .table-wrap { overflow-x:auto; margin-top:10px; }
  table { width:100%; border-collapse:collapse; font-size:.85em; font-variant-numeric: tabular-nums; }
  th, td { padding:7px 8px; text-align:right; white-space:nowrap; border-bottom:1px solid var(--divider-color, #e0e0e0); }
  th:first-child, td:first-child { text-align:left; }
  th { font-weight:600; color: var(--secondary-text-color); font-size:.9em; }
  tfoot td { font-weight:600; border-bottom:none; }
  tr.clickable { cursor:pointer; }
  tr.clickable:hover td { background: var(--secondary-background-color, rgba(127,127,127,.08)); }
`;

// ─── Editor ───────────────────────────────────────────────────────────────────
// Reines HTML, damit der Editor nicht von HA-internen Elementen abhängt.

class RoiTrackerCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
    this._built = false;
    this._devSig = null;
  }

  setConfig(config) { this._config = config || {}; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _devices() {
    const hass = this._hass;
    if (!hass) return [];
    const found = new Map();
    const devices = hass.devices || {};
    for (const [id, dev] of Object.entries(devices)) {
      if ((dev.identifiers || []).some((p) => Array.isArray(p) && p[0] === "roi_tracker")) {
        found.set(id, dev.name_by_user || dev.name || id);
      }
    }
    for (const ent of Object.values(hass.entities || {})) {
      if (ent && ent.platform === "roi_tracker" && ent.device_id && !found.has(ent.device_id)) {
        const dev = devices[ent.device_id] || {};
        found.set(ent.device_id, dev.name_by_user || dev.name || ent.device_id);
      }
    }
    return [...found.entries()].map(([id, name]) => ({ id, name }));
  }

  _render() {
    if (!this._hass) return;
    const t = TXT[langOf(this._hass, this._config)];
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const root = this.shadowRoot;

    if (!this._built) {
      this._built = true;
      root.innerHTML = `<style>
          .form { display:flex; flex-direction:column; gap:14px; padding:8px 0; }
          label { display:block; font-size:.85em; color: var(--secondary-text-color); margin-bottom:4px; }
          select, input { width:100%; padding:9px; box-sizing:border-box; font-size:1em; border-radius:6px;
            border:1px solid var(--divider-color, #ccc); background: var(--card-background-color, #fff); color: var(--primary-text-color); }
          .hint { font-size:.8em; color: var(--warning-color, #ff9800); margin-top:4px; display:none; }
        </style>
        <div class="form">
          <div><label for="device">${t.editor_device}</label><select id="device"></select>
            <div class="hint" id="hint">${t.editor_no_dev}</div></div>
          <div><label for="variant">${t.editor_variant}</label><select id="variant">
            ${VARIANTS.map((v) => `<option value="${v}">${t["v_" + v]}</option>`).join("")}</select></div>
          <div><label for="title">${t.editor_title}</label><input id="title" type="text"/></div>
        </div>`;
      root.getElementById("device").addEventListener("change", (e) => this._emit({ device: e.target.value }));
      root.getElementById("variant").addEventListener("change", (e) => this._emit({ variant: e.target.value }));
      root.getElementById("title").addEventListener("input", (e) => this._emit({ title: e.target.value }));
    }

    const devices = this._devices();
    const sel = root.getElementById("device");
    const sig = devices.map((d) => d.id + d.name).join("|");
    if (sig !== this._devSig) {
      this._devSig = sig;
      sel.innerHTML = `<option value="">${t.editor_none}</option>` +
        devices.map((d) => `<option value="${esc(d.id)}">${esc(d.name)}</option>`).join("");
    }
    sel.value = this._config.device || "";
    root.getElementById("hint").style.display = devices.length ? "none" : "block";
    root.getElementById("variant").value = VARIANTS.includes(this._config.variant) ? this._config.variant : "standard";
    const title = root.getElementById("title");
    if (root.activeElement !== title) title.value = this._config.title || "";
  }

  _emit(patch) {
    this._config = { ...this._config, ...patch };
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: this._config }, bubbles: true, composed: true,
    }));
  }
}

// ─── Registrierung ────────────────────────────────────────────────────────────

if (!customElements.get("roi-tracker-card")) {
  customElements.define("roi-tracker-card", RoiTrackerCard);
  customElements.define("roi-tracker-dialog", RoiTrackerDialog);
  customElements.define("roi-tracker-card-editor", RoiTrackerCardEditor);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "roi-tracker-card",
    name: "ROI Tracker Card",
    description: "PV-Ersparnis, Einspeiseertrag, Amortisation & Prognose – mit Detail-Popup.",
    preview: true,
    documentationURL: "https://github.com/pxljake/roi-tracker",
  });
  console.info(
    `%c ROI-TRACKER-CARD %c v${VERSION} `,
    "color:#fff;background:#2a78d6;font-weight:700;",
    "color:#2a78d6;background:#fff;font-weight:700;"
  );
}
