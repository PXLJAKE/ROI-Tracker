/**
 * ROI Tracker Card  v0.2.6
 *
 * Konfiguration:
 *   type: custom:roi-tracker-card
 *   device: <device_id>
 *   title: "Meine PV-Anlage"     # optional
 *   language: de | en            # optional, Standard: HA-Sprache
 *   show_chart: true             # Monatsbalken (Standard: true)
 *   show_breakdown: true         # Aufschlüsselung (Standard: true)
 *   show_energy: true            # kWh-Statistiken (Standard: true)
 */

const TXT = {
  de: {
    total_return: "Gesamtrückfluss",
    savings: "Ersparnis",
    battery_savings: "Batterie",
    revenue: "Einspeisung",
    remaining: "Offen",
    amortization: "Amortisiert",
    roi: "ROI",
    breakeven: "Break-Even",
    self_consumption: "Eigenverbrauch-%",
    daily: "Ø täglich",
    monthly: "Ø monatl.",
    yearly: "Prognose/Jahr",
    invested: "Investiert",
    chart_title: "Monatlicher Rückfluss",
    breakdown_title: "Rückfluss-Aufschlüsselung",
    energy_title: "Energie seit Start",
    grid_import: "Netzbezug",
    grid_cost: "Netzbezug-Kosten",
    consumption_kwh: "Eigenverbrauch",
    export_kwh: "Einspeisung",
    battery_kwh: "Batterie",
    no_data: "Noch keine Daten",
    no_device: "Bitte eine Anlage auswählen",
    pick_device: "Anlage",
    done: "amortisiert ✓",
    days: "Tagen",
    years: "Jahren",
    loading: "Lade Verlaufsdaten…",
  },
  en: {
    total_return: "Total return",
    savings: "Savings",
    battery_savings: "Battery",
    revenue: "Feed-in",
    remaining: "Remaining",
    amortization: "Amortized",
    roi: "ROI",
    breakeven: "Break-even",
    self_consumption: "Self-cons. %",
    daily: "Avg. daily",
    monthly: "Avg. monthly",
    yearly: "Est. yearly",
    invested: "Invested",
    chart_title: "Monthly return",
    breakdown_title: "Return breakdown",
    energy_title: "Energy since start",
    grid_import: "Grid import",
    grid_cost: "Grid import cost",
    consumption_kwh: "Self-consumption",
    export_kwh: "Feed-in",
    battery_kwh: "Battery",
    no_data: "No data yet",
    no_device: "Please select an asset",
    pick_device: "Asset",
    done: "paid off ✓",
    days: "days",
    years: "years",
    loading: "Loading history…",
  },
};

const KEYS = [
  "total_return", "savings", "battery_savings", "revenue",
  "remaining_investment", "amortization", "roi_percent",
  "breakeven_days", "self_sufficiency", "daily_average", "monthly_estimate",
  "grid_import_cost", "grid_import_kwh",
  "total_consumption_kwh", "total_export_kwh", "total_battery_discharge_kwh",
];

// ─── Hauptkarte ───────────────────────────────────────────────────────────────

