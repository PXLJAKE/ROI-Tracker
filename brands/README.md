# Brand-Assets

Seit Home Assistant 2026.3 liefern Custom Integrations ihre Icons selbst aus –
das zentrale [home-assistant/brands](https://github.com/home-assistant/brands)-Repository
nimmt für Custom Integrations keine Icons mehr an
([Ankündigung](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api)).

Die Icons liegen deshalb direkt in der Integration:

```
custom_components/roi_tracker/brand/icon.png      (256×256, transparent)
custom_components/roi_tracker/brand/icon@2x.png   (512×512, transparent)
```

Neu erzeugen: `python scripts/generate_icon.py`
