# LEDFX Home Assistant Integration - Development Handoff

## Project Overview
Custom Home Assistant integration for controlling LEDFX LED controllers via their REST API.

## Current Status
**Version:** 1.0.0  
**Status:** Working, ready for GitHub publication  
**Last Updated:** 2025-04-04

## Architecture

### Components
1. **Switch Platform** (`switch.py`) - Simple On/Off control for virtuals
2. **Select Platform** (`select.py`) - Three selects per virtual:
   - Audio-reactive effects (energy, power, scroll, etc.)
   - Static effects (gradient, rainbow, fade, etc.)
   - Gradient presets (8 predefined color gradients)
3. **Config Flow** (`config_flow.py`) - UI-based setup (host + port)
4. **API Client** (`ledfx_client.py`) - Async REST client for LEDFX API
5. **Coordinator** - DataUpdateCoordinator with 30s polling interval

### File Structure
```
custom_components/ledfx/
├── __init__.py          # Entry point, coordinator setup, virtual filtering
├── config_flow.py       # UI configuration flow
├── const.py             # Constants, gradient presets, category mappings
├── ledfx_client.py      # Async API client
├── switch.py            # Switch entities (On/Off)
├── select.py            # Select entities (effects + gradients)
├── manifest.json        # Integration metadata
└── strings.json         # Translation strings

Root files:
├── README.md            # User documentation
├── LICENSE              # MIT License
├── hacs.json            # HACS compatibility
├── .gitignore           # Git ignore rules
└── GITHUB_SETUP.md      # GitHub publication guide
```

## Key Technical Details

### LEDFX API Endpoints Used
- `GET /api/info` - Connection test
- `GET /api/virtuals` - All virtuals with status
- `GET /api/devices` - Device online status
- `GET /api/schema` - Available effects with categories
- `POST /api/virtuals/{id}/effects` - Set new effect
- `DELETE /api/virtuals/{id}/effects` - Clear effect (turn off)

### Virtual Filtering Logic
Location: `__init__.py`, function `should_include_virtual()`

**Filters out virtuals ending with:**
- `-background`
- `-foreground`
- `-mask`

**Reason:** LEDFX creates layer virtuals automatically. Users typically only want main virtuals.

### Effect Categories
Location: `const.py`

**Audio-Reactive Categories:**
- Classic (energy, power, scroll)
- Atmospheric
- BPM
- 2D
- Matrix
- Simple

**Non-Reactive Categories:**
- Non-Reactive (gradient, rainbow, fade)
- Diagnostic

### Gradient Presets
8 predefined gradients in `const.py`:
- Rainbow, Fire, Ocean, Sunset, Purple Dream, Forest, Ice, Lava
- Each is a CSS linear-gradient string
- Applied via effect config's `gradient` property

### State Synchronization
- Coordinator polls every 30 seconds
- After effect/gradient changes: `coordinator.async_request_refresh()`
- This ensures switch state updates when effect is changed

### Device Online Status
- Fetched from `/api/devices` endpoint
- Used to set `available` property on all entities
- Entities show as "unavailable" when device is offline

## Known Limitations & Design Decisions

1. **No RGB Color Control**
   - LEDFX works with effects and gradients, not simple RGB
   - Previous light entity with color picker didn't work well
   - Switched to simple switch + gradient presets instead

2. **Effect Changes Activate Virtual**
   - Changing effect automatically turns on the virtual
   - Coordinator refresh ensures switch state reflects this
   - By design - you can't have an effect without the virtual being active

3. **Gradient Only Works on Active Effects**
   - Gradient is part of effect config
   - If no effect is running, gradient selector may not update visual output
   - This is a LEDFX API limitation

4. **No Brightness Control**
   - LEDFX effects have their own brightness parameters in config
   - Different effects have different brightness properties
   - Could be added per-effect but would be complex

## Current Issues & TODO

### Known Issues
None currently - integration is working as designed.

