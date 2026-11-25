# Usage

## How it is calculated

The basis is **Home Assistant's long-term statistics**, the same data as in the
energy dashboard. For every hour:

```text
Savings      = self-consumed kWh × electricity price of that hour
Feed-in      = exported kWh      × feed-in tariff

Total return = Σ savings + Σ feed-in
Amortization = total return / investment
ROI          = (total return − investment) / investment
```

How the self-consumed kWh are determined depends on the
[calculation mode](configuration.md#calculation-mode).

Why hourly from statistics?

- **Dynamic prices** are valued correctly: midday kWh at the midday price, evening kWh at the evening price.
- **Charging the battery from the grid** (cheap hours) and discharging it (expensive hours) is correctly
  counted as savings. Self-consumption of a single hour may be negative.
- **Counter resets, daily counters, outages and restarts** are already handled by HA statistics,
  nothing is counted twice.
- If you change start date, sensors or prices, **everything is recalculated automatically**.

### Updates

ROI Tracker updates every **5 minutes**. Fully compiled hours are valued and stored as daily
values; the current hour is estimated from the 5-minute statistics and only displayed, not stored.

### Projection and break-even

- **From 12 months of data:** yearly estimate = sum of the last 365 days. Summer and winter
  balance out.
- **Before that:** daily average × 365. Marked as *provisional* in the card.
- Counting starts on the **first day with data**, not on the configured start date. If HA statistics
  do not reach back that far, the average would otherwise be too low.
- **Break-even date:** today + remaining amount ÷ daily average. If the system has already paid
  for itself, the day the total return reached the investment.

## Sensors per system

| Sensor | Unit | Description |
|---|---|---|
| Total return | € | Savings + feed-in revenue |
| Savings | € | Avoided electricity costs through self-consumption |
| Feed-in revenue | € | Tariff for exported power (only with an export sensor) |
| Remaining amount | € | Amount not yet paid back |
| Amortization | % | Share of the investment already returned |
| ROI | % | Profit/loss relative to the investment |
| Yearly estimate | € | Expected return per year |
| Break-even date | date | Expected (or actual) payback date |
| Total self-consumption | kWh | Self-consumed energy since start |
| Total export | kWh | Exported energy since start (only with an export sensor) |

The currency of the € sensors is the currency configured in Home Assistant.

The **Total return** sensor also has these attributes:

| Attribute | Meaning |
|---|---|
| `investment` | Investment |
| `data_since` | First day with data |
| `daily_average` | Return per day according to the projection |
| `month_total` | Return in the current month |
| `month_forecast` | Forecast for the current month |
| `today_total` | Return today |
| `avg_price` | Average electricity price of the self-consumed kWh |
| `years_to_breakeven` | Years until break-even |
| `projection_provisional` | `true` while there are less than 12 months of data |

## Dashboard card

The card is registered automatically. Choose system and layout in the card editor:

| Variant | Content |
|---|---|
| `mini` | One line: total return + amortization bar |
| `compact` | Donut, total return, savings / feed-in |
| `standard` | Additionally: this month, yearly estimate, break-even, ROI |
| `full` | Additionally: bar chart of the last 12 months |

```yaml
type: custom:roi-tracker-card
device: <device ID of the system>
variant: standard   # mini | compact | standard | full
title: PV system    # optional
language: en        # optional: de or en, default is the Home Assistant language
```

**Clicking the card opens the detail popup:**

- **Overview**: all key figures, kWh, average electricity price, price source
- **Months**: bar chart and table per year, yearly overview; clicking a month shows the daily values
- **Forecast**: cumulative return vs. investment with projection to break-even

The card reloads its data every 5 minutes.

## Recalculate

Normally not needed: changed settings trigger a recalculation automatically.
Manually with the action `roi_tracker.recalculate`:

```yaml
action: roi_tracker.recalculate
target:
  entity_id: sensor.<system>_total_return
data:
  start_date: "2025-01-01"   # optional, saved in the system
```

## Deleting a system

When a system is deleted under **Devices & services**, its stored daily values are removed as well.
