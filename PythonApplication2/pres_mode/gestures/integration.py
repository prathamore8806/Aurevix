"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🔌 GESTURE INTEGRATION HELPER                        ║
║                    Connect Hand Tracking to Presentation                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
from typing import Optional, Tuple, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from ..ui.viewer.presentation_viewer import PresentationViewer


class GestureIntegration(QObject):
    """
    Enhanced helper class for gesture recognition integration.
    
    FEATURES:
    - Hand position tracking for swipe detection
    - Automatic swipe gesture detection
    - Fist = Lock/Unlock zoom
    - Logarithmic pinch zoom
    
    USAGE WITH HAND TRACKING:
    ```python
    integration = GestureIntegration(viewer)
    
    # In your hand tracking loop:
    # Send continuous hand position for swipe detection
    integration.send_hand_position(normalized_x, normalized_y)
    
    # Send discrete gestures
    integration.send_gesture("fist")  # Lock zoom
    integration.send_gesture("open_palm")  # Reset
    
    # Send pinch updates
    integration.start_pinch((x1, y1), (x2, y2))
    integration.update_pinch((x1, y1), (x2, y2))
    integration.end_pinch()
    ```
    """
    
    # Signals
    gesture_detected = Signal(str)
    pinch_scale = Signal(float)
    pinch_start = Signal(float, float, float, float)
    pinch_distance = Signal(float)
    pinch_end = Signal()
    pointer_position = Signal(float, float)
    hand_position = Signal(float, float)  # For swipe detection
    
    def __init__(self, viewer: 'PresentationViewer' = None, parent=None):
        super().__init__(parent)
        
        self.viewer = viewer
        self._last_distance: Optional[float] = None
        self._is_pinching = False
        
        if viewer:
            self.connect_to_viewer(viewer)
    
    def connect_to_viewer(self, viewer: 'PresentationViewer'):
        """
        Connect all signals to viewer slots.
        
        Args:
            viewer: PresentationViewer instance to connect to
        """
        self.viewer = viewer
        
        try:
            self.gesture_detected.connect(viewer.handle_gesture)
            self.pinch_scale.connect(viewer.handle_pinch_scale)
            self.pinch_start.connect(viewer.handle_pinch_start)
            self.pinch_distance.connect(viewer.handle_pinch_distance)
            self.pinch_end.connect(viewer.handle_pinch_end)
            self.pointer_position.connect(viewer.update_pointer)
            self.hand_position.connect(viewer.handle_hand_position)
            print("✅ GestureIntegration connected to viewer")
        except Exception as e:
            print(f"❌ Error connecting to viewer: {e}")
    
    def disconnect_from_viewer(self):
        """Disconnect all signals from viewer"""
        if not self.viewer:
            return
        
        try:
            self.gesture_detected.disconnect(self.viewer.handle_gesture)
            self.pinch_scale.disconnect(self.viewer.handle_pinch_scale)
            self.pinch_start.disconnect(self.viewer.handle_pinch_start)
            self.pinch_distance.disconnect(self.viewer.handle_pinch_distance)
            self.pinch_end.disconnect(self.viewer.handle_pinch_end)
            self.pointer_position.disconnect(self.viewer.update_pointer)
            self.hand_position.disconnect(self.viewer.handle_hand_position)
            print("✅ GestureIntegration disconnected from viewer")
        except:
            pass
        
        self.viewer = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🎯 GESTURE COMMANDS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def send_gesture(self, gesture_name: str):
        """
        Send a discrete gesture command.
        
        Supported gestures:
        - "fist" / "closed_fist" → Toggle zoom lock
        - "swipe_left" / "prev" → Previous slide
        - "swipe_right" / "next" → Next slide
        - "open_palm" / "palm" → Reset view
        - "point" / "pointer" → Enable pointer
        - "peace" / "draw" → Draw mode
        - "thumb_up" → First slide
        - "thumb_down" → Last slide
        - "exit" / "quit" → Close presentation
        
        Args:
            gesture_name: Name of the gesture
        """
        try:
            self.gesture_detected.emit(gesture_name)
        except:
            pass
    
    def send_hand_position(self, x: float, y: float):
        """
        Send continuous hand position for swipe detection.
        Call this every frame with normalized coordinates.
        
        Args:
            x: X position (0=left, 1=right)
            y: Y position (0=top, 1=bottom)
        """
        try:
            # Emit for swipe detection
            self.hand_position.emit(x, y)
            
            # Also update pointer if in pointer mode
            self.pointer_position.emit(x, y)
        except:
            pass
    
    def send_pointer(self, x: float, y: float):
        """
        Send pointer position only (no swipe detection).
        
        Args:
            x: X position (0=left, 1=right)
            y: Y position (0=top, 1=bottom)
        """
        try:
            self.pointer_position.emit(x, y)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🤏 PINCH GESTURE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_pinch(self, finger1_pos: Tuple[float, float], finger2_pos: Tuple[float, float]):
        """
        Start pinch gesture tracking.
        
        Args:
            finger1_pos: (x, y) normalized position of first finger
            finger2_pos: (x, y) normalized position of second finger
        """
        try:
            x1, y1 = finger1_pos
            x2, y2 = finger2_pos
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            self._last_distance = distance
            self._is_pinching = True
            self.pinch_start.emit(x1, y1, x2, y2)
        except Exception as e:
            print(f"Pinch start error: {e}")
    
    def update_pinch(self, finger1_pos: Tuple[float, float], finger2_pos: Tuple[float, float]):
        """
        Update pinch gesture with new finger positions.
        
        Args:
            finger1_pos: (x, y) normalized position of first finger
            finger2_pos: (x, y) normalized position of second finger
        """
        if not self._is_pinching:
            self.start_pinch(finger1_pos, finger2_pos)
            return
        
        try:
            x1, y1 = finger1_pos
            x2, y2 = finger2_pos
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            self.pinch_distance.emit(distance)
            self._last_distance = distance
        except Exception as e:
            print(f"Pinch update error: {e}")
    
    def update_pinch_with_distance(self, distance: float):
        """
        Update pinch with direct distance value.
        
        Args:
            distance: Distance between fingers
        """
        try:
            self.pinch_distance.emit(distance)
            self._last_distance = distance
        except:
            pass
    
    def send_pinch_delta(self, scale_factor: float):
        """
        Send pinch scale delta for incremental zoom.
        
        Args:
            scale_factor: >1 = zoom in, <1 = zoom out
        """
        try:
            self.pinch_scale.emit(scale_factor)
        except:
            pass
    
    def end_pinch(self):
        """End pinch gesture"""
        try:
            self._is_pinching = False
            self.pinch_end.emit()
            self._last_distance = None
        except:
            pass
    
    @property
    def is_pinching(self) -> bool:
        """Check if currently in pinch gesture"""
        return self._is_pinching
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🎮 CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def next_slide(self):
        """Go to next slide"""
        self.send_gesture("next")
    
    def prev_slide(self):
        """Go to previous slide"""
        self.send_gesture("prev")
    
    def first_slide(self):
        """Go to first slide"""
        self.send_gesture("thumb_up")
    
    def last_slide(self):
        """Go to last slide"""
        self.send_gesture("thumb_down")
    
    def toggle_zoom_lock(self):
        """Toggle zoom lock (same as fist gesture)"""
        self.send_gesture("fist")
    
    def reset_view(self):
        """Reset view (same as open palm gesture)"""
        self.send_gesture("open_palm")
    
    def enable_pointer(self):
        """Enable pointer mode"""
        self.send_gesture("point")
    
    def enable_draw_mode(self):
        """Enable draw mode"""
        self.send_gesture("draw")
    
    def exit_presentation(self):
        """Exit presentation"""
        self.send_gesture("exit")