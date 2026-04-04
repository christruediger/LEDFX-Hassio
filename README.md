# LEDFX Home Assistant Integration

Home Assistant custom integration for controlling [LedFX](https://www.ledfx.app/) LED controllers.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/badge/version-1.1.0-blue)
![HA](https://img.shields.io/badge/Home%20Assistant-2023.1+-green)

## Features

- **RGB Color Control** — Pick any color in Home Assistant; LedFX uses it as the dominant color for every effect
- **Color Lock** — Your chosen color stays locked across effect changes. Switch from `energy` to `wavelength` and Magenta stays Magenta
- **Audio-reactive effects** — energy, power, scroll, blade_power_plus, and more
- **Static effects** — gradient, rainbow, fade, and more
- **8 gradient presets** — Rainbow, Fire, Ocean, Sunset, Purple Dream, Forest, Ice, Lava
- **Effect parameter sliders** — Control speed, blur, and intensity per virtual
- **Brightness control** — Per-virtual brightness slider (maps to LedFX `max_brightness`)
- **Auto-filter** — Background/foreground/mask virtuals are hidden automatically
- **Device status** — Online/offline monitoring
- **Fast sync** — 5-second polling keeps HA and LedFX in sync

---

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots → **Custom repositories**
4. Add the repository URL and select category **Integration**
5. Search for **LEDFX** and click Download
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/ledfx` folder into your Home Assistant `custom_components` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **LEDFX**
4. Enter your LedFX server details:
   - **Host**: IP address of your LedFX server (e.g. `192.168.1.100`)
   - **Port**: LedFX port (default: `8888`)

---

## Entities

For each LedFX virtual the integration creates the following entities:

| Entity | Type | Description |
|---|---|---|
| `light.ledfx_DEVICE_licht` | Light | RGB color picker + brightness + on/off |
| `switch.ledfx_DEVICE` | Switch | Simple on/off |
| `select.ledfx_DEVICE_effect_reactive` | Select | Audio-reactive effect selection |
| `select.ledfx_DEVICE_effect_static` | Select | Static effect selection |
| `select.ledfx_DEVICE_gradient` | Select | Gradient preset selection |
| `number.ledfx_DEVICE_max_brightness` | Number | Virtual brightness (0–1) |
| `number.ledfx_DEVICE_speed` | Number | Effect speed (where supported) |
| `number.ledfx_DEVICE_blur` | Number | Effect blur amount (where supported) |
| `number.ledfx_DEVICE_intensity` | Number | Effect brightness/intensity (where supported) |

> Background, foreground and mask virtuals are automatically excluded.

---

## Color Lock

The **Color Lock** is the core feature of v1.1. It lets you define a dominant color for a virtual that persists no matter what effect is active.

**How it works:**

1. Set a color via the `light` entity (e.g. Magenta)
2. The color is stored internally as a lock for that virtual
3. Every time you change the active effect, the locked color is automatically applied:
   - Effects with a `gradient` parameter → monochromatic gradient in your color
   - Effects with per-band colors (`color_high`, `color_lows`, `color_mids`, …) → variations of your color across the frequency bands
   - Effects with a single `color` parameter → your exact color

**Releasing the lock:**

Manually selecting a **Gradient preset** from the gradient selector clears the color lock for that virtual and hands back full gradient control.

### Example: Keep the whole room in Magenta

```yaml
service: light.turn_on
target:
  entity_id: light.ledfx_wohnzimmer_licht
data:
  rgb_color: [255, 0, 200]
```

From now on, switching between energy, wavelength, scroll, fade — everything stays Magenta-toned until you explicitly change it.

---

## Gradient Presets

| Name | Description |
|---|---|
| Rainbow | Classic full-spectrum rainbow |
| Fire | Red → orange → yellow |
| Ocean | Deep blue → turquoise → green |
| Sunset | Orange → pink → purple |
| Purple Dream | Indigo → violet → pink |
| Forest | Dark green → light green |
| Ice | Light blue → white |
| Lava | Dark red → orange |

---

## Automation Examples

### Magenta party mode on doorbell

```yaml
automation:
  - alias: "Party Mode Doorbell"
    trigger:
      platform: state
      entity_id: binary_sensor.doorbell
      to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.ledfx_wohnzimmer_licht
        data:
          rgb_color: [255, 0, 200]
      - service: select.select_option
        target:
          entity_id: select.ledfx_wohnzimmer_effect_reactive
        data:
          option: "energy"
```

### Sunset scene at dusk

```yaml
automation:
  - alias: "Sunset LEDs"
    trigger:
      platform: sun
      event: sunset
    action:
      - service: select.select_option
        target:
          entity_id: select.ledfx_wohnzimmer_gradient
        data:
          option: "Sunset"
      - service: select.select_option
        target:
          entity_id: select.ledfx_wohnzimmer_effect_static
        data:
          option: "gradient"
```

### Adjust speed for an effect

```yaml
service: number.set_value
target:
  entity_id: number.ledfx_wohnzimmer_speed
data:
  value: 3.5
```

---

## Effect Parameter Sliders

The sliders (speed, blur, intensity) are **always visible** regardless of the active effect. Whether a slider actually does anything depends on the active effect:

- Each entity exposes a `supported_by_current_effect` attribute — check it in Developer Tools if a slider seems to have no effect
- Applying a slider to an effect that doesn't support it is harmlessly ignored

---

## Troubleshooting

**Integration doesn't load**
- Confirm LedFX is running and reachable at the configured host/port
- Check Home Assistant logs (`Settings → System → Logs`) for errors

**Effects list is empty**
- Restart the integration to re-fetch the schema from LedFX
- Confirm your LedFX version is 2.0 or newer

**Color lock not working**
- Make sure the color was set via the `light` entity, not via the gradient selector
- The gradient selector explicitly clears the color lock

**Slider has no effect**
- Check the `supported_by_current_effect` attribute on the number entity
- Switch to an effect that supports the parameter (e.g. `gradient` or `scroll` for speed)

**Device shows as unavailable**
- Verify the physical device is online in LedFX
- Check network connectivity between Home Assistant and LedFX

---

## Requirements

- Home Assistant 2023.1 or newer
- LedFX 2.0 or newer
- Python 3.11 or newer
- aiohttp 3.8.0 or newer

---

## Changelog

### v1.1.0
- **New:** `light` entity with RGB color picker and brightness control per virtual
- **New:** Color Lock — chosen color persists automatically across effect changes
- **New:** Number sliders for speed, blur, and intensity
- **New:** Effects schema cached at startup — faster load, fewer API calls
- **Improved:** Sync interval reduced from 30s to 5s
- **Improved:** Number sliders always available (no more confusing "unavailable" state)
- **Fixed:** Default config extraction when switching effects

### v1.0.0
- Initial release: switch, effect select, gradient select

---

## License

MIT License — see [LICENSE](LICENSE) for details.

## Credits

Developed for the Home Assistant community by [christruediger](https://github.com/christruediger).
