"""
Global State Manager
"""

import time
import gc
import pyautogui
from collections import deque

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class TrackerState:
    """Centralized state management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Screen
        self.SCREEN_W, self.SCREEN_H = pyautogui.size()
        self.CAM_W, self.CAM_H = 640, 480
        
        # Click state
        self.click_ready = True
        self.click_cooldown_time = 0
        self.CLICK_COOLDOWN = 0.4
        self.rclick_ready = True
        self.rclick_cooldown_time = 0
        
        # Scroll
        self.prev_scroll_y = None
        
        # Drag
        self.click_held = False
        
        # Gesture
        self.last_gesture_time = 0
        self.COOLDOWN = 0.6
        self.prev_fingers = [False] * 5
        
        # Gaming
        self.last_gaming_gesture = None
        self.last_gaming_time = 0
        self.GAMING_COOLDOWN = 0.35
        self.current_zone = "CENTER"
        self.gaming_gesture_flash_time = 0
        self.zone_history = deque(maxlen=5)
        self.last_confirmed_zone = "CENTER"
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        
        # Position
        self.last_index_pos = (0.5, 0.5)
        
        # Action feedback
        self.action_feedback = {"text": "", "color": None, "time": 0}
        
        # Control
        self.running = True
        self.camera_enabled = False
        self.gesture_enabled = False
        
        # GUI
        self.gui = None
        
        # Cleanup tracking
        self.frame_count = 0
        self.last_gc_time = time.time()
        self.GC_INTERVAL = 30.0  # GC every 30 seconds
    
    def reset(self):
        """Reset all state"""
        self.click_ready = True
        self.rclick_ready = True
        self.click_held = False
        self.prev_scroll_y = None
        self.last_gesture_time = 0
        self.prev_fingers = [False] * 5
        
        self.last_gaming_gesture = None
        self.last_gaming_time = 0
        self.current_zone = "CENTER"
        self.gaming_gesture_flash_time = 0
        self.zone_history.clear()
        self.last_confirmed_zone = "CENTER"
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        
        self.last_index_pos = (0.5, 0.5)
        
        try:
            pyautogui.mouseUp(_pause=False)
            pyautogui.keyUp('shift', _pause=False)
        except:
            pass
    
    def tick(self):
        """Called every frame"""
        self.frame_count += 1
        now = time.time()
        
        # Periodic GC
        if now - self.last_gc_time > self.GC_INTERVAL:
            gc.collect()
            self.last_gc_time = now
    
    def show_action(self, text, color=None, duration=0.5):
        self.action_feedback = {
            "text": text,
            "color": color,
            "time": time.time() + duration
        }
    
    def get_action_feedback(self):
        if time.time() < self.action_feedback["time"]:
            return self.action_feedback
        return None


# Global instance
state = TrackerState()