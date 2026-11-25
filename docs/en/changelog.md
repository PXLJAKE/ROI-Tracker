# Changelog

All versions with downloads are listed under
[GitHub Releases](https://github.com/PXLJAKE/ROI-Tracker/releases). The release notes are written
in German; this page is a translation. After every update restart Home Assistant and reload the
browser once with **Ctrl+F5**.

## v0.5.1 (2026-11-22)

**Correct values before the first PV meter and with price gaps** ([release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.5.1))

- **No more negative self-consumption** if the production or consumption meter was created after the
  start date. For hours without a statistics row of that meter only the export is credited; export and
  battery are no longer subtracted from the (missing) self-consumption.
- **Fixed price takes precedence over long back-filling:** if the price history starts later, the first
  known price used to be spread back over up to 31 days. Now at most 6 hours are back-filled; before
  that the configured fixed price applies.
- Every system is recalculated once automatically after the update.

## v0.5.0 (2026-11-22)

**Several PV strings, safe prices for dynamic tariffs, more robust card** ([release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.5.0))

- **New:** several PV production meters (strings/inverters) with “PV production − export”; they are
  added up. A sum helper is no longer needed.
- **Dynamic price without long-term statistics** (e.g. `sensor.tibber_current_price`): if the start
  date is more than 10 days ago, setup requires a fixed price as a fallback. Previously savings were
  calculated as 0 € for hours without price history.
- **Card:** after deleting and re-adding the system, the card automatically uses the only existing
  system, otherwise it shows a clear hint.
- **Dashboard resource:** duplicate card entries are removed on startup.
- **Docs:** installation via HACS search first; note on DC vs. AC meters.

## v0.4.1 (2026-09-29)

**Dashboard card is registered reliably again** ([release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.4.1))

- The card was not registered as a dashboard resource on current Home Assistant versions. It is now
  registered automatically under *Settings → Dashboards → Resources*; a manually added entry is
  updated to the new version.
- Clearer help texts: **grid import** = import meter, **export** = export meter.
- Problems registering the card are logged as a warning.

## v0.4.0 (2026-09-26)

**Rewrite: hourly from HA statistics, monthly statistics and detail popup** ([release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.4.0))

Fixed calculation errors:

- A short sensor drop (e.g. 0 after a restart) counted the whole meter reading again; daily resets were
  sometimes counted twice.
- Battery discharge was counted twice if the consumption sensor already included it; grid import was
  never subtracted.
- The retroactive calculation valued everything at the current price; price sensors without statistics
  aborted it.
- Changed settings never applied retroactively; the monthly chart stayed empty; the projection was
  seasonally biased; the price unit was ignored.

New:

- 3 calculation modes, hourly dynamic prices, retroactive monthly/yearly/daily statistics, projection
  from 12 months based on the last 365 days, automatic recalculation, card in 4 sizes with detail popup.

### Upgrading from 0.3.x

On first start the existing system is migrated automatically (mode “ready-made self-consumption”) and
recalculated. Please check afterwards:

- **Calculation mode:** is your consumption sensor actually the *house consumption*? Then switch to
  “house consumption − grid import”.
- **Price:** the “ready-made € sensor” mode is gone; enter a price sensor or a fixed price.
- The “sensors reset daily” switch is gone (handled automatically).
- The service `roi_tracker.reset` is gone; use `roi_tracker.recalculate`.
- Sensors no longer needed are removed (16 → 10); total return, savings, feed-in revenue, remaining
  amount, amortization and ROI keep their entity IDs.
- Card: the old `show_*`/`tile_*` options are ignored; choose a `variant` instead.
- Minimum version: Home Assistant 2025.1.

## Older versions

| Version | Date | Title |
|---|---|---|
| [v0.3.3](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.3) | 2026-06-13 | “Today” section shows values reliably |
| [v0.3.2](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.2) | 2026-06-13 | Energy rows and top block can be hidden individually |
| [v0.3.1](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.1) | 2026-06-13 | Fix: “today” section |
| [v0.3.0](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.0) | 2026-06-13 | First stable release |

Pre-releases 0.2.x (May/June 2026) are listed on
[GitHub Releases](https://github.com/PXLJAKE/ROI-Tracker/releases).
