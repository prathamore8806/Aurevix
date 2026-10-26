"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GAMING MODE - CONSTANTS & CONFIGURATION                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains:
- Cyberpunk color palette
- Direction enum
- Configuration constants
- Feature flags
"""

from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTION ENUM
# ═══════════════════════════════════════════════════════════════════════════════
class Direction(Enum):
    """Direction enum for gaming controls"""
    NONE = "NONE"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


# ═══════════════════════════════════════════════════════════════════════════════
# CYBERPUNK COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════
class CyberColors:
    """Futuristic Cyberpunk Color Palette"""
   
    # Navy Blues
    NAVY_DARKEST = "#050a15"
    NAVY_DARKER = "#0a1628"
    NAVY_DARK = "#0d1b2a"
    NAVY_BASE = "#1b263b"
    NAVY_LIGHT = "#243b55"
   
    # Cyan Accents
    CYAN_BRIGHT = "#00ffff"
    CYAN_PRIMARY = "#00d4ff"
    CYAN_MEDIUM = "#00a8cc"
    CYAN_DARK = "#006688"
    CYAN_GLOW = "#00e5ff"
   
    # Electric Blues
    ELECTRIC_BLUE = "#0080ff"
    ELECTRIC_LIGHT = "#00bfff"
   
    # Neon Colors
    NEON_GREEN = "#00ff88"
    NEON_PINK = "#ff00ff"
    NEON_PURPLE = "#bf00ff"
    NEON_YELLOW = "#ffff00"
   
    # Accent Colors
    GOLD = "#ffd700"
    ORANGE = "#ff6b35"
    RED = "#ff3333"
    MAGENTA = "#ff00ff"
    PINK = "#ff0080"
    PURPLE = "#8b00ff"
    HOT_PINK = "#ff1493"
   
    # Holographic
    HOLO_BLUE = "#00c8ff"
    HOLO_CYAN = "#00fff2"
    HOLO_GREEN = "#00ffa0"
   
    # Text
    TEXT_WHITE = "#ffffff"
    TEXT_LIGHT = "#e0e0e0"
    TEXT_DIM = "#5588aa"
    TEXT_CYAN = "#a0d2ff"
   
    # Glitch Colors
    GLITCH_RED = "#ff0040"
    GLITCH_CYAN = "#00ffff"
    GLITCH_MAGENTA = "#ff00ff"


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Camera Settings
CAMERA_FPS = 10  # Frames per second for camera update
CAMERA_TIMER_INTERVAL = 100  # ms (10 FPS)

# Animation Settings
ANIMATION_FPS = 5  # Frames per second for UI animations
ANIMATION_TIMER_INTERVAL = 200  # ms (5 FPS)

# Floating Window Animation
FLOATING_ANIMATION_FPS = 5  # Frames per second for floating window
FLOATING_ANIMATION_INTERVAL = 200  # ms (5 FPS)

# Direction Detection
DIRECTION_THRESHOLD = 0.15  # Sensitivity for direction changes

# Camera Health
MAX_EMPTY_FRAMES = 60  # Maximum consecutive empty frames before recovery
CAMERA_HEALTH_CHECK_INTERVAL = 3000  # ms

# Particle Effects (reduced for performance)
PARTICLE_COUNT = 5  # Reduced from 20
DATA_STREAM_COUNT = 2  # Reduced from 8

# FPS Calculation
FPS_UPDATE_INTERVAL = 1000  # ms

# Feature Flags
GAMING_CANVAS_AVAILABLE = False
GAME_CONTROLLER_AVAILABLE = False

# Version Info
VERSION = "v3.1"
VERSION_FEATURES = "📌✅"  # Pin emoji + Check emoji