"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🔍 SMOOTH ZOOM CONTROLLER                            ║
║                    ✅ Logarithmic Scaling + Lock Feature                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
from enum import Enum, auto

from PySide6.QtCore import QObject, QTimer, Signal


# ═══════════════════════════════════════════════════════════════════════════════
#                         🔒 ZOOM LOCK STATE
# ═══════════════════════════════════════════════════════════════════════════════

class ZoomLockState(Enum):
    """Zoom lock states"""
    UNLOCKED = auto()
    LOCKED = auto()


# ═══════════════════════════════════════════════════════════════════════════════
#                         🔍 SMOOTH ZOOM CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class SmoothZoomController(QObject):
    """
    Handles smooth zoom with:
    ✅ Logarithmic scaling for natural feel
    ✅ FIST GESTURE = LOCK/UNLOCK zoom
    ✅ Visual feedback for lock state
    
    Usage:
        controller = SmoothZoomController()
        controller.zoom_changed.connect(on_zoom_changed)
        controller.lock_changed.connect(on_lock_changed)
        
        # Zoom operations
        controller.zoom_in()
        controller.zoom_out()
        controller.set_target_zoom(2.0)
        
        # Lock operations
        controller.toggle_lock()  # Fist gesture
        
        # Pinch zoom
        controller.start_pinch(distance)
        controller.update_pinch(new_distance)
        controller.end_pinch()
    """
    
    # Signals
    zoom_changed = Signal(float)
    lock_changed = Signal(bool)  # Emitted when lock state changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_zoom = 1.0
        self._target_zoom = 1.0
        self._min_zoom = 0.25
        self._max_zoom = 5.0
        
        # ═══════════════════════════════════════════════════════════════════
        # ZOOM LOCK STATE
        # ═══════════════════════════════════════════════════════════════════
        self._lock_state = ZoomLockState.UNLOCKED
        self._locked_zoom_value = 1.0  # Zoom value when locked
        
        # Animation timer
        self._zoom_timer = QTimer(self)
        self._zoom_timer.timeout.connect(self._animate_zoom)
        self._zoom_timer.setInterval(16)  # ~60 FPS
        
        # Pinch tracking
        self._pinch_start_distance = None
        self._pinch_start_zoom = 1.0
        
        # ═══════════════════════════════════════════════════════════════════
        # Logarithmic zoom parameters
        # ═══════════════════════════════════════════════════════════════════
        self._smoothing = 0.12          # Animation smoothing
        self._pinch_sensitivity = 0.25  # REDUCED - much slower pinch response
        self._button_zoom_factor = 1.1  # 10% per button click
        self._log_base = 2.0            # Logarithmic base for scaling
        
        self._destroyed = False
    
    def cleanup(self):
        """Clean up resources"""
        self._destroyed = True
        try:
            if self._zoom_timer:
                self._zoom_timer.stop()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🔒 ZOOM LOCK METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def is_locked(self) -> bool:
        """Check if zoom is locked"""
        return self._lock_state == ZoomLockState.LOCKED
    
    def toggle_lock(self) -> bool:
        """
        Toggle zoom lock state.
        When locked, zoom freezes at current value.
        
        Returns:
            New lock state (True = locked)
        """
        if self._destroyed:
            return False
        
        if self._lock_state == ZoomLockState.UNLOCKED:
            # LOCK at current zoom
            self._lock_state = ZoomLockState.LOCKED
            self._locked_zoom_value = self._current_zoom
            print(f"🔒 Zoom LOCKED at {self._current_zoom:.0%}")
        else:
            # UNLOCK
            self._lock_state = ZoomLockState.UNLOCKED
            print(f"🔓 Zoom UNLOCKED")
        
        self.lock_changed.emit(self.is_locked)
        return self.is_locked
    
    def lock_zoom(self):
        """Force lock zoom at current level"""
        if self._lock_state != ZoomLockState.LOCKED:
            self.toggle_lock()
    
    def unlock_zoom(self):
        """Force unlock zoom"""
        if self._lock_state == ZoomLockState.LOCKED:
            self.toggle_lock()
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         📊 ZOOM PROPERTIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def current_zoom(self) -> float:
        """Get current zoom level"""
        return self._current_zoom
    
    @property
    def target_zoom(self) -> float:
        """Get target zoom level"""
        return self._target_zoom
    
    @property
    def locked_zoom(self) -> float:
        """Get the zoom value that was locked"""
        return self._locked_zoom_value
    
    @property
    def min_zoom(self) -> float:
        """Get minimum zoom level"""
        return self._min_zoom
    
    @property
    def max_zoom(self) -> float:
        """Get maximum zoom level"""
        return self._max_zoom
    
    def set_zoom_limits(self, min_zoom: float, max_zoom: float):
        """
        Set zoom limits.
        
        Args:
            min_zoom: Minimum zoom level (e.g., 0.25)
            max_zoom: Maximum zoom level (e.g., 5.0)
        """
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🔍 ZOOM OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_target_zoom(self, zoom: float, immediate: bool = False):
        """
        Set target zoom level - BLOCKED if locked.
        
        Args:
            zoom: Target zoom level
            immediate: If True, apply zoom immediately without animation
        """
        if self._destroyed:
            return
        
        # LOCK CHECK: If locked, ignore zoom changes
        if self._lock_state == ZoomLockState.LOCKED:
            return  # Silently ignore
        
        zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        self._target_zoom = zoom
        
        if immediate:
            self._current_zoom = zoom
            self.zoom_changed.emit(self._current_zoom)
        else:
            if not self._zoom_timer.isActive():
                self._zoom_timer.start()
    
    def zoom_in(self, factor: float = None):
        """
        Zoom in - BLOCKED if locked.
        
        Args:
            factor: Zoom factor (default: 1.1 = 10% increase)
        """
        if self._lock_state == ZoomLockState.LOCKED:
            return
        if factor is None:
            factor = self._button_zoom_factor
        self.set_target_zoom(self._target_zoom * factor)
    
    def zoom_out(self, factor: float = None):
        """
        Zoom out - BLOCKED if locked.
        
        Args:
            factor: Zoom factor (default: 1.1 = 10% decrease)
        """
        if self._lock_state == ZoomLockState.LOCKED:
            return
        if factor is None:
            factor = self._button_zoom_factor
        self.set_target_zoom(self._target_zoom / factor)
    
    def reset_zoom(self):
        """Reset zoom to 100% - ALSO UNLOCKS"""
        self._lock_state = ZoomLockState.UNLOCKED
        self.lock_changed.emit(False)
        self.set_target_zoom(1.0)
    
    def _animate_zoom(self):
        """Animate zoom towards target"""
        if self._destroyed:
            return
        
        try:
            diff = self._target_zoom - self._current_zoom
            
            if abs(diff) < 0.001:
                self._current_zoom = self._target_zoom
                self._zoom_timer.stop()
            else:
                # Smooth easing
                self._current_zoom += diff * self._smoothing
            
            self.zoom_changed.emit(self._current_zoom)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🤏 PINCH ZOOM METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_pinch(self, distance: float):
        """
        Start pinch gesture - BLOCKED if locked.
        
        Args:
            distance: Initial distance between fingers
        """
        if self._destroyed or self._lock_state == ZoomLockState.LOCKED:
            return
        
        self._pinch_start_distance = distance
        self._pinch_start_zoom = self._current_zoom
        print(f"🤏 Pinch started - Distance: {distance:.1f}, Zoom: {self._current_zoom:.2f}")
    
    def update_pinch(self, current_distance: float):
        """
        Update pinch with LOGARITHMIC scaling - BLOCKED if locked.
        
        Args:
            current_distance: Current distance between fingers
        """
        if self._destroyed or self._pinch_start_distance is None:
            return
        
        if self._lock_state == ZoomLockState.LOCKED:
            return
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # Logarithmic scaling for natural zoom feel
            # ═══════════════════════════════════════════════════════════════
            ratio = current_distance / self._pinch_start_distance
            
            # Apply logarithmic scaling
            if ratio > 0:
                log_scale = math.log(ratio, self._log_base) * self._pinch_sensitivity
                adjusted_scale = math.pow(self._log_base, log_scale)
            else:
                adjusted_scale = 1.0
            
            new_zoom = self._pinch_start_zoom * adjusted_scale
            new_zoom = max(self._min_zoom, min(self._max_zoom, new_zoom))
            
            self._target_zoom = new_zoom
            
            if not self._zoom_timer.isActive():
                self._zoom_timer.start()
            
        except Exception as e:
            print(f"Pinch update error: {e}")
    
    def end_pinch(self):
        """End pinch gesture"""
        if self._destroyed:
            return
        
        print(f"🤏 Pinch ended - Final zoom: {self._current_zoom:.2f}")
        self._pinch_start_distance = None
        self._pinch_start_zoom = self._current_zoom
    
    def handle_pinch_delta(self, scale_delta: float):
        """
        Handle incremental pinch scale delta - BLOCKED if locked.
        
        Args:
            scale_delta: Scale factor (>1 = zoom in, <1 = zoom out)
        """
        if self._destroyed or self._lock_state == ZoomLockState.LOCKED:
            return
        
        try:
            # Logarithmic delta scaling
            if scale_delta > 0:
                log_delta = math.log(scale_delta, self._log_base) * self._pinch_sensitivity
                factor = math.pow(self._log_base, log_delta)
            else:
                factor = 1.0
            
            # Limit change per frame
            factor = max(0.95, min(1.05, factor))  # Max 5% change per update
            
            new_zoom = self._current_zoom * factor
            self.set_target_zoom(new_zoom)
            
        except Exception as e:
            print(f"Pinch delta error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         ⚙️ CONFIGURATION METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_smoothing(self, smoothing: float):
        """
        Set animation smoothing factor.
        
        Args:
            smoothing: 0.05 (very smooth) to 0.3 (snappy)
        """
        self._smoothing = max(0.05, min(0.3, smoothing))
    
    def set_pinch_sensitivity(self, sensitivity: float):
        """
        Set pinch zoom sensitivity.
        
        Args:
            sensitivity: 0.1 (less sensitive) to 0.5 (more sensitive)
        """
        self._pinch_sensitivity = max(0.1, min(0.5, sensitivity))
    
    def set_button_zoom_factor(self, factor: float):
        """
        Set zoom factor for button clicks.
        
        Args:
            factor: 1.05 (5% per click) to 1.3 (30% per click)
        """
        self._button_zoom_factor = max(1.05, min(1.3, factor))
    
    def get_zoom_percentage(self) -> int:
        """Get current zoom as percentage"""
        return int(self._current_zoom * 100)
    
    def get_status(self) -> str:
        """Get current status string"""
        lock_str = "🔒 LOCKED" if self.is_locked else "🔓 Unlocked"
        return f"Zoom: {self.get_zoom_percentage()}% | {lock_str}"