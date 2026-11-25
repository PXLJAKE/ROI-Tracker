# ROI Tracker

**When has your PV system paid for itself?**

ROI Tracker is an integration for [Home Assistant](https://www.home-assistant.io/).
It calculates how much you **saved** by using your own solar power and **earned** by
feeding into the grid, with a fixed or dynamic electricity price (Tibber, aWATTar,
EPEX …), and shows amortization, ROI, monthly statistics and a projection to break-even.

!!! warning "Estimates"
    All values are **calculated estimates** based on your sensors and prices.
    They do not replace your energy bill or tax advice.

## Features

- **Savings**: every self-consumed kWh × electricity price *of that hour*
- **Feed-in revenue**: exported kWh × feed-in tariff
- **ROI & amortization**: total return vs. investment, remaining amount, break-even date
- **Monthly and yearly statistics** with daily values
- **Projection**: from 12 months of data, seasonally correct from actual returns
- **Retroactive** from commissioning, as far as Home Assistant has statistics
- **Dashboard card** in 4 sizes, one click opens a popup with all details
- User interface in **English and German**

## Three steps

1. [Install](installation.md) via HACS
2. [Set up a system](configuration.md): choose prices and energy sensors
3. Put the [card on a dashboard](usage.md#dashboard-card)

## More

- [How it is calculated](usage.md#how-it-is-calculated)
- [FAQ](faq.md)
- [Troubleshooting](troubleshooting.md)
- [Changes per version](changelog.md)
- Source code and issues on [GitHub](https://github.com/PXLJAKE/ROI-Tracker)