class RoiTrackerCard extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
    this._statsCache = null;
    this._statsCacheTime = 0;
    this._statsFetching = false;
    this._root = null;
  }

  setConfig(config) { this._config = config || {}; }

  set hass(hass) {
    this._hass = hass;
    this._render();
    this._maybeRefreshStats();
  }

  getCardSize() { return 6; }

  static getConfigElement() {
    return document.createElement("roi-tracker-card-editor");
  }

  static getStubConfig() {
    return { type: "custom:roi-tracker-card", device: "" };
  }

  // ── Sprache ────────────────────────────────────────────────────────────────

  _lang() {
    const l = this._config.language || (this._hass && this._hass.language) || "de";
    return TXT[l] ? l : (l.startsWith("de") ? "de" : "en");
  }

  // ── Entitäten auflösen ────────────────────────────────────────────────────

  _resolveEntities() {
    const map = {};
    if (this._config.entities) {
      for (const k of KEYS) {
        if (this._config.entities[k]) map[k] = this._config.entities[k];
      }
    }
    const deviceId = this._config.device;
    if (deviceId && this._hass) {
      const entities = this._hass.entities || {};
      for (const [entityId, ent] of Object.entries(entities)) {
        if (ent.device_id !== deviceId || ent.platform !== "roi_tracker") continue;
        const uid = ent.unique_id || entityId;
        for (const k of KEYS) {
          if (uid.endsWith(k)) map[k] = entityId;
        }
      }
    }
    return map;
  }

  _value(entityId) {
    if (!entityId || !this._hass) return null;
    const s = this._hass.states[entityId];
    if (!s || s.state === "unknown" || s.state === "unavailable") return null;
    const n = parseFloat(s.state);
    return isNaN(n) ? null : n;
  }

  _attr(entityId, key) {
    if (!entityId || !this._hass) return null;
    const s = this._hass.states[entityId];
    return s && s.attributes ? (s.attributes[key] ?? null) : null;
  }

  // ── Formatierung ──────────────────────────────────────────────────────────

  _fmt(v, dec = 2) {
    if (v == null) return "–";
    const locale = this._lang() === "de" ? "de-DE" : "en-US";
    return new Intl.NumberFormat(locale, {
      style: "currency", currency: "EUR",
      minimumFractionDigits: dec, maximumFractionDigits: dec,
    }).format(v);
  }

  _fmtKwh(v) {
    if (v == null || v === 0) return null;
    const locale = this._lang() === "de" ? "de-DE" : "en-US";
    return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(v) + " kWh";
  }

  _fmtBreakeven(days, t) {
    if (days == null) return "–";
    if (days <= 0) return t.done;
    if (days > 730) return `${(days / 365).toFixed(1)} ${t.years}`;
    return `${Math.round(days)} ${t.days}`;
  }

  _fmtDate(isoDate) {
    if (!isoDate) return null;
    try {
      return new Date(isoDate).toLocaleDateString(
        this._lang() === "de" ? "de-DE" : "en-US"
      );
    } catch { return isoDate; }
  }

  // ── Statistics API ─────────────────────────────────────────────────────────

  _maybeRefreshStats() {
    const ent = this._resolveEntities();
    if (!ent.total_return) return;
    const now = Date.now();
    if (this._statsCache && now - this._statsCacheTime < 300_000) return;
    if (this._statsFetching) return;
    this._statsFetching = true;

    const start = new Date();
    start.setMonth(start.getMonth() - 12);
    start.setDate(1);
    start.setHours(0, 0, 0, 0);

    this._hass.callWS({
      type: "recorder/statistics_during_period",
      start_time: start.toISOString(),
      end_time: new Date().toISOString(),
      statistic_ids: [ent.total_return],
      period: "month",
      units: { currency: "EUR" },
      types: ["change"],
    }).then(result => {
      this._statsCache = (result && result[ent.total_return]) || [];
      this._statsCacheTime = Date.now();
      this._statsFetching = false;
      this._render();
    }).catch(() => {
      this._statsCache = [];
      this._statsFetching = false;
    });
  }

  // ── SVG-Donut ─────────────────────────────────────────────────────────────

  _renderDonut(pct) {
    const r = 38, cx = 50, cy = 50;
    const circ = 2 * Math.PI * r;
    const capped = Math.min(pct == null ? 0 : pct, 100);
    const filled = circ * capped / 100;
    const color = capped >= 100
      ? "var(--success-color, #4caf50)"
      : "var(--primary-color, #03a9f4)";
    const label = capped >= 100 ? "✓" : `${Math.round(capped)}%`;
    return `
      <svg viewBox="0 0 100 100" class="donut">
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
          stroke="var(--divider-color,#e0e0e0)" stroke-width="11"/>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
          stroke="${color}" stroke-width="11" stroke-linecap="round"
          stroke-dasharray="${filled} ${circ - filled}"
          stroke-dashoffset="${circ * 0.25}"
          style="transition:stroke-dasharray .7s ease;"/>
        <text x="50" y="46" text-anchor="middle" font-size="17" font-weight="700"
          fill="var(--primary-text-color)">${label}</text>
        <text x="50" y="60" text-anchor="middle" font-size="9"
          fill="var(--secondary-text-color)">${TXT[this._lang()].amortization}</text>
      </svg>`;
  }

  // ── Stacked Bar ───────────────────────────────────────────────────────────

  _renderStackedBar(savings, revenue, battery) {
    const t = TXT[this._lang()];
    const total = (savings || 0) + (revenue || 0) + (battery || 0);
    if (total <= 0) return "";
    const sp = ((savings || 0) / total * 100).toFixed(1);
    const rp = ((revenue || 0) / total * 100).toFixed(1);
    const bp = ((battery || 0) / total * 100).toFixed(1);
    const items = [
      savings > 0 ? `<span class="dot dot-blue"></span><span>${t.savings} ${this._fmt(savings, 0)}</span>` : "",
      revenue > 0 ? `<span class="dot dot-green"></span><span>${t.revenue} ${this._fmt(revenue, 0)}</span>` : "",
      battery > 0 ? `<span class="dot dot-orange"></span><span>${t.battery_savings} ${this._fmt(battery, 0)}</span>` : "",
    ].filter(Boolean).join("");
    return `
      <div class="section-title">${t.breakdown_title}</div>
      <div class="stack-bar">
        ${savings > 0 ? `<div class="stack-seg seg-blue" style="width:${sp}%"></div>` : ""}
        ${revenue > 0 ? `<div class="stack-seg seg-green" style="width:${rp}%"></div>` : ""}
        ${battery > 0 ? `<div class="stack-seg seg-orange" style="width:${bp}%"></div>` : ""}
      </div>
      <div class="stack-legend">${items}</div>`;
  }

  // ── Energie-Statistiken ───────────────────────────────────────────────────

  _renderEnergy(consumKwh, exportKwh, batteryKwh, gridKwh, gridCost) {
    const t = TXT[this._lang()];
    const rows = [
      [t.consumption_kwh, this._fmtKwh(consumKwh), "dot-blue"],
      [t.export_kwh, this._fmtKwh(exportKwh), "dot-green"],
      [t.battery_kwh, this._fmtKwh(batteryKwh), "dot-orange"],
      [t.grid_import, this._fmtKwh(gridKwh), "dot-grey"],
      gridCost > 0 ? [t.grid_cost, this._fmt(gridCost, 0), "dot-grey"] : null,
    ].filter(r => r && r[1]);

    if (!rows.length) return "";
    return `
      <div class="section-title">${t.energy_title}</div>
      <div class="energy-rows">
        ${rows.map(([label, val, dot]) =>
          `<div class="energy-row">
            <span class="dot ${dot}"></span>
            <span class="energy-lbl">${label}</span>
            <span class="energy-val">${val}</span>
          </div>`
        ).join("")}
      </div>`;
  }

  // ── Monatsbalken ──────────────────────────────────────────────────────────

  _renderMonthlyChart() {
    const t = TXT[this._lang()];
    const lang = this._lang();

    if (this._statsFetching && !this._statsCache) {
      return `<div class="section-title">${t.chart_title}</div>
              <div class="chart-msg">${t.loading}</div>`;
    }
    const data = this._statsCache;
    if (!data || !data.length) {
      return `<div class="section-title">${t.chart_title}</div>
              <div class="chart-msg">${t.no_data}</div>`;
    }

    const values = data.map(m => Math.max(0, m.change || 0));
    const maxVal = Math.max(...values, 0.01);
    const n = values.length;
    const barW = 18, gap = 4, chartH = 70;
    const totalW = n * (barW + gap) - gap;

    const bars = data.map((m, i) => {
      const h = Math.max(2, (values[i] / maxVal) * chartH);
      const x = i * (barW + gap);
      const mo = new Date(m.start).toLocaleDateString(
        lang === "de" ? "de-DE" : "en-US", { month: "short" }
      );
      return `<g>
        <rect x="${x}" y="${chartH - h}" width="${barW}" height="${h}" rx="3"
          fill="var(--primary-color,#03a9f4)" opacity="${i === n - 1 ? 1 : 0.65}"/>
        <text x="${x + barW / 2}" y="${chartH + 13}" text-anchor="middle"
          font-size="8" fill="var(--secondary-text-color)">${mo}</text>
      </g>`;
    }).join("");

    return `
      <div class="section-title">${t.chart_title}</div>
      <div class="chart-wrap">
        <svg viewBox="0 0 ${totalW} ${chartH + 18}"
          style="width:100%;height:90px;display:block;overflow:visible;">${bars}</svg>
      </div>`;
  }

  // ── Haupt-Render ──────────────────────────────────────────────────────────

  _render() {
    if (!this._hass) return;
    const t = TXT[this._lang()];
    const ent = this._resolveEntities();
    const title = this._config.title || "ROI Tracker";
    const showChart = this._config.show_chart !== false;
    const showBreakdown = this._config.show_breakdown !== false;
    const showEnergy = this._config.show_energy !== false;

    if (!this._config.device && (!this._config.entities || !Object.keys(ent).length)) {
      this._setHtml(`<ha-card header="${title}">
        <div class="empty">${t.no_device}</div></ha-card>`);
      return;
    }

    // Werte lesen
    const total = this._value(ent.total_return);
    const savings = this._value(ent.savings);
    const battery = this._value(ent.battery_savings);
    const revenue = this._value(ent.revenue);
    const remaining = this._value(ent.remaining_investment);
    const amort = this._value(ent.amortization);
    const roi = this._value(ent.roi_percent);
    const breakevenDays = this._value(ent.breakeven_days);
    const selfCons = this._value(ent.self_sufficiency);
    const daily = this._value(ent.daily_average);
    const monthly = this._value(ent.monthly_estimate);
    const gridCost = this._value(ent.grid_import_cost);
    const gridKwh = this._value(ent.grid_import_kwh);
    const consumKwh = this._value(ent.total_consumption_kwh);
    const exportKwh = this._value(ent.total_export_kwh);
    const battKwh = this._value(ent.total_battery_discharge_kwh);

    // Aus Attributes des total_return-Sensors
    const investment = this._attr(ent.total_return, "investment");
    const breakevenDate = this._attr(ent.total_return, "breakeven_date");
    const yearlyEst = this._attr(ent.total_return, "yearly_estimate");

    const pct = amort ?? 0;

    // Kacheln
    const tileData = [
      { label: t.daily, val: this._fmt(daily) },
      { label: t.monthly, val: this._fmt(monthly) },
      { label: t.yearly, val: this._fmt(yearlyEst) },
      { label: t.breakeven, val: this._fmtDate(breakevenDate) || this._fmtBreakeven(breakevenDays, t) },
      roi != null ? { label: t.roi, val: `${roi} %` } : null,
      selfCons != null ? { label: t.self_consumption, val: `${selfCons} %` } : null,
    ].filter(Boolean);

    const tiles = tileData.map(ti =>
      `<div class="tile">
        <div class="tile-val">${ti.val}</div>
        <div class="tile-lbl">${ti.label}</div>
      </div>`
    ).join("");

    const breakdownHtml = showBreakdown ? this._renderStackedBar(savings, revenue, battery) : "";
    const energyHtml = showEnergy ? this._renderEnergy(consumKwh, exportKwh, battKwh, gridKwh, gridCost) : "";
    const chartHtml = showChart ? this._renderMonthlyChart() : "";

    this._setHtml(`
      <ha-card>
        <div class="card-header">${title}</div>
        <div class="content">

          <div class="hero">
            ${this._renderDonut(pct)}
            <div class="hero-text">
              <div class="hero-total">${this._fmt(total)}</div>
              <div class="hero-label">${t.total_return}</div>
              <div class="hero-sub">
                <span>${t.invested}: ${this._fmt(investment, 0)}</span>
                ${remaining > 0 ? `<span class="hero-remain">▸ ${this._fmt(remaining, 0)} ${t.remaining}</span>` : ""}
              </div>
              <div class="amort-track"><div class="amort-fill" style="width:${Math.min(pct, 100)}%"></div></div>
            </div>
          </div>

          <div class="tiles">${tiles}</div>

          ${breakdownHtml ? `<div class="section">${breakdownHtml}</div>` : ""}
          ${energyHtml ? `<div class="section">${energyHtml}</div>` : ""}
          ${chartHtml ? `<div class="section">${chartHtml}</div>` : ""}

        </div>
      </ha-card>
    `);
  }

  _setHtml(inner) {
    if (!this._root) {
      this._root = this.attachShadow ? this.attachShadow({ mode: "open" }) : this;
    }
    this._root.innerHTML = `<style>
      :host{display:block}
      .card-header{padding:12px 16px 0;font-size:1.1em;font-weight:600;
        color:var(--ha-card-header-color,var(--primary-text-color))}
      .content{padding:8px 16px 16px}
      /* Hero */
      .hero{display:flex;align-items:center;gap:16px;margin-bottom:12px}
      .donut{width:90px;height:90px;flex-shrink:0}
      .hero-text{flex:1;min-width:0}
      .hero-total{font-size:1.9em;font-weight:700;color:var(--primary-color,#03a9f4);white-space:nowrap}
      .hero-label{font-size:.8em;color:var(--secondary-text-color);margin-bottom:2px}
      .hero-sub{font-size:.8em;color:var(--secondary-text-color);display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}
      .hero-remain{color:var(--warning-color,#ff9800)}
      .amort-track{height:6px;border-radius:3px;background:var(--divider-color,#e0e0e0);overflow:hidden}
      .amort-fill{height:100%;border-radius:3px;background:var(--primary-color,#03a9f4);transition:width .6s ease}
      /* Kacheln */
      .tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}
      .tile{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;padding:8px 6px;text-align:center}
      .tile-val{font-size:.95em;font-weight:600;color:var(--primary-text-color)}
      .tile-lbl{font-size:.72em;color:var(--secondary-text-color);margin-top:2px}
      /* Abschnitte */
      .section{margin-top:10px}
      .section-title{font-size:.78em;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
        color:var(--secondary-text-color);margin-bottom:6px}
      /* Stacked Bar */
      .stack-bar{height:12px;border-radius:6px;overflow:hidden;display:flex;gap:2px}
      .stack-seg{height:100%;transition:width .5s ease;border-radius:3px}
      .seg-blue{background:var(--primary-color,#03a9f4)}
      .seg-green{background:var(--success-color,#4caf50)}
      .seg-orange{background:#ff9800}
      .stack-legend{display:flex;gap:12px;flex-wrap:wrap;font-size:.78em;
        color:var(--secondary-text-color);margin-top:5px}
      .stack-legend span{display:flex;align-items:center;gap:4px}
      .dot{display:inline-block;width:8px;height:8px;border-radius:50%;flex-shrink:0}
      .dot-blue{background:var(--primary-color,#03a9f4)}
      .dot-green{background:var(--success-color,#4caf50)}
      .dot-orange{background:#ff9800}
      .dot-grey{background:var(--secondary-text-color,#9e9e9e)}
      /* Energie-Zeilen */
      .energy-rows{display:flex;flex-direction:column;gap:4px}
      .energy-row{display:flex;align-items:center;gap:6px;font-size:.85em}
      .energy-lbl{flex:1;color:var(--secondary-text-color)}
      .energy-val{font-weight:500;color:var(--primary-text-color)}
      /* Chart */
      .chart-wrap{width:100%;overflow-x:auto}
      .chart-msg{font-size:.82em;color:var(--secondary-text-color);padding:8px 0;text-align:center}
      /* Misc */
      .empty{padding:24px 16px;text-align:center;color:var(--secondary-text-color)}
    </style>${inner}`;
  }
}

