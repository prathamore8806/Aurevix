# auto_capture.py - Multiple capture modes (Manual, Stability, Countdown)
import time
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, List


class CaptureMode(Enum):
    """Auto-capture modes"""
    MANUAL = "manual"              # Button click only
    STABILITY = "stability"         # Auto when stable
    COUNTDOWN = "countdown"         # Countdown when stable


@dataclass
class CaptureConfig:
    """Configuration for auto-capture system"""
    mode: CaptureMode = CaptureMode.COUNTDOWN
    stability_required: float = 90.0      # Percentage
    countdown_seconds: int = 3
    hold_time: float = 1.5                 # Seconds for stability mode
    target_tolerance: float = 50.0         # Pixels from target


@dataclass
class CaptureResult:
    """Result from capture update"""
    should_capture: bool = False
    countdown: Optional[int] = None
    progress: float = 0.0
    status: str = "waiting"
    message: str = ""
    in_target_zone: bool = False


class AutoCaptureSystem:
    """Auto-capture with multiple modes"""
    
    def __init__(self, config: CaptureConfig = None):
        self.config = config or CaptureConfig()
        
        # State
        self.countdown_active = False
        self.countdown_start = 0.0
        self.countdown_value = 0
        self.stable_start_time = None
        self.last_capture_time = 0.0
        self.capture_cooldown = 0.8
        
        # Callbacks
        self.on_capture: Optional[Callable] = None
        self.on_countdown_tick: Optional[Callable[[int], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        
        # Stats
        self.capture_count = 0
        
    def set_mode(self, mode: CaptureMode):
        """Change capture mode"""
        self.config.mode = mode
        self.reset()
        
    def set_config(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.reset()
        
    def reset(self):
        """Reset capture state"""
        self.countdown_active = False
        self.countdown_start = 0.0
        self.countdown_value = 0
        self.stable_start_time = None
        
    def update(self, stability: float, hand_detected: bool, 
               finger_pos: tuple = None, target_pos: tuple = None) -> CaptureResult:
        """
        Update capture system.
        
        Args:
            stability: Stability percentage (0-100)
            hand_detected: Whether hand is detected
            finger_pos: Current finger position (x, y)
            target_pos: Current target position (x, y)
            
        Returns:
            CaptureResult with status
        """
        current_time = time.time()
        result = CaptureResult()
        
        # Check cooldown
        if current_time - self.last_capture_time < self.capture_cooldown:
            result.status = "cooldown"
            result.message = "Please wait..."
            remaining = self.capture_cooldown - (current_time - self.last_capture_time)
            result.progress = (1 - remaining / self.capture_cooldown) * 100
            return result
        
        # Check hand detection
        if not hand_detected:
            self.reset()
            result.status = "no_hand"
            result.message = "Show your hand"
            return result
        
        # Check if in target zone
        in_zone = False
        if finger_pos and target_pos:
            distance = math.sqrt(
                (finger_pos[0] - target_pos[0])**2 + 
                (finger_pos[1] - target_pos[1])**2
            )
            in_zone = distance < self.config.target_tolerance
            result.in_target_zone = in_zone
        
        if not in_zone:
            self.reset()
            result.status = "move_to_target"
            result.message = "Move to target"
            return result
        
        # Handle based on mode
        if self.config.mode == CaptureMode.MANUAL:
            result = self._handle_manual(stability)
            
        elif self.config.mode == CaptureMode.STABILITY:
            result = self._handle_stability(stability, current_time)
            
        elif self.config.mode == CaptureMode.COUNTDOWN:
            result = self._handle_countdown(stability, current_time)
        
        result.in_target_zone = in_zone
        
        # Handle capture
        if result.should_capture:
            self._do_capture(current_time)
            
        return result
    
    def _handle_manual(self, stability: float) -> CaptureResult:
        """Manual mode - wait for button click"""
        result = CaptureResult()
        result.status = "ready"
        result.message = "Press 'Capture' button"
        result.progress = stability
        return result
    
    def _handle_stability(self, stability: float, current_time: float) -> CaptureResult:
        """Auto capture when stable for required duration"""
        result = CaptureResult()
        
        if stability >= self.config.stability_required:
            if self.stable_start_time is None:
                self.stable_start_time = current_time
                
            elapsed = current_time - self.stable_start_time
            progress = min(100, (elapsed / self.config.hold_time) * 100)
            
            result.progress = progress
            result.status = "holding"
            result.message = f"Hold steady... {int(progress)}%"
            
            if elapsed >= self.config.hold_time:
                result.should_capture = True
                result.status = "captured"
                result.message = "Captured!"
                result.progress = 100
        else:
            self.stable_start_time = None
            result.status = "stabilizing"
            result.message = f"Stabilize: {int(stability)}%"
            result.progress = stability
            
        return result
    
    def _handle_countdown(self, stability: float, current_time: float) -> CaptureResult:
        """Countdown when stable"""
        result = CaptureResult()
        
        if stability >= self.config.stability_required:
            if not self.countdown_active:
                # Start countdown
                self.countdown_active = True
                self.countdown_start = current_time
                self.countdown_value = self.config.countdown_seconds
                
                # Initial tick callback
                if self.on_countdown_tick:
                    self.on_countdown_tick(self.countdown_value)
                
            elapsed = current_time - self.countdown_start
            remaining = self.config.countdown_seconds - elapsed
            
            if remaining <= 0:
                result.should_capture = True
                result.countdown = 0
                result.status = "captured"
                result.message = "📸 Captured!"
                result.progress = 100
            else:
                new_value = int(math.ceil(remaining))
                
                if new_value != self.countdown_value:
                    self.countdown_value = new_value
                    if self.on_countdown_tick:
                        self.on_countdown_tick(new_value)
                        
                result.countdown = new_value
                result.progress = ((self.config.countdown_seconds - remaining) / 
                                  self.config.countdown_seconds) * 100
                result.status = "countdown"
                result.message = str(new_value)
        else:
            # Lost stability
            was_active = self.countdown_active
            self.countdown_active = False
            self.countdown_value = 0
            
            if was_active:
                result.message = "Hold still!"
            else:
                result.message = f"Stabilize: {int(stability)}%"
                
            result.status = "stabilizing"
            result.progress = stability
            
        return result
    
    def _do_capture(self, current_time: float):
        """Execute capture"""
        self.last_capture_time = current_time
        self.capture_count += 1
        self.reset()
        
        if self.on_capture:
            self.on_capture()
            
        if self.on_status_change:
            self.on_status_change("captured")
    
    def force_capture(self) -> CaptureResult:
        """Manual capture override"""
        result = CaptureResult()
        result.should_capture = True
        result.progress = 100
        result.status = "captured"
        result.message = "Captured!"
        
        self._do_capture(time.time())
        return result
    
    def get_mode_name(self) -> str:
        """Get human-readable mode name"""
        names = {
            CaptureMode.MANUAL: "Manual",
            CaptureMode.STABILITY: "Auto (Stability)",
            CaptureMode.COUNTDOWN: "Auto (Countdown)"
        }
        return names.get(self.config.mode, "Unknown")
