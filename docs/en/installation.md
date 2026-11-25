# Installation

## Requirements

- **Home Assistant 2025.1** or newer
- **Recorder** enabled (ROI Tracker calculates from long-term statistics)
- [HACS](https://hacs.xyz/) for the recommended installation

## Via HACS (recommended)

ROI Tracker is part of the HACS default list:

1. Search for **ROI Tracker** in HACS.
2. Download **ROI Tracker** and restart Home Assistant.
3. **Settings → Devices & services → Add integration → ROI Tracker**.

[Open in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=PXLJAKE&repository=ROI-Tracker&category=integration){ .md-button }

### If ROI Tracker does not show up in HACS

Older HACS versions: HACS → **three-dot menu** → **Custom repositories**
→ URL `https://github.com/PXLJAKE/ROI-Tracker`, category **Integration**.
Then download and restart as above.

## Manual installation

!!! question "Open"
    Every release contains a file `roi_tracker.zip` with the contents of
    `custom_components/roi_tracker`. The project has no instructions for a manual
    installation yet, and none have been tested.

## After installation

- The **dashboard card** is registered as a dashboard resource automatically.
  If it does not appear in the card picker: reload the browser once with **Ctrl+F5**.
- Continue with the [configuration](configuration.md).

## Updating

Updates come through HACS. After each update restart Home Assistant and reload the
browser once with **Ctrl+F5** so the new card version is loaded.
Notes for individual versions are in the [changelog](changelog.md).
