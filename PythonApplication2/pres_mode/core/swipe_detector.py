"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         👋 SWIPE GESTURE STATE MACHINE                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
from enum import Enum, auto
from collections import deque
from typing import Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
#                         📊 SWIPE STATE ENUM
# ═══════════════════════════════════════════════════════════════════════════════

class SwipeState(Enum):
    """States for swipe gesture detection"""
    IDLE = auto()
    TRACKING = auto()
    COOLDOWN = auto()


# ═══════════════════════════════════════════════════════════════════════════════
#                         👋 SWIPE DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class SwipeDetector:
    """
    FIXED: Proper state machine for swipe gesture detection.
    Tracks hand movement and detects left/right swipes reliably.
    
    Usage:
        detector = SwipeDetector()
        
        # In your hand tracking loop:
        swipe = detector.add_position(normalized_x, normalized_y)
        
        if swipe == "swipe_left":
            go_to_previous_slide()
        elif swipe == "swipe_right":
            go_to_next_slide()
    """
    
    def __init__(self):
        # State machine
        self.state = SwipeState.IDLE
        
        # Position tracking
        self.position_history: deque = deque(maxlen=25)  # ~0.8s at 30fps
        self.tracking_start_time: float = 0
        self.tracking_start_pos: Optional[Tuple[float, float]] = None
        
        # Tuned parameters for reliable detection
        self.min_swipe_distance = 0.12      # 12% of screen width
        self.max_swipe_time = 0.5           # 500ms max swipe duration
        self.min_swipe_time = 0.08          # 80ms min to avoid jitter
        self.y_tolerance = 0.15             # Allow 15% vertical deviation
        self.velocity_threshold = 0.3       # Min velocity (distance/time)
        
        # Cooldown
        self.cooldown_duration = 0.6        # 600ms between swipes
        self.cooldown_end_time: float = 0
        
        # Tracking threshold
        self.tracking_threshold = 0.03      # Start tracking after 3% movement
        
        # Debug
        self.debug = False
    
    def add_position(self, x: float, y: float) -> Optional[str]:
        """
        Process new hand position.
        
        Args:
            x: Normalized X (0=left, 1=right)
            y: Normalized Y (0=top, 1=bottom)
            
        Returns:
            "swipe_left", "swipe_right", or None
        """
        current_time = time.time()
        
        # Handle cooldown state
        if self.state == SwipeState.COOLDOWN:
            if current_time >= self.cooldown_end_time:
                self.state = SwipeState.IDLE
                self.position_history.clear()
                if self.debug:
                    print("  [Swipe] Cooldown ended, now IDLE")
            else:
                return None
        
        # Add position to history
        self.position_history.append((x, y, current_time))
        
        # State: IDLE - look for movement start
        if self.state == SwipeState.IDLE:
            if len(self.position_history) >= 3:
                # Check if hand started moving
                first_x, first_y, first_t = self.position_history[0]
                dx = abs(x - first_x)
                
                if dx >= self.tracking_threshold:
                    self.state = SwipeState.TRACKING
                    self.tracking_start_time = first_t
                    self.tracking_start_pos = (first_x, first_y)
                    if self.debug:
                        print(f"  [Swipe] Movement detected, now TRACKING from ({first_x:.2f}, {first_y:.2f})")
            return None
        
        # State: TRACKING - analyze swipe
        if self.state == SwipeState.TRACKING:
            return self._analyze_swipe(x, y, current_time)
        
        return None
    
    def _analyze_swipe(self, x: float, y: float, current_time: float) -> Optional[str]:
        """Analyze current tracking for swipe completion"""
        
        if self.tracking_start_pos is None:
            self.state = SwipeState.IDLE
            return None
        
        start_x, start_y = self.tracking_start_pos
        elapsed = current_time - self.tracking_start_time
        
        # Timeout check
        if elapsed > self.max_swipe_time:
            if self.debug:
                print(f"  [Swipe] Timeout ({elapsed:.2f}s), resetting")
            self._reset_tracking()
            return None
        
        # Calculate movement
        dx = x - start_x
        dy = y - start_y
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        # Check if swipe completed
        if abs_dx >= self.min_swipe_distance:
            # Validate timing
            if elapsed < self.min_swipe_time:
                return None  # Too fast, probably noise
            
            # Validate direction (horizontal dominance)
            if abs_dy > self.y_tolerance:
                if self.debug:
                    print(f"  [Swipe] Too much Y movement ({abs_dy:.2f}), resetting")
                self._reset_tracking()
                return None
            
            # Calculate velocity
            velocity = abs_dx / elapsed
            if velocity < self.velocity_threshold:
                if self.debug:
                    print(f"  [Swipe] Too slow ({velocity:.2f}), resetting")
                self._reset_tracking()
                return None
            
            # SWIPE DETECTED!
            direction = "swipe_right" if dx > 0 else "swipe_left"
            
            if self.debug:
                print(f"  [Swipe] ✓ DETECTED: {direction} (dx={dx:.2f}, time={elapsed:.2f}s, vel={velocity:.2f})")
            
            # Enter cooldown
            self.state = SwipeState.COOLDOWN
            self.cooldown_end_time = current_time + self.cooldown_duration
            self.position_history.clear()
            self.tracking_start_pos = None
            
            return direction
        
        return None
    
    def _reset_tracking(self):
        """Reset to idle state"""
        self.state = SwipeState.IDLE
        self.position_history.clear()
        self.tracking_start_pos = None
        self.tracking_start_time = 0
    
    def reset(self):
        """Full reset"""
        self._reset_tracking()
        self.cooldown_end_time = 0
    
    def get_state_info(self) -> str:
        """Get current state for debugging"""
        return f"State: {self.state.name}, History: {len(self.position_history)}"
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         ⚙️ CONFIGURATION METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_sensitivity(self, sensitivity: float):
        """
        Set swipe sensitivity.
        
        Args:
            sensitivity: 0.5 (less sensitive) to 2.0 (more sensitive)
        """
        sensitivity = max(0.5, min(2.0, sensitivity))
        
        # Adjust parameters based on sensitivity
        self.min_swipe_distance = 0.12 / sensitivity
        self.tracking_threshold = 0.03 / sensitivity
        self.velocity_threshold = 0.3 / sensitivity
    
    def set_cooldown(self, duration: float):
        """
        Set cooldown duration between swipes.
        
        Args:
            duration: Cooldown in seconds (0.3 to 2.0)
        """
        self.cooldown_duration = max(0.3, min(2.0, duration))
    
    def enable_debug(self, enabled: bool = True):
        """Enable or disable debug output"""
        self.debug = enabled