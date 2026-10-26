"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     █████╗ ██╗   ██╗██████╗ ███████╗██╗   ██╗██╗██╗  ██╗                   ║
║    ██╔══██╗██║   ██║██╔══██╗██╔════╝██║   ██║██║╚██╗██╔╝                   ║
║    ███████║██║   ██║██████╔╝█████╗  ██║   ██║██║ ╚███╔╝                    ║
║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ╚██╗ ██╔╝██║ ██╔██╗                    ║
║    ██║  ██║╚██████╔╝██║  ██║███████╗ ╚████╔╝ ██║██╔╝ ██╗                   ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═╝                   ║
║                                                                              ║
║        ◢◤ ULTRA CYBERPUNK HOLOGRAPHIC GAMING INTERFACE v3.1 ◢◤             ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✅ FIX: Floating Camera stays visible when main app is minimized!         ║
║  ✅ FIX: Floating Camera CLOSES when exiting to Desktop Mode!              ║
║  ✅ External games can now see gesture feedback at all times               ║
║  ✅ Camera window is completely independent of main window                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

GAMING MODE PACKAGE
===================

This package provides the complete Gaming Mode functionality for Aurevix.

Modules:
--------
- constants: Color palette, enums, and configuration
- utils: Helper functions and decorators
- ui_components: Reusable UI widgets (CyberButton, GestureHUDPanel)
- direction_controller: Cyberpunk direction controller widget
- camera_widget: Holographic camera display widget
- floating_camera: Independent floating camera window

Usage:
------
    from gaming_mode.constants import CyberColors, Direction
    from gaming_mode.ui_components import CyberButton, GestureHUDPanel
    from gaming_mode.direction_controller import CyberpunkDirectionController
    from gaming_mode.floating_camera import FloatingCameraWindow
"""

# Version info
__version__ = "3.1"
__author__ = "Aurevix"

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT ALL PUBLIC CLASSES AND FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Constants and Enums
from gaming_mode.constants import (
    Direction,
    CyberColors,
    CAMERA_FPS,
    CAMERA_TIMER_INTERVAL,
    ANIMATION_FPS,
    ANIMATION_TIMER_INTERVAL,
    FLOATING_ANIMATION_FPS,
    FLOATING_ANIMATION_INTERVAL,
    DIRECTION_THRESHOLD,
    MAX_EMPTY_FRAMES,
    CAMERA_HEALTH_CHECK_INTERVAL,
    PARTICLE_COUNT,
    DATA_STREAM_COUNT,
    FPS_UPDATE_INTERVAL,
    VERSION,
    VERSION_FEATURES,
)

# Utilities
from gaming_mode.utils import (
    safe_execute,
    load_gaming_modules,
    hex_to_rgb,
    rgb_to_hex,
    normalize_direction,
    get_direction_icon,
    get_gesture_icon,
    clamp,
    normalize_position,
    get_fps_color,
)

# UI Components
from gaming_mode.ui_components import (
    CyberButton,
    GestureHUDPanel,
)

# Direction Controller
from gaming_mode.direction_controller import (
    CyberpunkDirectionController,
)

# Camera Widgets
from gaming_mode.camera_widget import (
    UltraHolographicCameraWidget,
)

# Floating Camera Window
from gaming_mode.floating_camera import (
    FloatingCameraWindow,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PACKAGE-LEVEL INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# Load gaming modules and get availability status
_GAMING_CANVAS_AVAILABLE, _GAME_CONTROLLER_AVAILABLE, _GamingCanvas, _game_controller = load_gaming_modules()

# Export availability flags
GAMING_CANVAS_AVAILABLE = _GAMING_CANVAS_AVAILABLE
GAME_CONTROLLER_AVAILABLE = _GAME_CONTROLLER_AVAILABLE

# Export loaded modules (may be None if not available)
GamingCanvas = _GamingCanvas
game_controller = _game_controller


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API - What gets exported with "from gaming_mode import *"
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Version
    "__version__",
    
    # Constants & Enums
    "Direction",
    "CyberColors",
    "CAMERA_FPS",
    "CAMERA_TIMER_INTERVAL",
    "ANIMATION_FPS",
    "ANIMATION_TIMER_INTERVAL",
    "DIRECTION_THRESHOLD",
    "MAX_EMPTY_FRAMES",
    "VERSION",
    
    # Availability Flags
    "GAMING_CANVAS_AVAILABLE",
    "GAME_CONTROLLER_AVAILABLE",
    "GamingCanvas",
    "game_controller",
    
    # Utilities
    "safe_execute",
    "load_gaming_modules",
    "hex_to_rgb",
    "rgb_to_hex",
    "normalize_direction",
    "get_direction_icon",
    "get_gesture_icon",
    "clamp",
    "normalize_position",
    "get_fps_color",
    
    # UI Components
    "CyberButton",
    "GestureHUDPanel",
    
    # Widgets
    "CyberpunkDirectionController",
    "UltraHolographicCameraWidget",
    "FloatingCameraWindow",
]