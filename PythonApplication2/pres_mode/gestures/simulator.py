"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🧪 GESTURE SIMULATOR                                 ║
║                    Test Gestures Without Hand Tracking                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer

if TYPE_CHECKING:
    from .integration import GestureIntegration


class GestureSimulator(QObject):
    """
    Simulates hand gestures for testing without actual hand tracking.
    Useful for development and demonstration.
    
    Usage:
        integration = GestureIntegration(viewer)
        simulator = GestureSimulator(integration)
        
        # Start continuous position updates
        simulator.start()
        
        # Simulate specific gestures
        simulator.simulate_swipe_right()
        simulator.simulate_fist()
        simulator.simulate_pinch_zoom_in()
        
        # Stop when done
        simulator.stop()
    """
    
    def __init__(self, integration: 'GestureIntegration', parent=None):
        super().__init__(parent)
        
        self.integration = integration
        self._running = False
        self._destroyed = False
        
        # Movement timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._simulate_movement)
        
        # Simulation state
        self._current_x = 0.5
        self._current_y = 0.5
        self._target_x = 0.5
        self._target_y = 0.5
        self._movement_speed = 0.03
    
    def cleanup(self):
        """Clean up resources"""
        self._destroyed = True
        self.stop()
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         ▶️ START / STOP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start(self):
        """Start continuous position updates"""
        if self._destroyed:
            return
        
        self._running = True
        self._timer.start(33)  # ~30 FPS
        print("🧪 Gesture simulator started")
    
    def stop(self):
        """Stop simulation"""
        self._running = False
        try:
            self._timer.stop()
        except:
            pass
        print("🧪 Gesture simulator stopped")
    
    def is_running(self) -> bool:
        """Check if simulator is running"""
        return self._running
    
    def _simulate_movement(self):
        """Send current position to integration"""
        if not self._running or self._destroyed:
            return
        
        try:
            # Smoothly move toward target
            dx = self._target_x - self._current_x
            dy = self._target_y - self._current_y
            
            if abs(dx) > 0.01:
                self._current_x += dx * 0.15
            if abs(dy) > 0.01:
                self._current_y += dy * 0.15
            
            # Send position
            self.integration.send_hand_position(self._current_x, self._current_y)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         👋 SWIPE GESTURES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def simulate_swipe_right(self):
        """Simulate a swipe right gesture (next slide)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating SWIPE RIGHT...")
        
        # Set start position
        self._current_x = 0.25
        self._current_y = 0.5
        
        # Animate to end position
        positions = [0.3, 0.4, 0.5, 0.6, 0.7, 0.75]
        
        def send_next(idx):
            if self._destroyed:
                return
            if idx < len(positions):
                self._current_x = positions[idx]
                self.integration.send_hand_position(self._current_x, self._current_y)
                QTimer.singleShot(60, lambda: send_next(idx + 1))
        
        send_next(0)
    
    def simulate_swipe_left(self):
        """Simulate a swipe left gesture (previous slide)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating SWIPE LEFT...")
        
        self._current_x = 0.75
        self._current_y = 0.5
        
        positions = [0.7, 0.6, 0.5, 0.4, 0.3, 0.25]
        
        def send_next(idx):
            if self._destroyed:
                return
            if idx < len(positions):
                self._current_x = positions[idx]
                self.integration.send_hand_position(self._current_x, self._current_y)
                QTimer.singleShot(60, lambda: send_next(idx + 1))
        
        send_next(0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         ✊ DISCRETE GESTURES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def simulate_fist(self):
        """Simulate fist gesture (toggle zoom lock)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating FIST (toggle zoom lock)...")
        self.integration.send_gesture("fist")
    
    def simulate_open_palm(self):
        """Simulate open palm gesture (reset view)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating OPEN PALM (reset)...")
        self.integration.send_gesture("open_palm")
    
    def simulate_point(self):
        """Simulate point gesture (enable pointer)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating POINT (pointer mode)...")
        self.integration.send_gesture("point")
    
    def simulate_peace(self):
        """Simulate peace gesture (draw mode)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating PEACE (draw mode)...")
        self.integration.send_gesture("peace")
    
    def simulate_thumb_up(self):
        """Simulate thumb up gesture (first slide)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating THUMB UP (first slide)...")
        self.integration.send_gesture("thumb_up")
    
    def simulate_thumb_down(self):
        """Simulate thumb down gesture (last slide)"""
        if self._destroyed:
            return
        
        print("🧪 Simulating THUMB DOWN (last slide)...")
        self.integration.send_gesture("thumb_down")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🤏 PINCH GESTURES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def simulate_pinch_zoom_in(self):
        """Simulate pinch zoom in"""
        if self._destroyed:
            return
        
        print("🧪 Simulating PINCH ZOOM IN...")
        
        # Start pinch
        self.integration.start_pinch((0.4, 0.5), (0.6, 0.5))
        
        # Animate fingers apart
        distances = [0.22, 0.26, 0.30, 0.35, 0.40]
        
        def send_next(idx):
            if self._destroyed:
                return
            if idx < len(distances):
                self.integration.update_pinch_with_distance(distances[idx])
                QTimer.singleShot(80, lambda: send_next(idx + 1))
            else:
                self.integration.end_pinch()
        
        QTimer.singleShot(100, lambda: send_next(0))
    
    def simulate_pinch_zoom_out(self):
        """Simulate pinch zoom out"""
        if self._destroyed:
            return
        
        print("🧪 Simulating PINCH ZOOM OUT...")
        
        self.integration.start_pinch((0.3, 0.5), (0.7, 0.5))
        
        distances = [0.38, 0.32, 0.26, 0.22, 0.18]
        
        def send_next(idx):
            if self._destroyed:
                return
            if idx < len(distances):
                self.integration.update_pinch_with_distance(distances[idx])
                QTimer.singleShot(80, lambda: send_next(idx + 1))
            else:
                self.integration.end_pinch()
        
        QTimer.singleShot(100, lambda: send_next(0))
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🖱️ POINTER SIMULATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def simulate_pointer_movement(self, duration_ms: int = 3000):
        """
        Simulate pointer moving around the screen.
        
        Args:
            duration_ms: Duration of movement in milliseconds
        """
        if self._destroyed:
            return
        
        print(f"🧪 Simulating POINTER MOVEMENT for {duration_ms}ms...")
        
        # Enable pointer mode
        self.integration.send_gesture("point")
        
        import math
        start_time = 0
        interval = 50  # ms
        
        def move_pointer():
            nonlocal start_time
            if self._destroyed:
                return
            
            start_time += interval
            if start_time >= duration_ms:
                return
            
            # Circular movement
            t = start_time / 1000.0
            x = 0.5 + 0.3 * math.cos(t * 2)
            y = 0.5 + 0.2 * math.sin(t * 2)
            
            self.integration.send_pointer(x, y)
            QTimer.singleShot(interval, move_pointer)
        
        move_pointer()
    
    def set_position(self, x: float, y: float):
        """
        Set current hand position directly.
        
        Args:
            x: X position (0-1)
            y: Y position (0-1)
        """
        if self._destroyed:
            return
        
        self._current_x = x
        self._current_y = y
        self.integration.send_hand_position(x, y)
    
    def move_to(self, x: float, y: float):
        """
        Set target position to move towards.
        
        Args:
            x: Target X position (0-1)
            y: Target Y position (0-1)
        """
        self._target_x = x
        self._target_y = y
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🎬 DEMO SEQUENCES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def run_demo_sequence(self):
        """
        Run a full demo sequence of all gestures.
        Useful for demonstrations.
        """
        if self._destroyed:
            return
        
        print("\n🎬 RUNNING DEMO SEQUENCE")
        print("=" * 50)
        print("   2s  → Swipe RIGHT (next slide)")
        print("   4s  → Swipe LEFT (previous slide)")
        print("   6s  → FIST (lock zoom)")
        print("   8s  → Pinch zoom in (blocked - locked)")
        print("   10s → FIST (unlock zoom)")
        print("   12s → Pinch zoom in (working)")
        print("   14s → Pinch zoom out")
        print("   16s → Open palm (reset)")
        print("=" * 50 + "\n")
        
        # Schedule demo gestures
        QTimer.singleShot(2000, self.simulate_swipe_right)
        QTimer.singleShot(4000, self.simulate_swipe_left)
        QTimer.singleShot(6000, self.simulate_fist)  # Lock
        QTimer.singleShot(8000, self.simulate_pinch_zoom_in)  # Blocked
        QTimer.singleShot(10000, self.simulate_fist)  # Unlock
        QTimer.singleShot(12000, self.simulate_pinch_zoom_in)  # Works
        QTimer.singleShot(14000, self.simulate_pinch_zoom_out)
        QTimer.singleShot(16000, self.simulate_open_palm)
    
    def run_navigation_demo(self):
        """Run a navigation-focused demo"""
        if self._destroyed:
            return
        
        print("\n🎬 RUNNING NAVIGATION DEMO")
        print("=" * 50)
        
        QTimer.singleShot(1000, self.simulate_swipe_right)
        QTimer.singleShot(2500, self.simulate_swipe_right)
        QTimer.singleShot(4000, self.simulate_swipe_right)
        QTimer.singleShot(5500, self.simulate_swipe_left)
        QTimer.singleShot(7000, self.simulate_swipe_left)
        QTimer.singleShot(8500, self.simulate_thumb_up)  # First
        QTimer.singleShot(10000, self.simulate_thumb_down)  # Last
    
    def run_zoom_demo(self):
        """Run a zoom-focused demo"""
        if self._destroyed:
            return
        
        print("\n🎬 RUNNING ZOOM DEMO")
        print("=" * 50)
        
        QTimer.singleShot(1000, self.simulate_pinch_zoom_in)
        QTimer.singleShot(3000, self.simulate_pinch_zoom_in)
        QTimer.singleShot(5000, self.simulate_fist)  # Lock
        QTimer.singleShot(7000, self.simulate_pinch_zoom_out)  # Blocked
        QTimer.singleShot(9000, self.simulate_fist)  # Unlock
        QTimer.singleShot(11000, self.simulate_pinch_zoom_out)
        QTimer.singleShot(13000, self.simulate_open_palm)  # Reset