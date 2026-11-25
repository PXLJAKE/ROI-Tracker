# Configuration

A system is added under **Settings → Devices & services → Add integration →
ROI Tracker** in two steps. You can add several systems; each gets its own device
with its own sensors.

## Step 1: Basic data

| Field | Required | Meaning |
|---|---|---|
| Name | yes | Name of the system (default: “PV-Anlage”) |
| Investment | yes | Total cost of the system in € that should pay for itself |
| Commissioning / start date | yes | Calculation starts on this day, also in the past, as far as HA has statistics |
| How is self-consumption determined? | yes | The [calculation mode](#calculation-mode), decides the sensors in step 2 |
| Dynamic electricity price (sensor) | one of both | Price sensor, e.g. Tibber, aWATTar, EPEX. `sensor` and `input_number` entities are allowed |
| Fixed electricity price (€/kWh) | one of both | Your energy price, e.g. `0.32`. With a price sensor it is only used for times without price data |
| Feed-in tariff (€/kWh) | yes | E.g. `0.082` for 8.2 ct/kWh, `0` if you get no tariff |

### Calculation mode

The calculation mode decides how the **self-consumed kWh** are determined per hour:

| Mode | Formula per hour | When to use |
|---|---|---|
| **House consumption − grid import** *(recommended)* | house consumption − grid import | You have a sensor for the total house consumption |
| **PV production − export** | PV − export + battery discharge − battery charge | You have the sensors from the energy dashboard |
| **Ready-made self-consumption** | self-consumption (+ battery discharge) | Your inverter reports self-consumption directly |

With “house consumption − grid import” a battery is automatically included correctly.

### Electricity price

- **Unit:** €/kWh, ct/kWh or €/MWh is detected automatically from the sensor's unit.
- **With long-term statistics** (`state_class: measurement`): the retroactive calculation is exact per hour.
- **Without long-term statistics** (e.g. `sensor.tibber_current_price`): the price is read from the
  state history (default: the last 10 days). If the start date is more than 10 days ago, setup
  therefore requires a **fixed price as a fallback**.
- **Gaps in price data:** an hour without a price uses the last known price. Before the first known
  price, at most **6 hours** are back-filled; before that the fixed price applies. Without a fixed
  price the first known price is used.

## Step 2: Energy sensors

All energy sensors must be **cumulative kWh meters with long-term statistics**
(`device_class: energy` and a `state_class`), exactly the sensors that also work in the
energy dashboard. Each sensor may only be selected once.

=== "House consumption − grid import"

    | Sensor | Required | Note |
    |---|---|---|
    | Total house consumption (kWh) | yes | Total power consumption of the house, whether from PV, battery or grid |
    | Grid import (kWh) | yes | Import meter, **not** the export. Energy dashboard: Electricity grid → Grid consumption |
    | Grid export (kWh) | no | Export meter, needed for feed-in revenue. Energy dashboard: Electricity grid → Return to grid |

=== "PV production − export"

    | Sensor | Required | Note |
    |---|---|---|
    | PV production (kWh) | yes | One or more meters; several strings or inverters are added up |
    | Grid export (kWh) | yes | Export meter |
    | Battery charged (kWh) | no | Only together with “Battery discharged” |
    | Battery discharged (kWh) | no | Only together with “Battery charged” |

    **AC meters** of the inverter are the most accurate. DC string meters still contain the
    conversion losses (typically 3–5 % too much self-consumption).

=== "Ready-made self-consumption"

    | Sensor | Required | Note |
    |---|---|---|
    | PV self-consumption (kWh) | yes | Directly used PV power, **not** house consumption and **not** grid import |
    | Battery discharged (kWh) | no | Only if the self-consumption sensor does **not** already include the battery |
    | Grid export (kWh) | no | Export meter, needed for feed-in revenue |

## Changing settings later

All settings can be changed under **Settings → Devices & services → ROI Tracker →
Configure**. Changing the start date, calculation mode, sensors or prices automatically triggers
a **full recalculation** from the start date. Changing the investment only changes ROI,
amortization and projection; daily values stay.

Setup problems: see [Troubleshooting](troubleshooting.md#error-messages-during-setup).
