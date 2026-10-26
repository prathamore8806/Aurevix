"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GAMING MODE - UTILITIES & HELPERS                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains:
- Safe execution decorator
- Helper functions
- Import utilities
"""

from functools import wraps
import traceback


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE EXECUTION DECORATOR - Prevents crashes from camera lag
# ═══════════════════════════════════════════════════════════════════════════════
def safe_execute(func):
    """Decorator to catch exceptions and prevent crashes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ Safe catch in {func.__name__}: {e}")
            return None
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE IMPORTS - Import gaming modules with error handling
# ═══════════════════════════════════════════════════════════════════════════════
def load_gaming_modules():
    """
    Safely load gaming modules and return availability status.
    
    Returns:
        tuple: (GAMING_CANVAS_AVAILABLE, GAME_CONTROLLER_AVAILABLE, GamingCanvas, game_controller)
    """
    print("\n" + "═" * 70)
    print("     ◢◤ AUREVIX ULTRA CYBERPUNK GAMING SYSTEM v3.1 ◢◤")
    print("═" * 70)
    
    GAMING_CANVAS_AVAILABLE = False
    GAME_CONTROLLER_AVAILABLE = False
    GamingCanvas = None
    game_controller = None
    
    try:
        from gaming_canvas import GamingCanvas as GC
        GamingCanvas = GC
        GAMING_CANVAS_AVAILABLE = True
        print("  ✅ Gaming Canvas")
    except Exception as e:
        print(f"  ⚠️  Gaming Canvas: {e}")
    
    try:
        from gaming_gesture_controller import game_controller as gc
        game_controller = gc
        GAME_CONTROLLER_AVAILABLE = True
        print("  ✅ Game Controller")
    except Exception as e:
        print(f"  ⚠️  Game Controller: {e}")
    
    print("  ✅ Using hand_tracker.py (main tracker)")
    print("  ✅ Camera State Preservation: ON→ON, OFF→OFF")
    print("  ✅ Desktop Mode Always Activates on Exit")
    print("  ✨ ULTRA Holographic Camera Effects ENABLED")
    print("  🎮 CYBERPUNK Direction Controller ENABLED")
    print("  🔒 Floating Camera STAYS VISIBLE when app minimized")
    print("  ✅ Floating Camera CLOSES when exiting Gaming Mode")
    print("═" * 70 + "\n")
    
    return GAMING_CANVAS_AVAILABLE, GAME_CONTROLLER_AVAILABLE, GamingCanvas, game_controller


# ═══════════════════════════════════════════════════════════════════════════════
# COLOR UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def hex_to_rgb(hex_color):
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color (str): Hex color string (e.g., "#00ffff")
    
    Returns:
        tuple: (r, g, b) values
    """
    c = hex_color.lstrip('#')
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def rgb_to_hex(r, g, b):
    """
    Convert RGB values to hex color string.
    
    Args:
        r (int): Red value (0-255)
        g (int): Green value (0-255)
        b (int): Blue value (0-255)
    
    Returns:
        str: Hex color string
    """
    return f"#{r:02x}{g:02x}{b:02x}"


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTION UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def normalize_direction(direction):
    """
    Normalize direction value to string.
    
    Args:
        direction: Direction enum, object with value attribute, or string
    
    Returns:
        str: Direction name as string
    """
    from gaming_mode.constants import Direction
    
    if isinstance(direction, Direction):
        return direction.value
    elif hasattr(direction, 'value'):
        return direction.value
    else:
        return str(direction)


def get_direction_icon(direction):
    """
    Get icon for direction.
    
    Args:
        direction: Direction value
    
    Returns:
        str: Unicode icon for direction
    """
    icons = {
        "UP": "▲",
        "DOWN": "▼", 
        "LEFT": "◀",
        "RIGHT": "▶",
        "NONE": "◎",
        "CENTER": "◎"
    }
    dir_name = normalize_direction(direction)
    return icons.get(dir_name, "◎")


# ═══════════════════════════════════════════════════════════════════════════════
# GESTURE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def get_gesture_icon(gesture):
    """
    Get icon for gesture.
    
    Args:
        gesture (str): Gesture name
    
    Returns:
        str: Unicode emoji for gesture
    """
    icons = {
        "FIST": "✊",
        "PALM": "✋",
        "POINT": "☝",
        "PEACE": "✌",
        "THUMBS_UP": "👍",
        "ROCK": "🤘",
        "OK": "👌",
        "NONE": "◎"
    }
    return icons.get(gesture, "●")


# ═══════════════════════════════════════════════════════════════════════════════
# POSITION UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def clamp(value, min_val, max_val):
    """
    Clamp value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def normalize_position(x, y, width=640, height=480):
    """
    Normalize pixel position to 0.0-1.0 range.
    
    Args:
        x: X pixel position
        y: Y pixel position
        width: Frame width (default 640)
        height: Frame height (default 480)
    
    Returns:
        tuple: (normalized_x, normalized_y)
    """
    norm_x = clamp(x / width if x else 0.5, 0.0, 1.0)
    norm_y = clamp(y / height if y else 0.5, 0.0, 1.0)
    return norm_x, norm_y


# ═══════════════════════════════════════════════════════════════════════════════
# TIMING UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def get_fps_color(fps):
    """
    Get color based on FPS value.
    
    Args:
        fps (int): Current FPS value
    
    Returns:
        str: Hex color string
    """
    from gaming_mode.constants import CyberColors
    
    if fps >= 25:
        return CyberColors.NEON_GREEN
    elif fps >= 15:
        return CyberColors.GOLD
    else:
        return CyberColors.ORANGE