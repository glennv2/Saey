Saey Pelletstove Integration for Home Assistant

Deze integratie voegt ondersteuning toe voor Saey pelletkachels (Duepi EVO controllers) via een ESP-Link, ideaal voor **UI Minimalist** of andere dashboards.

## Kenmerken
- **Climate Control**: Bediening van temperatuur, fan-modus en aan/uit.
- **Native Sensoren**: Losse entiteiten voor:
  - Rookgastemperatuur (`sensor.saey_rookgas`)
  - Ventilator RPM (`sensor.saey_rpm`)
  - Pellet Toevoer Snelheid (`sensor.saey_pellet`)
  - Status/Fase meldingen

## Installatie

### Via HACS
1. Open **HACS** in Home Assistant.
2. Ga naar **Integrations** en klik op de drie puntjes rechtsboven.
3. Kies **Custom repositories**.
4. Plak de URL van deze GitHub repo en kies categorie 'Integration'.
5. Klik op **Install**.
6. Herstart Home Assistant.

### Configuratie
Voeg het volgende toe aan je `configuration.yaml`:

```yaml
climate:
  - platform: saey_pellet
    name: Pelletstove
    host: 192.168.x.x  # Het IP van je Wemos/ESP-Link
    port: 23
    min_temp: 20
    max_temp: 30