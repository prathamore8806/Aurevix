"""
Gaming Gesture Controller - External Games Support (ENHANCED + FIXED)
Maps gestures AND directions to keyboard/mouse for ANY game
Works with gaming_hand_tracker.py

FIXES APPLIED:
- Uses 'keyboard' library instead of pyautogui for KEY inputs
- keyboard library works with Admin/Fullscreen/DirectInput games
- pyautogui kept ONLY for mouse actions
- ctypes SendInput fallback for maximum compatibility
- Proper key hold/release with keyboard library
- Thread-safe operation

Features:
- Dual-mode operation (Internal/External)
- Keyboard (keyboard lib) + Mouse (pyautogui) simulation
- WASD or Arrow key support
- Continuous key holding for smooth movement
- Game presets (FPS, Racing, Platformer, etc.)
- Hold gestures for continuous actions
- Works with Admin/Elevated games
"""

import time
import threading
from collections import deque
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List, Set

# ═══════════════════════════════════════════════════════════════════════════════
# KEYBOARD LIBRARY IMPORT (PRIMARY - for key simulation)
# ═══════════════════════════════════════════════════════════════════════════════

KEYBOARD_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
    print("✅ Keyboard library available (Admin game support)")
except ImportError:
    print("⚠️ keyboard library not installed!")
    print("   Install with: pip install keyboard")
