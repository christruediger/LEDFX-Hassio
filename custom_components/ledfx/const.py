"""Constants for the LEDFX integration."""
from datetime import timedelta

DOMAIN = "ledfx"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"

# Defaults
DEFAULT_PORT = 8888
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

# API Endpoints
API_INFO = "/api/info"
API_VIRTUALS = "/api/virtuals"
API_SCENES = "/api/scenes"
API_EFFECTS = "/api/effects"

# Effect categories that are audio-reactive
AUDIO_REACTIVE_CATEGORIES = {
    "Classic",
    "Atmospheric", 
    "BPM",
    "2D",
    "Matrix",
    "Simple",
}

# Effect categories that are non-reactive
NON_REACTIVE_CATEGORIES = {
    "Non-Reactive",
    "Diagnostic",
}

# Gradient Presets
GRADIENT_PRESETS = {
    "Rainbow": "linear-gradient(90deg, rgb(255, 0, 0) 0%, rgb(255, 120, 0) 14%, rgb(255, 200, 0) 28%, rgb(0, 255, 0) 42%, rgb(0, 199, 140) 56%, rgb(0, 0, 255) 70%, rgb(128, 0, 128) 84%, rgb(255, 0, 178) 98%)",
    "Fire": "linear-gradient(90deg, rgb(255, 0, 0) 0%, rgb(255, 60, 0) 25%, rgb(255, 120, 0) 50%, rgb(255, 200, 0) 75%, rgb(255, 255, 0) 100%)",
    "Ocean": "linear-gradient(90deg, rgb(0, 0, 139) 0%, rgb(0, 100, 200) 25%, rgb(0, 191, 255) 50%, rgb(0, 255, 200) 75%, rgb(0, 255, 127) 100%)",
    "Sunset": "linear-gradient(90deg, rgb(255, 100, 0) 0%, rgb(255, 140, 60) 25%, rgb(255, 100, 150) 50%, rgb(200, 100, 200) 75%, rgb(138, 43, 226) 100%)",
    "Purple Dream": "linear-gradient(90deg, rgb(75, 0, 130) 0%, rgb(138, 43, 226) 25%, rgb(186, 85, 211) 50%, rgb(221, 160, 221) 75%, rgb(255, 192, 203) 100%)",
    "Forest": "linear-gradient(90deg, rgb(0, 100, 0) 0%, rgb(34, 139, 34) 25%, rgb(50, 205, 50) 50%, rgb(144, 238, 144) 75%, rgb(152, 251, 152) 100%)",
    "Ice": "linear-gradient(90deg, rgb(0, 191, 255) 0%, rgb(135, 206, 250) 25%, rgb(176, 224, 230) 50%, rgb(224, 255, 255) 75%, rgb(240, 248, 255) 100%)",
    "Lava": "linear-gradient(90deg, rgb(139, 0, 0) 0%, rgb(178, 34, 34) 25%, rgb(255, 0, 0) 50%, rgb(255, 69, 0) 75%, rgb(255, 140, 0) 100%)",
}
