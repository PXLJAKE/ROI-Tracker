/**
 * ROI Tracker Card
 * Eine konfigurierbare Lovelace-Karte zur Anzeige eines ROI-Rechners.
 *
 * Konfiguration (YAML oder grafischer Editor):
 *   type: custom:roi-tracker-card
 *   device: <device_id der Anlage>      # bevorzugt
 *   # ODER manuell einzelne Entitäten:
 *   entities:
 *     total_return: sensor.roi_..._gesamtrueckfluss
 *     amortization: sensor.roi_..._amortisation
 *     ...
 *   title: "Meine PV-Anlage"
 *   language: de | en                    # optional, Standard: HA-Sprache
 */

const TXT = {
  de: {
    total_return: "Gesamtrückfluss",
    savings: "Ersparnis",
    revenue: "Einspeiseertrag",
    remaining_investment: "Offener Restbetrag",
    amortization: "Amortisation",
    roi_percent: "ROI",
    breakeven_days: "Break-Even in",
    self_sufficiency: "Autarkiegrad",
    days: "Tagen",
    years: "Jahren",
    done: "amortisiert",
    no_device: "Bitte eine Anlage auswählen",
    pick_device: "Anlage",
  },
  en: {
    total_return: "Total return",
    savings: "Savings",
    revenue: "Feed-in revenue",
    remaining_investment: "Remaining",
    amortization: "Amortization",
    roi_percent: "ROI",
    breakeven_days: "Break-even in",
    self_sufficiency: "Self-sufficiency",
    days: "days",
    years: "years",
    done: "paid off",
    no_device: "Please select an asset",
    pick_device: "Asset",
  },
};

// Suffixe der von der Integration erzeugten unique_ids -> logische Schlüssel
const KEYS = [
  "total_return",
  "savings",
  "revenue",
  "remaining_investment",
  "amortization",
  "roi_percent",
  "breakeven_days",
  "self_sufficiency",
];

class RoiTrackerCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._lastEntityKey = null;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("roi-tracker-card-editor");
  }

  static getStubConfig() {
    return { type: "custom:roi-tracker-card", device: "" };
  }

  _lang() {
    const l = this._config.language || (this._hass && this._hass.language) || "de";
    return TXT[l] ? l : "en";
  }

  /** Findet alle ROI-Sensoren des konfigurierten Geräts und mappt sie auf Schlüssel. */
  _resolveEntities() {
    const map = {};
    // 1) Explizit angegebene Entitäten haben Vorrang.
    if (this._config.entities) {
      for (const k of KEYS) {
        if (this._config.entities[k]) map[k] = this._config.entities[k];
      }
    }
    // 2) Über Gerät auflösen (via entity registry im hass-Objekt).
    const deviceId = this._config.device;
    if (deviceId && this._hass) {
      const entities = this._hass.entities || {};
      for (const [entityId, ent] of Object.entries(entities)) {
        if (ent.device_id !== deviceId) continue;
        if (ent.platform !== "roi_tracker") continue;
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
    return isNaN(n) ? s.state : n;
  }

  _fmtMoney(v) {
    if (v == null) return "–";
    const l = this._lang() === "de" ? "de-DE" : "en-US";
    return new Intl.NumberFormat(l, { style: "currency", currency: "EUR" }).format(v);
  }

  _fmtBreakeven(days, t) {
    if (days == null) return "–";
    if (days <= 0) return t.done;
    if (days > 365) return `${(days / 365).toFixed(1)} ${t.years}`;
    return `${Math.round(days)} ${t.days}`;
  }

  _render() {
    if (!this._hass) return;
    const t = TXT[this._lang()];
    const ent = this._resolveEntities();
    const title = this._config.title || "ROI Tracker";

    if (!this._config.device && (!this._config.entities || !Object.keys(ent).length)) {
      this._html(`<ha-card header="${title}"><div class="empty">${t.no_device}</div></ha-card>`);
      return;
    }

    const total = this._value(ent.total_return);
    const savings = this._value(ent.savings);
    const revenue = this._value(ent.revenue);
    const remaining = this._value(ent.remaining_investment);
    const amort = this._value(ent.amortization);
    const roi = this._value(ent.roi_percent);
    const breakeven = this._value(ent.breakeven_days);
    const selfSuff = this._value(ent.self_sufficiency);

    const pct = Math.max(0, Math.min(100, amort == null ? 0 : amort));
    const barColor =
      pct >= 100 ? "var(--success-color, #4caf50)" : "var(--primary-color, #03a9f4)";

    const rows = [];
    const addRow = (label, val) => {
      if (val === null || val === undefined) return;
      rows.push(
        `<div class="row"><span class="lbl">${label}</span><span class="val">${val}</span></div>`
      );
    };
    addRow(t.savings, this._fmtMoney(savings));
    if (revenue != null && revenue !== 0) addRow(t.revenue, this._fmtMoney(revenue));
    addRow(t.remaining_investment, this._fmtMoney(remaining));
    addRow(t.breakeven_days, this._fmtBreakeven(breakeven, t));
    if (roi != null) addRow(t.roi_percent, `${roi} %`);
    if (selfSuff != null) addRow(t.self_sufficiency, `${selfSuff} %`);

    this._html(`
      <ha-card header="${title}">
        <div class="content">
          <div class="hero">
            <div class="hero-value">${this._fmtMoney(total)}</div>
            <div class="hero-label">${t.total_return}</div>
          </div>
          <div class="bar-wrap">
            <div class="bar-track">
              <div class="bar-fill" style="width:${pct}%;background:${barColor}"></div>
            </div>
            <div class="bar-label">${t.amortization}: ${amort == null ? "–" : amort + " %"}</div>
          </div>
          <div class="rows">${rows.join("")}</div>
        </div>
      </ha-card>
    `);
  }

  _html(inner) {
    if (!this._root) {
      this._root = this.attachShadow ? this.attachShadow({ mode: "open" }) : this;
    }
    this._root.innerHTML = `
      <style>
        .content { padding: 8px 16px 16px; }
        .hero { text-align: center; margin: 8px 0 16px; }
        .hero-value { font-size: 2.4em; font-weight: 600; color: var(--primary-text-color); }
        .hero-label { font-size: 0.9em; color: var(--secondary-text-color); }
        .bar-wrap { margin: 8px 0 16px; }
        .bar-track { height: 14px; border-radius: 7px; background: var(--divider-color, #e0e0e0); overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 7px; transition: width .6s ease; }
        .bar-label { font-size: 0.85em; color: var(--secondary-text-color); margin-top: 6px; text-align: center; }
        .rows { display: flex; flex-direction: column; gap: 6px; }
        .row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--divider-color, #eee); }
        .row:last-child { border-bottom: none; }
        .lbl { color: var(--secondary-text-color); }
        .val { font-weight: 500; color: var(--primary-text-color); }
        .empty { padding: 24px 16px; text-align: center; color: var(--secondary-text-color); }
      </style>
      ${inner}
    `;
  }
}

class RoiTrackerCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;
    const lang = (this._hass.language || "de").startsWith("de") ? "de" : "en";
    const t = TXT[lang];

    // Geräte der Integration roi_tracker sammeln.
    const devices = this._hass.devices || {};
    const entities = this._hass.entities || {};
    const roiDeviceIds = new Set();
    for (const ent of Object.values(entities)) {
      if (ent.platform === "roi_tracker" && ent.device_id) roiDeviceIds.add(ent.device_id);
    }

    if (!this._root) this._root = this.attachShadow({ mode: "open" });

    const options = [...roiDeviceIds]
      .map((id) => {
        const d = devices[id] || {};
        const name = d.name_by_user || d.name || id;
        const sel = this._config.device === id ? "selected" : "";
        return `<option value="${id}" ${sel}>${name}</option>`;
      })
      .join("");

    this._root.innerHTML = `
      <style>
        .form { padding: 8px; display: flex; flex-direction: column; gap: 12px; }
        label { font-size: 0.85em; color: var(--secondary-text-color); display:block; margin-bottom:4px; }
        select, input { width: 100%; padding: 8px; box-sizing: border-box;
          border:1px solid var(--divider-color,#ccc); border-radius:6px;
          background: var(--card-background-color); color: var(--primary-text-color); }
      </style>
      <div class="form">
        <div>
          <label>${t.pick_device}</label>
          <select id="device">
            <option value="">— ${t.no_device} —</option>
            ${options}
          </select>
        </div>
        <div>
          <label>Titel / Title</label>
          <input id="title" type="text" value="${this._config.title || ""}" />
        </div>
      </div>
    `;

    this._root.getElementById("device").addEventListener("change", (e) => {
      this._emit({ ...this._config, device: e.target.value });
    });
    this._root.getElementById("title").addEventListener("input", (e) => {
      this._emit({ ...this._config, title: e.target.value });
    });
  }

  _emit(config) {
    this._config = config;
    this.dispatchEvent(
      new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true })
    );
  }
}

customElements.define("roi-tracker-card", RoiTrackerCard);
customElements.define("roi-tracker-card-editor", RoiTrackerCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "roi-tracker-card",
  name: "ROI Tracker Card",
  description: "Zeigt Amortisation, Ersparnis und ROI einer ROI-Tracker-Anlage / Shows amortization, savings and ROI of a ROI Tracker asset.",
  preview: true,
  documentationURL: "https://github.com/pxljake/roi-tracker",
});

console.info(
  "%c ROI-TRACKER-CARD %c v0.1.0 ",
  "color:#fff;background:#03a9f4;font-weight:700;",
  "color:#03a9f4;background:#fff;font-weight:700;"
);
