# LEDFX Home Assistant Integration

Home Assistant custom integration for controlling [LEDFX](https://www.ledfx.app/) LED controllers.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

## Features

- 🎨 Full RGB color control
- 💡 Brightness adjustment (0-255)
- 🎵 Audio-reactive effects (energy, power, scroll, etc.)
- 🌈 Static effects (gradient, rainbow, fade, etc.)
- 🎨 8 pre-configured gradient presets (Rainbow, Fire, Ocean, Sunset, etc.)
- 🔌 Device online/offline status monitoring
- ⚡ Real-time state synchronization

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/YOUR-USERNAME/ledfx-homeassistant`
6. Select category: "Integration"
7. Click "Add"
8. Search for "LEDFX" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ledfx` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "LEDFX"
4. Enter your LEDFX server details:
   - **Host**: IP address of your LEDFX server (e.g., `192.168.1.100`)
   - **Port**: LEDFX port (default: `8888`)

## Entities

For each LEDFX virtual, the integration creates:

- **Light** (`light.ledfx_DEVICE`) - On/Off, brightness, RGB color control
- **Effect (Audio Reactive)** (`select.ledfx_DEVICE_effect_reactive`) - Audio-reactive effects like energy, power, scroll
- **Effect (Static)** (`select.ledfx_DEVICE_effect_static`) - Static effects like gradient, rainbow, fade
- **Gradient** (`select.ledfx_DEVICE_gradient`) - Pre-configured gradient presets

## Gradient Presets

The integration includes 8 beautiful gradient presets:

- 🌈 **Rainbow** - Classic rainbow spectrum
- 🔥 **Fire** - Red-orange-yellow fire effect
- 🌊 **Ocean** - Blue-turquoise-green ocean waves
- 🌅 **Sunset** - Orange-pink-purple sunset
- 💜 **Purple Dream** - Purple-pink dreamy colors
- 🌲 **Forest** - Various shades of green
- ❄️ **Ice** - Light blue to white icy colors
- 🌋 **Lava** - Dark red to orange lava flow

## Usage Examples

### Set a Static Effect with Color

```yaml
service: select.select_option
target:
  entity_id: select.ledfx_bedroom_effect_static
data:
  option: "rainbow"
```

### Apply a Gradient Preset

```yaml
service: select.select_option
target:
  entity_id: select.ledfx_bedroom_gradient
data:
  option: "Fire"
```

### Turn On with Audio-Reactive Effect

```yaml
service: light.turn_on
target:
  entity_id: light.ledfx_bedroom
data:
  brightness: 200

service: select.select_option
target:
  entity_id: select.ledfx_bedroom_effect_reactive
data:
  option: "energy"
```

## Automation Examples

### Party Mode on Doorbell

```yaml
automation:
  - alias: "Party Mode Doorbell"
    trigger:
      platform: state
      entity_id: binary_sensor.doorbell
      to: "on"
    action:
      - service: select.select_option
        target:
          entity_id: select.ledfx_living_room_effect_reactive
        data:
          option: "energy"
      - service: select.select_option
        target:
          entity_id: select.ledfx_living_room_gradient
        data:
          option: "Rainbow"
```

### Sunset Colors at Night

```yaml
automation:
  - alias: "Sunset LEDs"
    trigger:
      platform: sun
      event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.ledfx_bedroom
        data:
          brightness: 150
      - service: select.select_option
        target:
          entity_id: select.ledfx_bedroom_effect_static
        data:
          option: "gradient"
      - service: select.select_option
        target:
          entity_id: select.ledfx_bedroom_gradient
        data:
          option: "Sunset"
```

## Troubleshooting

### Integration doesn't load

- Check that LEDFX is running and accessible at the configured IP/port
- Verify the LEDFX API is enabled
- Check Home Assistant logs for error messages

### Effects not appearing

- Ensure your LEDFX installation has effects configured
- Try restarting the integration
- Check that virtuals are properly configured in LEDFX

### Device shows as unavailable

- Verify the physical LED device is online in LEDFX
- Check network connectivity between Home Assistant and LEDFX
- Restart both LEDFX and Home Assistant

## Requirements

- Home Assistant 2023.1 or newer
- LEDFX 2.0 or newer
- Python 3.11 or newer
- aiohttp 3.8.0 or newer

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/YOUR-USERNAME/ledfx-homeassistant/issues).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Developed for the Home Assistant community.
