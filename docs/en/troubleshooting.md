# Troubleshooting

## Error messages during setup

| Message | Cause | Solution |
|---|---|---|
| Please enter a price sensor or a fixed electricity price. | Both price fields are empty | Select a price sensor or enter a fixed price |
| This price sensor has no long-term statistics … Please enter a fixed price as a fallback. | Price sensor without `state_class` and start date older than 10 days | Enter a fixed price, e.g. your average energy price |
| This sensor has no long-term statistics (state_class missing) and cannot be used. | Energy sensor without `state_class` | Choose a cumulative kWh meter that also works in the energy dashboard |
| Each sensor may only be selected once. | Same sensor in two fields | Assign a separate sensor to each field |
| Please provide battery charged and battery discharged together (or leave both empty). | Only one of the two battery fields filled | Fill in both or leave both empty |
| Please select at least one sensor. | Required sensor missing | Fill in the required field, see [step 2](configuration.md#step-2-energy-sensors) |

## Dashboard card

### The card is missing from the card picker or shows an old version

The card is registered as a dashboard resource on startup, with the version in the URL
(`/roi_tracker/roi-tracker-card.js?v=…`). Duplicate or outdated entries are removed on startup.

1. Restart Home Assistant.
2. Reload the browser once with **Ctrl+F5**. In the companion app: *Settings → Companion app →
   Troubleshooting → Reset frontend cache*.
3. Check under **Settings → Dashboards → Resources** that the card is listed.

If the resource could not be registered, the Home Assistant log contains a warning
“Karte konnte nicht als Dashboard-Ressource eingetragen werden” (German log message).

### “The selected system no longer exists”

The system was deleted and added again and therefore has a new device ID. If there is exactly one
ROI Tracker system, the card uses it automatically. Otherwise select the system again in the card editor.

### “No ROI Tracker system found” in the card editor

No system has been set up yet. [Set up the integration](configuration.md) first.

### “No data yet”

Values appear as soon as Home Assistant has compiled the first hour of statistics.

## Values look wrong

- **Savings far too high or too low:** check calculation mode and sensors. A typical mix-up: export
  selected instead of grid import, or house consumption selected for “ready-made self-consumption”.
- **Battery counted twice:** with “ready-made self-consumption” only add “battery discharged” if the
  self-consumption sensor does not already include the battery.
- **Self-consumption slightly too high:** DC string meters instead of AC meters (see [FAQ](faq.md#ac-or-dc-meters-for-pv-production)).
- **Negative values before the first meter:** possible in versions before 0.5.1 if a meter was created
  after the start date. Update to 0.5.1 or newer.
- **Savings of 0 € in older periods with a dynamic price:** possible in versions before 0.5.0. Update and
  enter a fixed price as a fallback.
- **Price gaps:** if price data was missing for some hours, the detail popup shows a note with the number
  of hours under **Overview**. The last known price or the fixed price was used for them.

## Logs

!!! question "Open"
    ROI Tracker does not document its own procedure for logs yet. In Home Assistant in general:
    **Settings → System → Logs**; more detailed logging via `logger:` in `configuration.yaml`
    for `custom_components.roi_tracker`. This is a general Home Assistant hint, not verified for this project.

## Reporting bugs

Please open issues on [GitHub](https://github.com/PXLJAKE/ROI-Tracker/issues) with the versions of
ROI Tracker and Home Assistant, the calculation mode and the relevant log lines.