### Potential Enhancements
1. **Brightness Control** - Add a number entity for brightness (needs per-effect mapping)
2. **Custom Gradients** - Allow users to define their own gradients in config
3. **Scene Support** - LEDFX has scenes API, could add scene select entity
4. **Effect Configuration** - Expose effect parameters (speed, intensity, etc.)
5. **Multi-Device Selection** - Allow selecting which virtuals to include during setup
6. **Icons** - Add custom icons for different effect types

## Development Environment Setup

### Requirements
- Python 3.11+
- Home Assistant 2023.1+
- LEDFX server running (typically on port 8888)

### Local Testing
1. Copy `custom_components/ledfx` to HA's `custom_components/` directory
2. Restart Home Assistant
3. Add integration via UI (Settings → Devices & Services → Add Integration)
4. Enter LEDFX server IP and port

### Debugging
Enable debug logging in `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.ledfx: debug
```

## API Client Implementation Notes

### Session Management
- Uses Home Assistant's `async_get_clientsession()`
- Single aiohttp session shared across all API calls
- Properly closed on integration unload

### Error Handling
- Client raises `aiohttp.ClientError` on connection issues
- Coordinator catches errors and marks entities unavailable
- Logs errors but doesn't crash integration

### Rate Limiting
- 30-second polling interval to avoid hammering LEDFX
- Manual refresh triggered only after user actions (effect changes)

## Testing Checklist

Before publishing updates:
- [ ] Integration loads without errors
- [ ] Virtuals discovered correctly (no background/foreground/mask)
- [ ] Switch turns on/off
- [ ] Audio-reactive effects populate and work
- [ ] Static effects populate and work
- [ ] Gradient presets apply correctly
- [ ] Device offline detection works
- [ ] Coordinator refresh after effect change updates switch state
- [ ] No errors in Home Assistant logs
- [ ] HACS validation passes

## GitHub Publication Process

See `GITHUB_SETUP.md` for detailed steps.

**Quick checklist:**
1. Create GitHub repository (public)
2. Upload files maintaining folder structure
3. Create release with tag `v1.0.0`
4. Users add via HACS custom repository

## Support & Community

**For issues:**
- Check Home Assistant logs first
- Verify LEDFX is accessible at configured IP/port
- Test API endpoints manually with curl
- Check that virtuals are configured in LEDFX

**Common user mistakes:**
- Wrong IP address
- LEDFX not running
- Port blocked by firewall
- No virtuals configured in LEDFX

## Code Style & Conventions

- Follow Home Assistant code style
- Use type hints (`dict[str, Any]`)
- Async/await for all I/O operations
- Log errors with context (virtual ID, error message)
- Use coordinator for state management, not manual polling

## Dependencies

- `aiohttp>=3.8.0` (async HTTP client)
- Home Assistant 2023.1+ (for coordinator improvements)

## License

MIT License - See LICENSE file

---

## Quick Reference: Key Functions

**`__init__.py`**
- `should_include_virtual()` - Virtual filtering logic
- `async_update_data()` - Coordinator update function

**`ledfx_client.py`**
- `get_virtuals()` - Fetch all virtuals
- `get_devices()` - Fetch device status
- `get_effects()` - Fetch available effects from schema
- `set_virtual_effect()` - Apply effect to virtual
- `clear_virtual_effect()` - Turn off virtual

**`switch.py`**
- `async_turn_on()` - Activate virtual with last effect
- `async_turn_off()` - Clear effect (deactivate)

**`select.py`**
- `LEDFXEffectSelect` - Effect selection (filtered by category)
- `LEDFXGradientSelect` - Gradient preset selection
- `async_select_option()` - Apply effect/gradient and refresh coordinator

---

## Contact & Handoff Notes

This integration was developed iteratively with the following key decisions:

1. Started with light entity → replaced with switch (RGB control didn't fit LEDFX's effect-based model)
2. Initially one effect dropdown → split into reactive/non-reactive for better UX
3. Added virtual filtering to hide LEDFX's automatic layer virtuals
4. Coordinator refresh after changes ensures UI stays in sync

The integration is production-ready and follows Home Assistant best practices.