// ─── Editor ───────────────────────────────────────────────────────────────────
// Bewusst reines HTML: keine Abhängigkeit von ha-selector/ha-textfield, die im
// Editor-Kontext nicht garantiert geladen sind. Geräte werden direkt aus
// hass.devices (identifiers) UND hass.entities (platform) ermittelt.

class RoiTrackerCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  /** Findet alle ROI-Tracker-Geräte: {id, name}. Robust über zwei Quellen. */
  _roiDevices() {
    const found = new Map();  // id -> name
    const hass = this._hass;
    if (!hass) return [];

    const devices = hass.devices || {};
    const entities = hass.entities || {};

    // Quelle 1: device-registry über identifiers [["roi_tracker", ...]]
    for (const [id, dev] of Object.entries(devices)) {
      const ids = dev && dev.identifiers ? dev.identifiers : [];
      const isRoi = ids.some((pair) => Array.isArray(pair) && pair[0] === "roi_tracker");
      if (isRoi) found.set(id, dev.name_by_user || dev.name || id);
    }

    // Quelle 2: entity-registry über platform === "roi_tracker"
    for (const ent of Object.values(entities)) {
      if (ent && ent.platform === "roi_tracker" && ent.device_id && !found.has(ent.device_id)) {
        const dev = devices[ent.device_id] || {};
        found.set(ent.device_id, dev.name_by_user || dev.name || ent.device_id);
      }
    }

    return [...found.entries()].map(([id, name]) => ({ id, name }));
  }

  _render() {
    try {
      this._renderInner();
    } catch (err) {
      // Editor darf niemals crashen – sonst "Configuration error"
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });
      this.shadowRoot.innerHTML =
        `<div style="padding:12px;color:var(--error-color,#db4437)">
           Editor-Fehler: ${err && err.message ? err.message : err}
         </div>`;
    }
  }

  _renderInner() {
    if (!this._hass) return;
    const lang = (this._hass.language || "de").startsWith("de") ? "de" : "en";
    const cfg = this._config || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const root = this.shadowRoot;

    const devices = this._roiDevices();
    const noDevices = lang === "de"
      ? "Keine ROI-Tracker-Anlage gefunden – zuerst die Integration einrichten."
      : "No ROI Tracker asset found – set up the integration first.";

    const options = [`<option value="">${lang === "de" ? "— Anlage wählen —" : "— Select asset —"}</option>`]
      .concat(devices.map((d) =>
        `<option value="${d.id}" ${cfg.device === d.id ? "selected" : ""}>${d.name}</option>`
      )).join("");

    const checked = (key) => (cfg[key] !== false ? "checked" : "");

    root.innerHTML = `
      <style>
        .form { display:flex; flex-direction:column; gap:14px; padding:8px; }
        .row label { display:block; font-size:.85em; color:var(--secondary-text-color); margin-bottom:4px; }
        select, input[type=text] {
          width:100%; padding:9px; box-sizing:border-box; font-size:1em;
          border:1px solid var(--divider-color,#ccc); border-radius:6px;
          background:var(--card-background-color,#fff); color:var(--primary-text-color);
        }
        .hint { font-size:.8em; color:var(--warning-color,#ff9800); margin-top:4px; }
        .row-check { display:flex; align-items:center; gap:10px; }
        .row-check input { width:18px; height:18px; }
        .row-check label { font-size:.9em; color:var(--primary-text-color); margin:0; }
      </style>
      <div class="form">
        <div class="row">
          <label>${lang === "de" ? "Anlage (ROI Tracker Gerät)" : "Asset (ROI Tracker device)"}</label>
          <select id="device">${options}</select>
          ${devices.length === 0 ? `<div class="hint">${noDevices}</div>` : ""}
        </div>
        <div class="row">
          <label>${lang === "de" ? "Titel (optional)" : "Title (optional)"}</label>
          <input id="title" type="text" value="${(cfg.title || "").replace(/"/g, "&quot;")}"
            placeholder="ROI Tracker"/>
        </div>
        <div class="row-check">
          <input id="chk-chart" type="checkbox" ${checked("show_chart")}/>
          <label for="chk-chart">${lang === "de" ? "Monatsbalken anzeigen" : "Show monthly chart"}</label>
        </div>
        <div class="row-check">
          <input id="chk-breakdown" type="checkbox" ${checked("show_breakdown")}/>
          <label for="chk-breakdown">${lang === "de" ? "Aufschlüsselung anzeigen" : "Show breakdown"}</label>
        </div>
        <div class="row-check">
          <input id="chk-energy" type="checkbox" ${checked("show_energy")}/>
          <label for="chk-energy">${lang === "de" ? "kWh-Statistiken anzeigen" : "Show energy stats"}</label>
        </div>
      </div>`;

    root.getElementById("device").addEventListener("change", (e) =>
      this._emit({ ...this._config, device: e.target.value }));
    root.getElementById("title").addEventListener("input", (e) =>
      this._emit({ ...this._config, title: e.target.value }));
    root.getElementById("chk-chart").addEventListener("change", (e) =>
      this._emit({ ...this._config, show_chart: e.target.checked }));
    root.getElementById("chk-breakdown").addEventListener("change", (e) =>
      this._emit({ ...this._config, show_breakdown: e.target.checked }));
    root.getElementById("chk-energy").addEventListener("change", (e) =>
      this._emit({ ...this._config, show_energy: e.target.checked }));
  }

  _emit(config) {
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config }, bubbles: true, composed: true,
    }));
  }
}

// ─── Registrierung ────────────────────────────────────────────────────────────

customElements.define("roi-tracker-card", RoiTrackerCard);
customElements.define("roi-tracker-card-editor", RoiTrackerCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "roi-tracker-card",
  name: "ROI Tracker Card",
  description: "PV-Amortisation, Ersparnis & Prognose mit Donut, Aufschlüsselung und Monatshistogramm.",
  preview: true,
  documentationURL: "https://github.com/pxljake/roi-tracker",
});

console.info(
  "%c ROI-TRACKER-CARD %c v0.2.6 ",
  "color:#fff;background:#03a9f4;font-weight:700;",
  "color:#03a9f4;background:#fff;font-weight:700;"
);