except Exception as e:
    print(f"⚠️ keyboard import error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PYAUTOGUI IMPORT (SECONDARY - only for mouse actions)
# ═══════════════════════════════════════════════════════════════════════════════

PYAUTOGUI_AVAILABLE = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    PYAUTOGUI_AVAILABLE = True
    print("✅ PyAutoGUI available (Mouse control)")
except ImportError:
    print("⚠️ PyAutoGUI not installed - Mouse actions won't work")
except Exception as e:
    print(f"⚠️ PyAutoGUI import error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CTYPES FALLBACK (for DirectInput games)
# ═══════════════════════════════════════════════════════════════════════════════

CTYPES_AVAILABLE = False
SendInput = None
PUL = None

try:
    import ctypes
    from ctypes import wintypes
    
    CTYPES_AVAILABLE = True
    
    # Windows API constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    
    # Virtual key code mapping
    VK_CODES = {
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
        'z': 0x5A,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        'space': 0x20, 'enter': 0x0D, 'escape': 0x1B, 'tab': 0x09,
        'shift': 0xA0, 'ctrl': 0xA2, 'alt': 0xA4,
        'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
        'backspace': 0x08, 'delete': 0x2E,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    }
    
    # Scan code mapping (for DirectInput games)
    SCAN_CODES = {
        'a': 0x1E, 'b': 0x30, 'c': 0x2E, 'd': 0x20, 'e': 0x12,
        'f': 0x21, 'g': 0x22, 'h': 0x23, 'i': 0x17, 'j': 0x24,
        'k': 0x25, 'l': 0x26, 'm': 0x32, 'n': 0x31, 'o': 0x18,
        'p': 0x19, 'q': 0x10, 'r': 0x13, 's': 0x1F, 't': 0x14,
        'u': 0x16, 'v': 0x2F, 'w': 0x11, 'x': 0x2D, 'y': 0x15,
        'z': 0x2C,
        '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05, '5': 0x06,
        '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A, '0': 0x0B,
        'space': 0x39, 'enter': 0x1C, 'escape': 0x01, 'tab': 0x0F,
        'shift': 0x2A, 'ctrl': 0x1D, 'alt': 0x38,
        'up': 0x48, 'down': 0x50, 'left': 0x4B, 'right': 0x4D,
        'backspace': 0x0E,
        'f1': 0x3B, 'f2': 0x3C, 'f3': 0x3D, 'f4': 0x3E,
        'f5': 0x3F, 'f6': 0x40, 'f7': 0x41, 'f8': 0x42,
    }
    
    # Input structure for SendInput
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]
    
    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _fields_ = [
            ("type", wintypes.DWORD),
            ("_input", _INPUT)
        ]
    
    def _send_key_event(key_name, key_up=False):
        """Send a key event using Windows SendInput API with scan codes"""
        key_lower = key_name.lower()
        scan_code = SCAN_CODES.get(key_lower, 0)
        vk_code = VK_CODES.get(key_lower, 0)
        
        if scan_code == 0 and vk_code == 0:
            return False
        
        extra = ctypes.c_ulong(0)
        
        flags = KEYEVENTF_SCANCODE
        if key_up:
            flags |= KEYEVENTF_KEYUP
        
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp._input.ki = KEYBDINPUT(
            wVk=0,
            wScan=scan_code,
            dwFlags=flags,
            time=0,
            dwExtraInfo=ctypes.pointer(extra)
        )
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        return True
    
    print("✅ ctypes SendInput available (DirectInput game support)")

except Exception as e:
    print(f"⚠️ ctypes not available: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED KEY SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════

class KeySimulator:
    """
    Unified key simulation with 3-tier fallback:
    1. keyboard library (best for admin games)
    2. ctypes SendInput with scan codes (best for DirectInput games)
    3. pyautogui (fallback, doesn't work with admin games)
    """
    
    @staticmethod
    def press_key(key: str):
        """Press and release a key"""
        key_lower = key.lower()
        
        # Tier 1: keyboard library
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.press_and_release(key_lower)
                return True
            except Exception as e:
                print(f"⚠️ keyboard.press failed: {e}")
        
        # Tier 2: ctypes SendInput
        if CTYPES_AVAILABLE:
            try:
                _send_key_event(key_lower, key_up=False)
                time.sleep(0.05)
                _send_key_event(key_lower, key_up=True)
                return True
            except Exception as e:
                print(f"⚠️ ctypes press failed: {e}")
        
        # Tier 3: pyautogui fallback
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.press(key_lower)
                return True
            except Exception as e:
                print(f"⚠️ pyautogui press failed: {e}")
        
        print(f"❌ No method available to press key: {key}")
        return False
    
    @staticmethod
    def hold_key(key: str):
        """Hold down a key"""
        key_lower = key.lower()
        
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.press(key_lower)
                return True
            except Exception as e:
                print(f"⚠️ keyboard.hold failed: {e}")
        
        if CTYPES_AVAILABLE:
            try:
                _send_key_event(key_lower, key_up=False)
                return True
            except Exception as e:
                print(f"⚠️ ctypes hold failed: {e}")
        
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.keyDown(key_lower)
                return True
            except Exception as e:
                print(f"⚠️ pyautogui hold failed: {e}")
        
        return False
    
    @staticmethod
    def release_key(key: str):
        """Release a held key"""
        key_lower = key.lower()
        
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.release(key_lower)
                return True
            except Exception as e:
                print(f"⚠️ keyboard.release failed: {e}")
        
        if CTYPES_AVAILABLE:
            try:
                _send_key_event(key_lower, key_up=True)
                return True
            except Exception as e:
                print(f"⚠️ ctypes release failed: {e}")
        
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.keyUp(key_lower)
                return True
            except Exception as e:
                print(f"⚠️ pyautogui release failed: {e}")
        
        return False
    
    @staticmethod
    def mouse_click(button="left"):
        """Click mouse button (always uses pyautogui)"""
        if PYAUTOGUI_AVAILABLE:
            try:
                if button == "left":
                    pyautogui.click()
                elif button == "right":
                    pyautogui.rightClick()
                elif button == "middle":
                    pyautogui.middleClick()
                return True
            except Exception as e:
                print(f"⚠️ Mouse click failed: {e}")
        return False
    
    @staticmethod
    def mouse_down(button="left"):
        """Hold mouse button"""
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.mouseDown(button=button)
                return True
            except:
                pass
        return False
    
    @staticmethod
    def mouse_up(button="left"):
        """Release mouse button"""
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.mouseUp(button=button)
                return True
            except:
                pass
        return False


# Create global simulator instance
key_sim = KeySimulator()


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTION ENUM (must match gaming_hand_tracker.py)
# ═══════════════════════════════════════════════════════════════════════════════

class Direction(Enum):
    """Movement directions"""
    NONE = "NONE"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP_LEFT = "UP_LEFT"
    UP_RIGHT = "UP_RIGHT"
    DOWN_LEFT = "DOWN_LEFT"
    DOWN_RIGHT = "DOWN_RIGHT"


# ═══════════════════════════════════════════════════════════════════════════════
# GESTURE ACTION TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ActionType(Enum):
    """Type of action to perform"""
    KEY_TAP = "KEY_TAP"
    KEY_HOLD = "KEY_HOLD"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_RIGHT = "MOUSE_RIGHT"
    MOUSE_HOLD = "MOUSE_HOLD"
    KEY_COMBO = "KEY_COMBO"


# ═══════════════════════════════════════════════════════════════════════════════
# GAME PRESET DATA CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GamePreset:
    """Predefined key bindings for different game types."""
    name: str
    description: str = ""
    up: str = 'w'
    down: str = 's'
    left: str = 'a'
    right: str = 'd'
    use_arrows: bool = False
    gestures: Dict[str, tuple] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.use_arrows:
            self.up = 'up'
            self.down = 'down'
            self.left = 'left'
            self.right = 'right'


# ═══════════════════════════════════════════════════════════════════════════════
# PREDEFINED GAME PRESETS (UNCHANGED)
# ═══════════════════════════════════════════════════════════════════════════════

GAME_PRESETS: Dict[str, GamePreset] = {
    
    "default": GamePreset(
        name="Default (WASD)",
        description="Standard WASD + common keys",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump/Grab"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "Ability"),
            'POINT':       ('e',      ActionType.KEY_TAP,    "Interact"),
            'PEACE':       ('space',  ActionType.KEY_TAP,    "Jump"),
            'THUMBS_UP':   ('f',      ActionType.KEY_TAP,    "Use/Confirm"),
            'THUMBS_DOWN': ('escape', ActionType.KEY_TAP,    "Menu/Cancel"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reload/Action"),
            'THREE':       ('3',      ActionType.KEY_TAP,    "Weapon 3"),
        }
    ),
    
    "fps": GamePreset(
        name="FPS Shooter",
        description="For Valorant, CS2, Apex Legends, etc.",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "Ability Q"),
            'POINT':       (None,     ActionType.MOUSE_CLICK,"Shoot"),
            'PEACE':       ('ctrl',   ActionType.KEY_HOLD,   "Crouch"),
            'THUMBS_UP':   ('f',      ActionType.KEY_TAP,    "Use/Defuse"),
            'THUMBS_DOWN': ('g',      ActionType.KEY_TAP,    "Drop Weapon"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reload"),
            'THREE':       ('e',      ActionType.KEY_TAP,    "Ability E"),
        }
    ),
    
    "valorant": GamePreset(
        name="Valorant",
        description="Optimized for Valorant",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump"),
            'PALM':        ('c',      ActionType.KEY_TAP,    "Ability C"),
            'POINT':       (None,     ActionType.MOUSE_CLICK,"Fire"),
            'PEACE':       ('ctrl',   ActionType.KEY_HOLD,   "Crouch"),
            'THUMBS_UP':   ('f',      ActionType.KEY_TAP,    "Use/Plant"),
            'THUMBS_DOWN': ('g',      ActionType.KEY_TAP,    "Drop"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause"),
            'OK':          ('e',      ActionType.KEY_TAP,    "Ability E"),
            'THREE':       ('q',      ActionType.KEY_TAP,    "Ability Q"),
        }
    ),
    
    "csgo": GamePreset(
        name="CS:GO / CS2",
        description="For Counter-Strike",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump"),
            'PALM':        ('4',      ActionType.KEY_TAP,    "Grenade"),
            'POINT':       (None,     ActionType.MOUSE_CLICK,"Shoot"),
            'PEACE':       ('ctrl',   ActionType.KEY_HOLD,   "Crouch"),
            'THUMBS_UP':   ('e',      ActionType.KEY_TAP,    "Use"),
            'THUMBS_DOWN': ('g',      ActionType.KEY_TAP,    "Drop"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reload"),
            'THREE':       ('b',      ActionType.KEY_TAP,    "Buy Menu"),
        }
    ),
    
    "racing": GamePreset(
        name="Racing (Arrows)",
        description="For racing games with arrow keys",
        use_arrows=True,
        gestures={
            'FIST':        ('space',  ActionType.KEY_HOLD,   "Brake/Handbrake"),
            'PALM':        ('n',      ActionType.KEY_TAP,    "Nitro"),
            'POINT':       ('ctrl',   ActionType.KEY_HOLD,   "Look Back"),
            'PEACE':       ('space',  ActionType.KEY_TAP,    "Handbrake"),
            'THUMBS_UP':   ('enter',  ActionType.KEY_TAP,    "Confirm"),
            'THUMBS_DOWN': ('escape', ActionType.KEY_TAP,    "Pause"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause/Boost"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reset Car"),
            'THREE':       ('c',      ActionType.KEY_TAP,    "Change View"),
        }
    ),
    
    "racing_wasd": GamePreset(
        name="Racing (WASD)",
        description="For racing games with WASD",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_HOLD,   "Brake"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "Nitro"),
            'POINT':       ('e',      ActionType.KEY_TAP,    "Look Back"),
            'PEACE':       ('space',  ActionType.KEY_TAP,    "Handbrake"),
            'THUMBS_UP':   ('enter',  ActionType.KEY_TAP,    "Confirm"),
            'THUMBS_DOWN': ('escape', ActionType.KEY_TAP,    "Pause"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause/Boost"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reset"),
            'THREE':       ('c',      ActionType.KEY_TAP,    "Camera"),
        }
    ),
    
    "platformer": GamePreset(
        name="Platformer",
        description="For platformer/action games",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "Special"),
            'POINT':       ('e',      ActionType.KEY_TAP,    "Attack"),
            'PEACE':       ('space',  ActionType.KEY_TAP,    "Double Jump"),
            'THUMBS_UP':   ('f',      ActionType.KEY_TAP,    "Interact"),
            'THUMBS_DOWN': ('escape', ActionType.KEY_TAP,    "Pause"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause/Run"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Roll/Dodge"),
            'THREE':       ('tab',    ActionType.KEY_TAP,    "Inventory"),
        }
    ),
    
    "minecraft": GamePreset(
        name="Minecraft",
        description="For Minecraft",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_HOLD,   "Jump/Fly Up"),
            'PALM':        ('f',      ActionType.KEY_TAP,    "Swap Hands"),
            'POINT':       (None,     ActionType.MOUSE_CLICK,"Attack/Mine"),
            'PEACE':       (None,     ActionType.MOUSE_RIGHT,"Place/Use"),
            'THUMBS_UP':   ('e',      ActionType.KEY_TAP,    "Inventory"),
            'THUMBS_DOWN': ('q',      ActionType.KEY_TAP,    "Drop Item"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause/Sneak"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Pick Block"),
            'THREE':       ('ctrl',   ActionType.KEY_HOLD,   "Sprint"),
        }
    ),
    
    "fighting": GamePreset(
        name="Fighting Game",
        description="For fighting games",
        use_arrows=True,
        gestures={
            'FIST':        ('z',      ActionType.KEY_TAP,    "Punch"),
            'PALM':        ('a',      ActionType.KEY_TAP,    "Super"),
            'POINT':       ('c',      ActionType.KEY_TAP,    "Special"),
            'PEACE':       ('space',  ActionType.KEY_TAP,    "Jump"),
            'THUMBS_UP':   ('v',      ActionType.KEY_TAP,    "Block"),
            'THUMBS_DOWN': ('escape', ActionType.KEY_TAP,    "Pause"),
            'ROCK':        ('x',      ActionType.KEY_TAP,    "Pause/Kick"),
            'OK':          ('s',      ActionType.KEY_TAP,    "Grab"),
            'THREE':       ('d',      ActionType.KEY_TAP,    "Taunt"),
        }
    ),
    
    "browser": GamePreset(
        name="Browser Games",
        description="For simple browser/web games",
        use_arrows=True,
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump/Action"),
            'PALM':        ('c',      ActionType.KEY_TAP,    "Special"),
            'POINT':       ('z',      ActionType.KEY_TAP,    "Action 1"),
            'PEACE':       ('x',      ActionType.KEY_TAP,    "Action 2"),
            'THUMBS_UP':   ('enter',  ActionType.KEY_TAP,    "Confirm"),
            'THUMBS_DOWN': ('escape', ActionType.KEY_TAP,    "Back"),
            'ROCK':        ('p',      ActionType.KEY_TAP,    "Pause"),
            'OK':          ('v',      ActionType.KEY_TAP,    "Item"),
            'THREE':       ('r',      ActionType.KEY_TAP,    "Restart"),
        }
    ),
    
    "emulator": GamePreset(
        name="Emulator (NES/SNES)",
        description="For retro game emulators",
        use_arrows=True,
        gestures={
            'FIST':        ('z',      ActionType.KEY_TAP,    "A Button"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "L Button"),
            'POINT':       ('a',      ActionType.KEY_TAP,    "X Button"),
            'PEACE':       ('s',      ActionType.KEY_TAP,    "Y Button"),
            'THUMBS_UP':   ('enter',  ActionType.KEY_TAP,    "Start"),
            'THUMBS_DOWN': ('shift',  ActionType.KEY_TAP,    "Select"),
            'ROCK':        ('x',      ActionType.KEY_TAP,    "Pause/B Button"),
            'OK':          ('w',      ActionType.KEY_TAP,    "R Button"),
            'THREE':       ('escape', ActionType.KEY_TAP,    "Menu"),
        }
    ),
    
    "gta": GamePreset(
        name="GTA / Open World",
        description="For GTA, Saints Row, etc.",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump/Handbrake"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "Weapon Wheel"),
            'POINT':       (None,     ActionType.MOUSE_CLICK,"Shoot"),
            'PEACE':       ('ctrl',   ActionType.KEY_HOLD,   "Crouch/Duck"),
            'THUMBS_UP':   ('f',      ActionType.KEY_TAP,    "Enter Vehicle"),
            'THUMBS_DOWN': ('g',      ActionType.KEY_TAP,    "Throw/Drop"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause/Sprint"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reload"),
            'THREE':       ('e',      ActionType.KEY_TAP,    "Take Cover"),
        }
    ),
    
    "survival": GamePreset(
        name="Battle Royale",
        description="For Fortnite, PUBG, Warzone",
        up='w', down='s', left='a', right='d',
        gestures={
            'FIST':        ('space',  ActionType.KEY_TAP,    "Jump"),
            'PALM':        ('q',      ActionType.KEY_TAP,    "Build/Ability"),
            'POINT':       (None,     ActionType.MOUSE_CLICK,"Shoot"),
            'PEACE':       ('ctrl',   ActionType.KEY_HOLD,   "Crouch"),
            'THUMBS_UP':   ('f',      ActionType.KEY_TAP,    "Interact"),
            'THUMBS_DOWN': ('g',      ActionType.KEY_TAP,    "Grenade"),
            'ROCK':        ('shift',  ActionType.KEY_HOLD,   "Pause/Sprint"),
            'OK':          ('r',      ActionType.KEY_TAP,    "Reload"),
            'THREE':       ('z',      ActionType.KEY_HOLD,   "Prone"),
        }
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# GAME GESTURE CONTROLLER (FIXED VERSION)
# ═══════════════════════════════════════════════════════════════════════════════

class GameGestureController:
    """
    Dual-mode gesture controller for gaming (FIXED VERSION).
    
    KEY FIX: Uses keyboard library + ctypes SendInput instead of pyautogui
    for key simulation. This allows working with:
    - Admin/Elevated games
    - Fullscreen games
    - DirectInput games
    - Anti-cheat protected games (basic level)
    
    PyAutoGUI is only used for mouse actions now.
    """

    def __init__(self):
        print("🎮 Initializing Game Gesture Controller (FIXED)...")
        
        # STATE
        self.is_active = False
        self.control_mode = "INTERNAL"
        
        # CURRENT PRESET
        self.current_preset: GamePreset = GAME_PRESETS["default"]
        self.preset_name = "default"
        
        # GESTURE TRACKING
        self.gesture_history = deque(maxlen=10)
        self.last_gesture: Optional[str] = None
        self.current_gesture: Optional[str] = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.15
        
        # Hold gesture tracking
        self.held_gesture: Optional[str] = None
        self.gesture_hold_key: Optional[str] = None
        
        # DIRECTION TRACKING
        self.last_direction = Direction.NONE
        self.current_direction = Direction.NONE
        self.last_direction_time = 0
        self.direction_cooldown = 0.03
        
        # CALLBACKS
        self.game_callback: Optional[Callable] = None
        self.direction_callback: Optional[Callable] = None
        
        # KEY STATE MANAGEMENT
        self.held_keys: Set[str] = set()
        self.current_direction_key: Optional[str] = None
        self.mouse_held = False
        self.mouse_right_held = False
        self.continuous_direction = True
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Print capability status
        print("✅ Game Gesture Controller initialized (FIXED)")
        print(f"   Preset: {self.current_preset.name}")
        print(f"   keyboard lib: {'✅ Available' if KEYBOARD_AVAILABLE else '❌ Not Available'}")
        print(f"   ctypes:       {'✅ Available' if CTYPES_AVAILABLE else '❌ Not Available'}")
        print(f"   PyAutoGUI:    {'✅ Available (mouse only)' if PYAUTOGUI_AVAILABLE else '❌ Not Available'}")
        
        if not KEYBOARD_AVAILABLE and not CTYPES_AVAILABLE:
            print("\n   ⚠️ WARNING: No reliable key simulation method available!")
            print("   Install keyboard library: pip install keyboard")
            print("   Or run as Administrator for ctypes support")

    # ═══════════════════════════════════════════════════════════════════════════
    # PRESET MANAGEMENT (UNCHANGED)
    # ═══════════════════════════════════════════════════════════════════════════

    def set_preset(self, preset_name: str) -> bool:
        with self.lock:
            if preset_name not in GAME_PRESETS:
                print(f"⚠️ Unknown preset: {preset_name}")
                print(f"   Available: {list(GAME_PRESETS.keys())}")
                return False
            self._release_all_keys()
            self.current_preset = GAME_PRESETS[preset_name]
            self.preset_name = preset_name
            print(f"🎮 Loaded preset: {self.current_preset.name}")
            print(f"   {self.current_preset.description}")
            return True

    def get_available_presets(self) -> List[str]:
        return list(GAME_PRESETS.keys())

    def get_preset_info(self, preset_name: str = None) -> dict:
        preset = GAME_PRESETS.get(preset_name, self.current_preset)
        gesture_info = {}
        for gesture, (key, action_type, desc) in preset.gestures.items():
            if key is None:
                key_str = "Mouse" if action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_RIGHT] else "None"
            else:
                key_str = key
            gesture_info[gesture] = {
                'key': key_str,
                'action': action_type.value,
                'description': desc
            }
        return {
            'name': preset.name,
            'description': preset.description,
            'directions': {
                'UP': preset.up, 'DOWN': preset.down,
                'LEFT': preset.left, 'RIGHT': preset.right,
            },
            'gestures': gesture_info
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTROL MODE (UNCHANGED)
    # ═══════════════════════════════════════════════════════════════════════════

    def set_control_mode(self, mode: str):
        mode = mode.upper()
        if mode not in ["INTERNAL", "EXTERNAL"]:
            print(f"⚠️ Invalid mode: {mode}. Use 'INTERNAL' or 'EXTERNAL'")
            return
        with self.lock:
            self._release_all_keys()
            old_mode = self.control_mode
            self.control_mode = mode
            print(f"🎮 Control mode: {old_mode} → {mode}")
            if mode == "EXTERNAL":
                if KEYBOARD_AVAILABLE:
                    print(f"   ✅ Using keyboard library for key simulation")
                elif CTYPES_AVAILABLE:
                    print(f"   ✅ Using ctypes SendInput for key simulation")
                elif PYAUTOGUI_AVAILABLE:
                    print(f"   ⚠️ Using PyAutoGUI (may not work with admin games)")
                else:
                    print("   ❌ No key simulation method available!")
                print(f"   📋 Preset: {self.current_preset.name}")
            else:
                print("   ✅ Internal game mode active")

    def set_game_callback(self, callback: Callable):
        self.game_callback = callback

    def set_direction_callback(self, callback: Callable):
        self.direction_callback = callback

    # ═══════════════════════════════════════════════════════════════════════════
    # START / STOP (UNCHANGED)
    # ═══════════════════════════════════════════════════════════════════════════

    def start(self):
        if self.is_active:
            print("⚠️ Controller already active")
            return
        with self.lock:
            self.is_active = True
            self.last_gesture = None
            self.current_gesture = None
            self.last_direction = Direction.NONE
            self.current_direction = Direction.NONE
            self.gesture_history.clear()
        print(f"▶️ Game Controller STARTED")
        print(f"   Mode: {self.control_mode}")
        print(f"   Preset: {self.current_preset.name}")

    def stop(self):
        if not self.is_active:
            return
        with self.lock:
            self.is_active = False
            self._release_all_keys()
            self.last_gesture = None
            self.current_gesture = None
            self.held_gesture = None
            self.last_direction = Direction.NONE
            self.current_direction = Direction.NONE
        print("⏹ Game Controller STOPPED")

    # ═══════════════════════════════════════════════════════════════════════════
    # GESTURE HANDLING (FIXED - uses KeySimulator)
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_game_action(self, gesture_name: str):
        if not self.is_active or gesture_name is None:
            return
        
        current_time = time.time()
        gesture_name = gesture_name.upper()
        self.current_gesture = gesture_name
        
        if gesture_name == self.last_gesture:
            if current_time - self.last_gesture_time < self.gesture_cooldown:
                if self.control_mode == "EXTERNAL":
                    self._maintain_hold_gesture(gesture_name)
                return
        
        self.last_gesture = gesture_name
        self.last_gesture_time = current_time
        self.gesture_history.append((gesture_name, current_time))
        
        if self.control_mode == "INTERNAL":
            self._handle_internal_gesture(gesture_name)
        else:
            self._handle_external_gesture(gesture_name)

    def release_gesture(self):
        if not self.is_active:
            return
        self.current_gesture = None
        if self.control_mode == "EXTERNAL":
            self._release_hold_gesture()

    def _handle_internal_gesture(self, gesture_name: str):
        if self.game_callback:
            try:
                self.game_callback(gesture_name)
                print(f"🎮 Internal: {gesture_name}")
            except Exception as e:
                print(f"⚠️ Game callback error: {e}")

    def _handle_external_gesture(self, gesture_name: str):
        """
        FIXED: Convert gesture to keyboard/mouse action
        Uses KeySimulator (keyboard lib → ctypes → pyautogui fallback)
        """
        if gesture_name not in self.current_preset.gestures:
            print(f"⚠️ Gesture '{gesture_name}' not mapped in preset")
            return
        
        key, action_type, description = self.current_preset.gestures[gesture_name]
        
        try:
            if action_type == ActionType.KEY_TAP:
                if key:
                    success = key_sim.press_key(key)
                    if success:
                        print(f"⌨️ {gesture_name} → [{key}] ({description})")
                    else:
                        print(f"❌ {gesture_name} → [{key}] FAILED")
            
            elif action_type == ActionType.KEY_HOLD:
                if key:
                    self._start_hold_gesture(gesture_name, key)
                    print(f"⌨️ {gesture_name} → HOLD [{key}] ({description})")
            
            elif action_type == ActionType.MOUSE_CLICK:
                success = key_sim.mouse_click("left")
                if success:
                    print(f"🖱️ {gesture_name} → LEFT CLICK ({description})")
            
            elif action_type == ActionType.MOUSE_RIGHT:
                success = key_sim.mouse_click("right")
                if success:
                    print(f"🖱️ {gesture_name} → RIGHT CLICK ({description})")
            
            elif action_type == ActionType.MOUSE_HOLD:
                if not self.mouse_held:
                    key_sim.mouse_down("left")
                    self.mouse_held = True
                    print(f"🖱️ {gesture_name} → HOLD MOUSE ({description})")
            
            elif action_type == ActionType.KEY_COMBO:
                if isinstance(key, (list, tuple)):
                    for k in key:
                        key_sim.press_key(k)
                        time.sleep(0.02)
                    print(f"⌨️ {gesture_name} → COMBO {key} ({description})")
                    
        except Exception as e:
            print(f"⚠️ External gesture error: {e}")

    def _start_hold_gesture(self, gesture_name: str, key: str):
        """FIXED: Start holding a key using KeySimulator"""
        self._release_hold_gesture()
        try:
            key_sim.hold_key(key)
            self.held_gesture = gesture_name
            self.gesture_hold_key = key
            self.held_keys.add(key)
        except Exception as e:
            print(f"⚠️ Key hold error: {e}")

    def _maintain_hold_gesture(self, gesture_name: str):
        pass

    def _release_hold_gesture(self):
        """FIXED: Release held gesture key using KeySimulator"""
        if self.gesture_hold_key:
            try:
                key_sim.release_key(self.gesture_hold_key)
                self.held_keys.discard(self.gesture_hold_key)
            except:
                pass
        
        self.held_gesture = None
        self.gesture_hold_key = None
        
        if self.mouse_held:
            try:
                key_sim.mouse_up("left")
            except:
                pass
            self.mouse_held = False

    # ═══════════════════════════════════════════════════════════════════════════
    # DIRECTION HANDLING (FIXED - uses KeySimulator)
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_direction(self, direction):
        if not self.is_active:
            return
        
        if isinstance(direction, str):
            try:
                direction = Direction[direction.upper()]
            except (KeyError, AttributeError):
                direction = Direction.NONE
        elif not isinstance(direction, Direction):
            if hasattr(direction, 'value'):
                pass
            else:
                direction = Direction.NONE
        
        self.current_direction = direction
        
        current_time = time.time()
        if current_time - self.last_direction_time < self.direction_cooldown:
            if self.control_mode == "EXTERNAL" and self.continuous_direction:
                self._update_direction_key(direction)
            return
        
        self.last_direction_time = current_time
        
        if self.control_mode == "INTERNAL":
            self._handle_internal_direction(direction)
        else:
            self._handle_external_direction(direction)
        
        self.last_direction = direction

    def _handle_internal_direction(self, direction: Direction):
        if self.direction_callback:
            try:
                self.direction_callback(direction)
            except Exception as e:
                print(f"⚠️ Direction callback error: {e}")

    def _handle_external_direction(self, direction: Direction):
        self._update_direction_key(direction)

    def _update_direction_key(self, direction: Direction):
        """FIXED: Update direction keys using KeySimulator"""
        preset = self.current_preset
        
        dir_keys = {
            Direction.UP: preset.up,
            Direction.DOWN: preset.down,
            Direction.LEFT: preset.left,
            Direction.RIGHT: preset.right,
            Direction.NONE: None,
            Direction.UP_LEFT: (preset.up, preset.left),
            Direction.UP_RIGHT: (preset.up, preset.right),
            Direction.DOWN_LEFT: (preset.down, preset.left),
            Direction.DOWN_RIGHT: (preset.down, preset.right),
        }
        
        new_key = dir_keys.get(direction)
        
        try:
            if self.continuous_direction:
                if isinstance(new_key, tuple):
                    # Diagonal: release keys not in new combo
                    if self.current_direction_key:
                        if self.current_direction_key not in new_key:
                            key_sim.release_key(self.current_direction_key)
                            self.held_keys.discard(self.current_direction_key)
                    
                    for k in new_key:
                        if k not in self.held_keys:
                            key_sim.hold_key(k)
                            self.held_keys.add(k)
                    
                    self.current_direction_key = None
                    print(f"⌨️ Holding: [{new_key[0]}+{new_key[1]}] ({direction.value})")
                
                else:
                    # Single direction
                    for k in [preset.up, preset.down, preset.left, preset.right]:
                        if k in self.held_keys and k != new_key:
                            key_sim.release_key(k)
                            self.held_keys.discard(k)
                    
                    if self.current_direction_key and self.current_direction_key != new_key:
                        key_sim.release_key(self.current_direction_key)
                        self.held_keys.discard(self.current_direction_key)
                        self.current_direction_key = None
                    
                    if new_key and new_key != self.current_direction_key:
                        key_sim.hold_key(new_key)
                        self.held_keys.add(new_key)
                        self.current_direction_key = new_key
                        print(f"⌨️ Holding: [{new_key}] ({direction.value})")
                    
                    if direction == Direction.NONE and self.current_direction_key:
                        key_sim.release_key(self.current_direction_key)
                        self.held_keys.discard(self.current_direction_key)
                        self.current_direction_key = None
            
            else:
                if new_key and direction != self.last_direction:
                    if isinstance(new_key, tuple):
                        for k in new_key:
                            key_sim.press_key(k)
                    else:
                        key_sim.press_key(new_key)
                    print(f"⌨️ Tap: [{new_key}] ({direction.value})")
                    
        except Exception as e:
            print(f"⚠️ External direction error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # KEY MANAGEMENT (FIXED - uses KeySimulator)
    # ═══════════════════════════════════════════════════════════════════════════

    def _release_all_keys(self):
        """FIXED: Release all keys using KeySimulator"""
        try:
            for key in list(self.held_keys):
                try:
                    key_sim.release_key(key)
                except:
                    pass
            
            if self.mouse_held:
                try:
                    key_sim.mouse_up("left")
                except:
                    pass
                self.mouse_held = False
            
            if self.mouse_right_held:
                try:
                    key_sim.mouse_up("right")
                except:
                    pass
                self.mouse_right_held = False
            
            self.held_keys.clear()
            self.current_direction_key = None
            self.gesture_hold_key = None
            self.held_gesture = None
            
            print("⌨️ Released all keys")
                
        except Exception as e:
            print(f"⚠️ Release all keys error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION (UNCHANGED)
    # ═══════════════════════════════════════════════════════════════════════════

    def set_gesture_mapping(self, gesture: str, key: str, action_type: ActionType = ActionType.KEY_TAP, description: str = ""):
        gesture = gesture.upper()
        self.current_preset.gestures[gesture] = (key, action_type, description or gesture)
        print(f"🔧 Gesture mapping: {gesture} → [{key}] ({action_type.value})")

    def set_direction_key(self, direction: str, key: str):
        direction = direction.upper()
        if direction == "UP":
            self.current_preset.up = key
        elif direction == "DOWN":
            self.current_preset.down = key
        elif direction == "LEFT":
            self.current_preset.left = key
        elif direction == "RIGHT":
            self.current_preset.right = key
        else:
            print(f"⚠️ Invalid direction: {direction}")
            return
        print(f"🔧 Direction mapping: {direction} → [{key}]")

    def set_continuous_mode(self, enabled: bool):
        if not enabled:
            self._release_all_keys()
        self.continuous_direction = enabled
        print(f"🔧 Continuous direction: {'ON' if enabled else 'OFF'}")

    def set_gesture_cooldown(self, seconds: float):
        self.gesture_cooldown = max(0.05, seconds)
        print(f"🔧 Gesture cooldown: {self.gesture_cooldown}s")

    # ═══════════════════════════════════════════════════════════════════════════
    # STATUS / INFO (UNCHANGED)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_status(self) -> dict:
        return {
            'active': self.is_active,
            'mode': self.control_mode,
            'preset': self.preset_name,
            'preset_name': self.current_preset.name,
            'current_gesture': self.current_gesture,
            'last_gesture': self.last_gesture,
            'current_direction': self.current_direction.value if self.current_direction else "NONE",
            'held_keys': list(self.held_keys),
            'held_gesture': self.held_gesture,
            'continuous': self.continuous_direction,
            'keyboard_available': KEYBOARD_AVAILABLE,
            'ctypes_available': CTYPES_AVAILABLE,
            'pyautogui_available': PYAUTOGUI_AVAILABLE,
        }

    def get_key_mappings(self) -> dict:
        preset = self.current_preset
        gesture_display = {}
        for gesture, (key, action_type, desc) in preset.gestures.items():
            if key is None:
                if action_type == ActionType.MOUSE_CLICK:
                    key_str = "🖱️ Click"
                elif action_type == ActionType.MOUSE_RIGHT:
                    key_str = "🖱️ Right"
                else:
                    key_str = "None"
            else:
                key_str = key.upper() if len(key) == 1 else key.title()
            gesture_display[gesture] = f"{key_str} ({desc})"
        
        return {
            'preset': preset.name,
            'directions': {
                'UP': preset.up.upper() if len(preset.up) == 1 else preset.up.title(),
                'DOWN': preset.down.upper() if len(preset.down) == 1 else preset.down.title(),
                'LEFT': preset.left.upper() if len(preset.left) == 1 else preset.left.title(),
                'RIGHT': preset.right.upper() if len(preset.right) == 1 else preset.right.title(),
            },
            'gestures': gesture_display
        }

    def print_mappings(self):
        mappings = self.get_key_mappings()
        print("\n" + "═" * 50)
        print(f"🎮 CURRENT MAPPINGS: {mappings['preset']}")
        print("═" * 50)
        print("\n📍 DIRECTIONS:")
        for direction, key in mappings['directions'].items():
            print(f"   {direction:8} → [{key}]")
        print("\n✊ GESTURES:")
        for gesture, action in mappings['gestures'].items():
            print(f"   {gesture:12} → {action}")
        print("═" * 50 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

game_controller = GameGestureController()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def start_external_control(preset: str = "default") -> GameGestureController:
    game_controller.set_preset(preset)
    game_controller.set_control_mode("EXTERNAL")
    game_controller.start()
    game_controller.print_mappings()
    return game_controller

def stop_control():
    game_controller.stop()

def list_presets():
    print("\n" + "═" * 50)
    print("🎮 AVAILABLE GAME PRESETS")
    print("═" * 50)
    for name, preset in GAME_PRESETS.items():
        print(f"\n  📌 {name}")
        print(f"     {preset.name}")
        print(f"     {preset.description}")
    print("\n" + "═" * 50 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("🎮 GAME GESTURE CONTROLLER - FIXED VERSION TEST")
    print("=" * 60)
    
    print(f"\n📊 CAPABILITY CHECK:")
    print(f"   keyboard library: {'✅' if KEYBOARD_AVAILABLE else '❌'}")
    print(f"   ctypes SendInput: {'✅' if CTYPES_AVAILABLE else '❌'}")
    print(f"   PyAutoGUI:        {'✅' if PYAUTOGUI_AVAILABLE else '❌'}")
    
    list_presets()
    game_controller.print_mappings()
    
    # Test INTERNAL mode
    print("\n" + "─" * 60)
    print("📌 TESTING INTERNAL MODE")
    print("─" * 60)
    
    game_controller.set_control_mode("INTERNAL")
    
    def test_gesture_callback(gesture):
        print(f"   ✅ Internal received gesture: {gesture}")
    
    def test_direction_callback(direction):
        print(f"   ✅ Internal received direction: {direction.value}")
    
    game_controller.set_game_callback(test_gesture_callback)
    game_controller.set_direction_callback(test_direction_callback)
    game_controller.start()
    
    print("\nTesting gestures...")
    for gesture in ["FIST", "PALM", "POINT", "PEACE", "ROCK"]:
        game_controller.execute_game_action(gesture)
        time.sleep(0.25)
    
    print("\nTesting directions...")
    for direction in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.NONE]:
        game_controller.handle_direction(direction)
        time.sleep(0.25)
    
    game_controller.stop()
    
    # Test EXTERNAL mode
    print("\n" + "─" * 60)
    print("📌 TESTING EXTERNAL MODE")
    print("─" * 60)
    
    if KEYBOARD_AVAILABLE or CTYPES_AVAILABLE:
        print("\n⚠️  WARNING: This will simulate keyboard presses!")
        print("   Open a text editor (Notepad) to see the output.")
        print("   Press Ctrl+C to cancel.\n")
        
        response = input("   Continue with external test? (y/n): ").strip().lower()
        
        if response == 'y':
            print("\n   Starting in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            game_controller.set_preset("default")
            game_controller.set_control_mode("EXTERNAL")
            game_controller.start()
            
            print("\n✅ Testing gesture key presses:")
            game_controller.execute_game_action("FIST")
            time.sleep(0.5)
            game_controller.execute_game_action("POINT")
            time.sleep(0.5)
            
            print("\n✅ Testing direction HOLD:")
            game_controller.handle_direction(Direction.UP)
            time.sleep(1)
            game_controller.handle_direction(Direction.RIGHT)
            time.sleep(1)
            game_controller.handle_direction(Direction.NONE)
            
            game_controller.stop()
            print("\n✅ External mode test complete!")
        else:
            print("   Skipped external test.")
    else:
        print("\n⚠️  No key simulation available!")
        print("   Install: pip install keyboard")
    
    # Final status
    print("\n" + "=" * 60)
    print("📊 FINAL STATUS")
    print("=" * 60)
    
    status = game_controller.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60 + "\n")