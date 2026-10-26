"""
Base Mode - Abstract base class
"""

from abc import ABC, abstractmethod
import math
import config


class BaseMode(ABC):
    """Abstract base class for tracking modes"""
    
    def __init__(self, state, hud):
        self.state = state
        self.hud = hud
        self.active = False
    
    @abstractmethod
    def process(self, landmarks, fingers, frame, handed):
        """Process frame in this mode"""
        pass
    
    @abstractmethod
    def reset(self):
        """Reset mode state"""
        pass
    
    @abstractmethod
    def activate(self):
        """Called when mode becomes active"""
        pass
    
    @abstractmethod
    def deactivate(self):
        """Called when mode becomes inactive"""
        pass
    
    def get_screen_coords(self, index_lm):
        """Convert landmark to screen coordinates"""
        mx = getattr(config, 'tracking_margin_x', 0.15)
        mt = getattr(config, 'tracking_margin_top', 0.15)
        mb = getattr(config, 'tracking_margin_bottom', 0.80)
        
        hx, hy = index_lm.x, index_lm.y
        if getattr(config, 'left_handed_mode', False):
            hx = 1.0 - hx
        
        nx = max(0, min(1, (hx - mx) / (1 - 2 * mx)))
        ny = max(0, min(1, (hy - mt) / (mb - mt)))
        
        return int(nx * self.state.SCREEN_W), int(ny * self.state.SCREEN_H)
    
    def get_gesture(self, fingers, lm):
        """Basic gesture detection"""
        i, m, r, p, t = fingers[1], fingers[2], fingers[3], fingers[4], fingers[0]
        n = sum(fingers)
        
        if i and not m and not r and not p:
            return "MOVE"
        if i and m and not r and not p:
            return "SCROLL"
        if n == 0:
            return "FIST"
        if i and m and r and not p:
            return "DRAG"
        if n == 5:
            return "OPEN"
        return "NONE"