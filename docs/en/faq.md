# FAQ

## Which calculation mode should I use?

If you have a sensor for the **total house consumption**: “house consumption − grid import”.
A battery is then included correctly automatically. If you only have the energy dashboard
sensors (PV production, export, battery), use “PV production − export”.
Details: [calculation mode](configuration.md#calculation-mode).

## I have several PV strings or inverters. Do I need a sum helper?

No. With “PV production − export” you can select several production meters; they are added
up (since v0.5.0).

## AC or DC meters for PV production?

AC meters of the inverter are the most accurate. DC string meters still contain the conversion
losses, so self-consumption is typically 3–5 % too high.

## Does it work with Tibber, aWATTar or EPEX?

Yes. Select the price sensor as “Dynamic electricity price”. The unit (€/kWh, ct/kWh, €/MWh)
is detected automatically. If the sensor has no long-term statistics (e.g.
`sensor.tibber_current_price`), hourly prices are only available for roughly the last 10 days.
For older periods you enter a fixed price as a fallback; with a start date older than 10 days,
setup requires it.

## Why is self-consumption of an hour sometimes negative?

That is intended, e.g. when the battery is charged from the grid at a cheap dynamic price. It is
credited back when the battery discharges later at a higher price, so savings reflect the actual
price difference.

## How far back can ROI Tracker calculate?

As far as Home Assistant has long-term statistics for your energy sensors. Hours before a meter's
first statistics entry are not valued; projection and average start on the first day with data.

## Why is the yearly estimate “provisional”?

With less than 12 months of data the daily average × 365 is projected. Starting in summer this is
too optimistic, in winter too pessimistic. From 12 months on, the actual sum of the last 365 days
is used.

## Do I need to recalculate after a change?

No. Changing start date, calculation mode, sensors or prices triggers a full recalculation
automatically. Manually: [`roi_tracker.recalculate`](usage.md#recalculate).

## Does this replace my electricity bill?

No. All values are calculated estimates from your sensors and prices, without standing charges,
taxes or your supplier's billing details.
