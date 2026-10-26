"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📽️ PRESENTATION VIEWER                               ║
║                    Fullscreen Viewer with Gesture Support                    ║
║                    ✅ Swipe Navigation                                       ║
║                    ✅ Fist = Lock/Unlock Zoom                                ║
║                    ✅ Logarithmic Zoom Scaling                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import gc
import math
import time
from typing import List, Optional, Tuple
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPoint
from PySide6.QtGui import (
    QPixmap, QGuiApplication, QColor, QPainter, QPen, QBrush,
    QFont, QRadialGradient
)

from ...config.colors import FuturisticColors
from ...core.zoom_controller import SmoothZoomController
from ...core.swipe_detector import SwipeDetector
from ..widgets.buttons import FuturisticButton
from ..widgets.decorations import ScanLineOverlay
from ..widgets.indicators import GestureIndicator


class PresentationViewer(QWidget):
    """
    Fullscreen Presentation Viewer with gesture support.
    
    Features:
    - Hand swipe gesture detection for slide navigation
    - FIST = Lock/Unlock zoom at current level
    - Logarithmic zoom scaling
    - Proper state machine for gestures
    - Keyboard and mouse controls
    
    Usage:
        viewer = PresentationViewer(slides)
        viewer.closed.connect(on_closed)
        viewer.showFullScreen()
    """
    
    closed = Signal()
    draw_requested = Signal()
    
    def __init__(self, slides: List[QPixmap], parent=None):
        super().__init__(None)
        
        # Copy slides to prevent memory issues
        self.slides: List[QPixmap] = []
        if slides:
            for slide in slides:
                if slide and not slide.isNull():
                    self.slides.append(slide.copy())
        
        self.current_index = 0
        self.parent_window = parent
        self._is_active = True
        self._destroyed = False
        
        # Zoom controller with lock feature
        self.zoom_controller = SmoothZoomController(self)
        self.zoom_controller.set_zoom_limits(0.25, 5.0)
        self.zoom_controller.zoom_changed.connect(self._on_zoom_changed)
        self.zoom_controller.lock_changed.connect(self._on_lock_changed)
        
        # Swipe detector with state machine
        self.swipe_detector = SwipeDetector()
        self.swipe_detector.debug = False  # Set True for debug output
        
        # View state
        self.pan_x = 0
        self.pan_y = 0
        self.pointer_pos: Optional[Tuple[int, int]] = None
        self.show_pointer = False
        self._display_zoom = 1.0
        
        # Swipe visualization
        self._swipe_trail: deque = deque(maxlen=15)
        self._show_swipe_trail = True
        
        # Window setup
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Window |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # Screen geometry
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.screen_w = geometry.width()
            self.screen_h = geometry.height()
        else:
            self.screen_w = 1920
            self.screen_h = 1080
        
        self.setGeometry(0, 0, self.screen_w, self.screen_h)
        self.setStyleSheet(f"background: {FuturisticColors.NAVY_DARKEST};")
        
        self._build_ui()
        
        # Gesture indicator
        self.gesture_indicator = GestureIndicator(self)
        self.gesture_indicator.move((self.screen_w - 400) // 2, self.screen_h - 200)
        
        # Scanlines overlay
        self.scanlines = ScanLineOverlay(self)
        self.scanlines.setGeometry(0, 0, self.screen_w, self.screen_h)
        self.scanlines.lower()
        
        # Timers
        self._zoom_display_timer = QTimer(self)
        self._zoom_display_timer.setSingleShot(True)
        self._zoom_display_timer.timeout.connect(self._update_zoom_display_delayed)
        
        self._trail_timer = QTimer(self)
        self._trail_timer.timeout.connect(self._fade_trail)
        self._trail_timer.start(60)
        
        print(f"✅ PresentationViewer initialized with {len(self.slides)} slides")
        print(f"   👋 Swipe gestures: Swipe LEFT/RIGHT for navigation")
        print(f"   ✊ Fist gesture: Lock/Unlock zoom")
        print(f"   🔍 Logarithmic zoom scaling active")
    
    def _build_ui(self):
        """Build the viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ═══════════════════════════════════════════════════════════════════
        # TOP BAR
        # ═══════════════════════════════════════════════════════════════════
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(3, 8, 17, 0.98),
                    stop:1 rgba(3, 8, 17, 0));
                border-bottom: 1px solid rgba(0, 212, 255, 0.2);
            }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(40, 12, 40, 12)
        
        # Slide counter
        hud_left = QFrame()
        hud_left.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 212, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-radius: 4px;
            }}
        """)
        hud_left_layout = QHBoxLayout(hud_left)
        hud_left_layout.setContentsMargins(20, 8, 20, 8)
        
        slide_count = len(self.slides) if self.slides else 0
        self.slide_label = QLabel(f"◆ SLIDE 01 / {slide_count:02d}")
        self.slide_label.setStyleSheet(f"""
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            font-weight: bold;
            color: {FuturisticColors.CYAN};
            background: transparent;
            letter-spacing: 2px;
        """)
        hud_left_layout.addWidget(self.slide_label)
        top_layout.addWidget(hud_left)
        
        top_layout.addStretch()
        
        # Center - Title and gesture status
        center_frame = QVBoxLayout()
        title = QLabel("⬡ PRESENTATION MODE")
        title.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 12px;
            color: {FuturisticColors.TEXT_MUTED};
            background: transparent;
            letter-spacing: 3px;
        """)
        title.setAlignment(Qt.AlignCenter)
        center_frame.addWidget(title)
        
        self.gesture_status = QLabel("👋 SWIPE = NAVIGATE • ✊ FIST = LOCK ZOOM • 🤏 PINCH = ZOOM")
        self.gesture_status.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {FuturisticColors.GREEN};
            background: transparent;
            letter-spacing: 1px;
        """)
        self.gesture_status.setAlignment(Qt.AlignCenter)
        center_frame.addWidget(self.gesture_status)
        top_layout.addLayout(center_frame)
        
        top_layout.addStretch()
        
        # ═══════════════════════════════════════════════════════════════════
        # ZOOM CONTROLS WITH LOCK INDICATOR
        # ═══════════════════════════════════════════════════════════════════
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 212, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-radius: 4px;
            }}
        """)
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(8, 8, 8, 8)
        zoom_layout.setSpacing(8)
        
        # Lock indicator
        self.lock_indicator = QLabel("🔓")
        self.lock_indicator.setStyleSheet("background: transparent; font-size: 16px;")
        self.lock_indicator.setToolTip("Zoom Lock Status")
        zoom_layout.addWidget(self.lock_indicator)
        
        # Zoom out button
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(32, 32)
        self.zoom_out_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_out_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 212, 255, 0.2);
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 4px;
                color: {FuturisticColors.CYAN};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.4);
                border: 1px solid {FuturisticColors.CYAN};
                color: white;
            }}
        """)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        # Zoom label
        self.zoom_label = QPushButton("100%")
        self.zoom_label.setFixedSize(80, 32)
        self.zoom_label.setCursor(Qt.PointingHandCursor)
        self.zoom_label.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 212, 255, 0.15);
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-radius: 4px;
                color: {FuturisticColors.TEXT_SECONDARY};
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.3);
                color: white;
            }}
        """)
        self.zoom_label.clicked.connect(self._reset_zoom)
        zoom_layout.addWidget(self.zoom_label)
        
        # Zoom in button
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(32, 32)
        self.zoom_in_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_in_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 212, 255, 0.2);
                border: 1px solid rgba(0, 212, 255, 0.5);
                border-radius: 4px;
                color: {FuturisticColors.CYAN};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.4);
                border: 1px solid {FuturisticColors.CYAN};
                color: white;
            }}
        """)
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        # Lock button
        self.lock_btn = QPushButton("🔒")
        self.lock_btn.setFixedSize(32, 32)
        self.lock_btn.setCursor(Qt.PointingHandCursor)
        self.lock_btn.setToolTip("Toggle Zoom Lock (or use Fist gesture)")
        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(234, 179, 8, 0.2);
                border: 1px solid rgba(234, 179, 8, 0.5);
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: rgba(234, 179, 8, 0.4);
                border: 1px solid {FuturisticColors.YELLOW};
            }}
        """)
        self.lock_btn.clicked.connect(self._toggle_zoom_lock)
        zoom_layout.addWidget(self.lock_btn)
        
        top_layout.addWidget(zoom_frame)
        
        # Draw button
        self.draw_btn = FuturisticButton("◈ DRAW", FuturisticColors.PURPLE)
        self.draw_btn.clicked.connect(self._on_draw_clicked)
        top_layout.addWidget(self.draw_btn)
        
        # Close button
        self.close_btn = FuturisticButton("✕ EXIT", FuturisticColors.RED)
        self.close_btn.clicked.connect(self._close_presentation)
        top_layout.addWidget(self.close_btn)
        
        layout.addWidget(top_bar)
        
        # ═══════════════════════════════════════════════════════════════════
        # SLIDE DISPLAY
        # ═══════════════════════════════════════════════════════════════════
        slide_container = QFrame()
        slide_container.setStyleSheet("background: transparent;")
        slide_layout = QVBoxLayout(slide_container)
        slide_layout.setAlignment(Qt.AlignCenter)
        
        self.slide_frame = QFrame()
        self.slide_frame.setStyleSheet(f"""
            QFrame {{
                background: {FuturisticColors.NAVY_DARKER};
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
            }}
        """)
        frame_layout = QVBoxLayout(self.slide_frame)
        frame_layout.setContentsMargins(4, 4, 4, 4)
        
        self.slide_display = QLabel()
        self.slide_display.setAlignment(Qt.AlignCenter)
        self.slide_display.setStyleSheet("background: transparent;")
        frame_layout.addWidget(self.slide_display)
        
        slide_layout.addWidget(self.slide_frame)
        layout.addWidget(slide_container, 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # BOTTOM BAR
        # ═══════════════════════════════════════════════════════════════════
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(100)
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(3, 8, 17, 0.98),
                    stop:1 rgba(3, 8, 17, 0));
                border-top: 1px solid rgba(0, 212, 255, 0.2);
            }}
        """)
        nav_layout = QHBoxLayout(bottom_bar)
        nav_layout.setContentsMargins(40, 15, 40, 25)
        
        # Gesture hints
        hints_frame = QFrame()
        hints_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 22, 40, 0.6);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 4px;
            }}
        """)
        hints_layout = QVBoxLayout(hints_frame)
        hints_layout.setContentsMargins(15, 8, 15, 8)
        hints_layout.setSpacing(2)
        
        hints_title = QLabel("GESTURE CONTROLS")
        hints_title.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 9px;
            color: {FuturisticColors.CYAN};
            background: transparent;
            letter-spacing: 1px;
        """)
        hints_layout.addWidget(hints_title)
        
        hints_text = QLabel("👈 SWIPE = NAV | ✊ FIST = LOCK ZOOM | 🤏 PINCH = ZOOM | ✋ PALM = RESET")
        hints_text.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {FuturisticColors.TEXT_MUTED};
            background: transparent;
        """)
        hints_layout.addWidget(hints_text)
        nav_layout.addWidget(hints_frame)
        
        nav_layout.addStretch()
        
        # Previous button
        self.prev_btn = FuturisticButton("◀ PREV", FuturisticColors.ELECTRIC_BLUE)
        self.prev_btn.setFixedWidth(140)
        self.prev_btn.clicked.connect(self._prev_slide)
        nav_layout.addWidget(self.prev_btn)
        
        # Progress display
        progress_frame = QFrame()
        progress_frame.setFixedWidth(250)
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 22, 40, 0.8);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 4px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(20, 10, 20, 10)
        progress_layout.setSpacing(8)
        
        self.progress_text = QLabel("SLIDE 01")
        self.progress_text.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
            color: {FuturisticColors.CYAN};
            background: transparent;
            letter-spacing: 3px;
        """)
        self.progress_text.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(0, 212, 255, 0.1);
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {FuturisticColors.CYAN},
                    stop:1 {FuturisticColors.ELECTRIC_BLUE});
                border-radius: 2px;
            }}
        """)
        self.progress_bar.setMaximum(max(len(self.slides), 1))
        self.progress_bar.setValue(1)
        progress_layout.addWidget(self.progress_bar)
        nav_layout.addWidget(progress_frame)
        
        # Next button
        self.next_btn = FuturisticButton("NEXT ▶", FuturisticColors.CYAN)
        self.next_btn.setFixedWidth(140)
        self.next_btn.clicked.connect(self._next_slide)
        nav_layout.addWidget(self.next_btn)
        
        nav_layout.addStretch()
        layout.addWidget(bottom_bar)
        
        # Initial slide update
        QTimer.singleShot(100, self._update_slide)
    
    def _fade_trail(self):
        """Fade out the swipe trail"""
        if self._destroyed:
            return
        try:
            if self._swipe_trail:
                self._swipe_trail.popleft()
                self.update()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🔒 ZOOM LOCK HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _toggle_zoom_lock(self):
        """Toggle zoom lock via button"""
        if self._destroyed:
            return
        try:
            is_locked = self.zoom_controller.toggle_lock()
            self._update_lock_display(is_locked)
            
            if is_locked:
                zoom_pct = int(self.zoom_controller.locked_zoom * 100)
                self.gesture_indicator.show_gesture(
                    f"ZOOM LOCKED", "🔒",
                    f"Frozen at {zoom_pct}%",
                    QColor(FuturisticColors.YELLOW)
                )
            else:
                self.gesture_indicator.show_gesture(
                    "ZOOM UNLOCKED", "🔓",
                    "Pinch to zoom",
                    QColor(FuturisticColors.GREEN)
                )
        except Exception as e:
            print(f"Toggle lock error: {e}")
    
    @Slot(bool)
    def _on_lock_changed(self, is_locked: bool):
        """Handle lock state change from controller"""
        self._update_lock_display(is_locked)
    
    def _update_lock_display(self, is_locked: bool):
        """Update UI to reflect lock state"""
        if self._destroyed:
            return
        try:
            if is_locked:
                self.lock_indicator.setText("🔒")
                self.lock_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(234, 179, 8, 0.5);
                        border: 2px solid {FuturisticColors.YELLOW};
                        border-radius: 4px;
                        font-size: 14px;
                    }}
                """)
                self.zoom_in_btn.setEnabled(False)
                self.zoom_out_btn.setEnabled(False)
                
                # Update zoom label to show locked state
                zoom_pct = int(self.zoom_controller.locked_zoom * 100)
                self.zoom_label.setText(f"🔒{zoom_pct}%")
                self.zoom_label.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(234, 179, 8, 0.2);
                        border: 1px solid {FuturisticColors.YELLOW};
                        border-radius: 4px;
                        color: {FuturisticColors.YELLOW};
                        font-family: 'Consolas', monospace;
                        font-size: 10px;
                        font-weight: bold;
                    }}
                """)
            else:
                self.lock_indicator.setText("🔓")
                self.lock_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(234, 179, 8, 0.2);
                        border: 1px solid rgba(234, 179, 8, 0.5);
                        border-radius: 4px;
                        font-size: 14px;
                    }}
                    QPushButton:hover {{
                        background: rgba(234, 179, 8, 0.4);
                    }}
                """)
                self.zoom_in_btn.setEnabled(True)
                self.zoom_out_btn.setEnabled(True)
                
                # Reset zoom label style
                self._update_zoom_display_delayed()
        except:
            pass
    
    @Slot(float)
    def _on_zoom_changed(self, zoom: float):
        """Handle zoom change"""
        if self._destroyed:
            return
        try:
            self._display_zoom = zoom
            self._update_slide_display()
            self._zoom_display_timer.start(50)
        except Exception as e:
            print(f"Zoom change error: {e}")
    
    def _update_zoom_display_delayed(self):
        """Update zoom display after delay"""
        if self._destroyed:
            return
        try:
            if self.zoom_controller.is_locked:
                return  # Don't update if locked (keep lock display)
            
            pct = int(self._display_zoom * 100)
            if hasattr(self, 'zoom_label'):
                self.zoom_label.setText(f"{pct}%")
                self.zoom_label.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(0, 212, 255, 0.15);
                        border: 1px solid rgba(0, 212, 255, 0.4);
                        border-radius: 4px;
                        color: {FuturisticColors.TEXT_SECONDARY};
                        font-family: 'Consolas', monospace;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: rgba(0, 212, 255, 0.3);
                        color: white;
                    }}
                """)
        except:
            pass
    
    def _zoom_in(self):
        """Zoom in"""
        if self._destroyed:
            return
        try:
            if self.zoom_controller.is_locked:
                self.gesture_indicator.show_gesture(
                    "ZOOM LOCKED", "🔒",
                    "Use fist to unlock",
                    QColor(FuturisticColors.ORANGE)
                )
                return
            self.zoom_controller.zoom_in()
            self.gesture_indicator.show_gesture("ZOOM IN", "🔍+")
        except Exception as e:
            print(f"Zoom in error: {e}")
    
    def _zoom_out(self):
        """Zoom out"""
        if self._destroyed:
            return
        try:
            if self.zoom_controller.is_locked:
                self.gesture_indicator.show_gesture(
                    "ZOOM LOCKED", "🔒",
                    "Use fist to unlock",
                    QColor(FuturisticColors.ORANGE)
                )
                return
            self.zoom_controller.zoom_out()
            self.gesture_indicator.show_gesture("ZOOM OUT", "🔍−")
        except Exception as e:
            print(f"Zoom out error: {e}")
    
    def _reset_zoom(self):
        """Reset zoom"""
        if self._destroyed:
            return
        try:
            self.zoom_controller.reset_zoom()  # Also unlocks
            self.pan_x = 0
            self.pan_y = 0
            self.gesture_indicator.show_gesture("ZOOM RESET", "🔄", "Unlocked")
        except Exception as e:
            print(f"Reset zoom error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         👋 HAND POSITION / SWIPE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    @Slot(float, float)
    def handle_hand_position(self, x: float, y: float):
        """
        Handle continuous hand position updates for swipe detection.
        
        Args:
            x: X position (0-1 normalized, 0=left, 1=right)
            y: Y position (0-1 normalized, 0=top, 1=bottom)
        """
        if self._destroyed or not self._is_active:
            return
        
        try:
            # Add to visual trail
            if self._show_swipe_trail:
                screen_x = int(x * self.screen_w)
                screen_y = int(y * self.screen_h)
                self._swipe_trail.append((screen_x, screen_y, time.time()))
                self.update()
            
            # Check for swipe gesture
            swipe = self.swipe_detector.add_position(x, y)
            
            if swipe == "swipe_right":
                print("👉 SWIPE RIGHT → NEXT slide")
                self._next_slide()
                self.gesture_indicator.show_gesture(
                    "NEXT SLIDE", "👉",
                    f"Slide {self.current_index + 1}",
                    QColor(FuturisticColors.CYAN)
                )
                
            elif swipe == "swipe_left":
                print("👈 SWIPE LEFT → PREVIOUS slide")
                self._prev_slide()
                self.gesture_indicator.show_gesture(
                    "PREVIOUS SLIDE", "👈",
                    f"Slide {self.current_index + 1}",
                    QColor(FuturisticColors.ELECTRIC_BLUE)
                )
                
        except Exception as e:
            print(f"Hand position error: {e}")
    
    @Slot(str)
    def handle_gesture(self, gesture: str):
        """Handle discrete gesture commands"""
        if self._destroyed or not self._is_active:
            return
        
        try:
            gesture_lower = gesture.lower().strip()
            
            # ═══════════════════════════════════════════════════════════════
            # FIST = TOGGLE ZOOM LOCK (not exit!)
            # ═══════════════════════════════════════════════════════════════
            if gesture_lower in ["fist", "closed_fist", "closed fist", "closed"]:
                is_locked = self.zoom_controller.toggle_lock()
                self._update_lock_display(is_locked)
                
                if is_locked:
                    zoom_pct = int(self.zoom_controller.locked_zoom * 100)
                    self.gesture_indicator.show_gesture(
                        f"ZOOM LOCKED", "✊🔒",
                        f"Frozen at {zoom_pct}%",
                        QColor(FuturisticColors.YELLOW)
                    )
                else:
                    self.gesture_indicator.show_gesture(
                        "ZOOM UNLOCKED", "✊🔓",
                        "Pinch to zoom",
                        QColor(FuturisticColors.GREEN)
                    )
                return
            
            # Navigation gestures
            if gesture_lower in ["swipe_left", "prev", "previous", "left"]:
                self._prev_slide()
                self.gesture_indicator.show_gesture("PREVIOUS SLIDE", "👈")
                
            elif gesture_lower in ["swipe_right", "next", "right"]:
                self._next_slide()
                self.gesture_indicator.show_gesture("NEXT SLIDE", "👉")
            
            # Zoom gestures (blocked if locked)
            elif gesture_lower in ["pinch_open", "pinch open", "zoom_in", "zoom in"]:
                if not self.zoom_controller.is_locked:
                    self._zoom_in()
                else:
                    self.gesture_indicator.show_gesture(
                        "ZOOM LOCKED", "🔒",
                        "Use fist to unlock",
                        QColor(FuturisticColors.ORANGE)
                    )
                
            elif gesture_lower in ["pinch_close", "pinch close", "zoom_out", "zoom out"]:
                if not self.zoom_controller.is_locked:
                    self._zoom_out()
                else:
                    self.gesture_indicator.show_gesture(
                        "ZOOM LOCKED", "🔒",
                        "Use fist to unlock",
                        QColor(FuturisticColors.ORANGE)
                    )
                
            # Pointer mode
            elif gesture_lower in ["point", "pointer", "index", "one"]:
                self.show_pointer = True
                self.gesture_indicator.show_gesture("POINTER MODE", "☝️")
                
            # Draw mode
            elif gesture_lower in ["peace", "draw", "two", "victory"]:
                self._on_draw_clicked()
                self.gesture_indicator.show_gesture("DRAW MODE", "✌️")
                
            # Jump to first
            elif gesture_lower in ["thumb_up", "thumbs up", "first", "thumbs_up"]:
                self.current_index = 0
                self.zoom_controller.reset_zoom()
                self._update_slide()
                self.gesture_indicator.show_gesture("FIRST SLIDE", "👍")
                
            # Jump to last
            elif gesture_lower in ["thumb_down", "thumbs down", "last", "thumbs_down"]:
                if self.slides:
                    self.current_index = len(self.slides) - 1
                    self.zoom_controller.reset_zoom()
                    self._update_slide()
                self.gesture_indicator.show_gesture("LAST SLIDE", "👎")
                
            # Reset/stop
            elif gesture_lower in ["open_palm", "palm", "stop", "open", "five"]:
                self.show_pointer = False
                self._reset_zoom()
                self.swipe_detector.reset()
                self.gesture_indicator.show_gesture("RESET", "✋")
            
            # Exit (use specific "exit" command, not fist)
            elif gesture_lower in ["exit", "quit", "close"]:
                self.gesture_indicator.show_gesture("EXITING...", "👋")
                QTimer.singleShot(500, self._close_presentation)
                
        except Exception as e:
            print(f"Gesture handling error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🤏 PINCH HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    @Slot(float, float, float, float)
    def handle_pinch_start(self, x1: float, y1: float, x2: float, y2: float):
        """Handle pinch start"""
        if self._destroyed or not self._is_active:
            return
        
        if self.zoom_controller.is_locked:
            self.gesture_indicator.show_gesture(
                "ZOOM LOCKED", "🔒",
                "Use fist to unlock",
                QColor(FuturisticColors.ORANGE)
            )
            return
        
        try:
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            self.zoom_controller.start_pinch(distance)
            self.gesture_indicator.show_gesture("PINCH ZOOM", "🤏")
        except Exception as e:
            print(f"Pinch start error: {e}")
    
    @Slot(float)
    def handle_pinch_distance(self, current_distance: float):
        """Handle pinch distance update"""
        if self._destroyed or not self._is_active:
            return
        if self.zoom_controller.is_locked:
            return
        try:
            self.zoom_controller.update_pinch(current_distance)
        except Exception as e:
            print(f"Pinch distance error: {e}")
    
    @Slot(float)
    def handle_pinch_scale(self, scale_delta: float):
        """Handle pinch scale delta"""
        if self._destroyed or not self._is_active:
            return
        if self.zoom_controller.is_locked:
            return
        try:
            self.zoom_controller.handle_pinch_delta(scale_delta)
        except Exception as e:
            print(f"Pinch scale error: {e}")
    
    @Slot()
    def handle_pinch_end(self):
        """Handle pinch end"""
        if self._destroyed or not self._is_active:
            return
        try:
            self.zoom_controller.end_pinch()
        except Exception as e:
            print(f"Pinch end error: {e}")
    
    @Slot(float, float)
    def update_pointer(self, x: float, y: float):
        """Update pointer position"""
        if self._destroyed:
            return
        try:
            if self.show_pointer:
                self.pointer_pos = (int(x * self.screen_w), int(y * self.screen_h))
                self.update()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🎨 PAINTING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def paintEvent(self, event):
        """Paint event for custom drawing"""
        super().paintEvent(event)
        
        if self._destroyed:
            return
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw swipe trail
            if self._show_swipe_trail and self._swipe_trail:
                current_time = time.time()
                points = list(self._swipe_trail)
                
                for i, (x, y, t) in enumerate(points):
                    age = current_time - t
                    if age > 0.4:
                        continue
                    
                    alpha = int(200 * (1 - age / 0.4))
                    size = int(12 * (1 - age / 0.4)) + 4
                    
                    progress = i / max(len(points), 1)
                    color = QColor(
                        int(0 + 59 * progress),
                        int(212 - 82 * progress),
                        int(255 - 9 * progress),
                        alpha
                    )
                    
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPoint(x, y), size, size)
            
            # Draw pointer
            if self.show_pointer and self.pointer_pos:
                x, y = self.pointer_pos
                
                gradient = QRadialGradient(x, y, 30)
                gradient.setColorAt(0, QColor(0, 212, 255, 150))
                gradient.setColorAt(0.5, QColor(0, 212, 255, 50))
                gradient.setColorAt(1, QColor(0, 212, 255, 0))
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(x, y), 30, 30)
                
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QPoint(x, y), 8, 8)
                
                pen = QPen(QColor(0, 212, 255), 2)
                painter.setPen(pen)
                painter.drawLine(x - 20, y, x - 10, y)
                painter.drawLine(x + 10, y, x + 20, y)
                painter.drawLine(x, y - 20, x, y - 10)
                painter.drawLine(x, y + 10, x, y + 20)
                
            # Draw lock indicator overlay when locked
            if self.zoom_controller.is_locked:
                # Small lock icon in corner
                painter.setPen(QPen(QColor(FuturisticColors.YELLOW), 2))
                font = QFont("Consolas", 16)
                painter.setFont(font)
                painter.drawText(self.screen_w - 80, 100, "🔒")
                
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         📊 SLIDE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _update_slide_display(self):
        """Update slide display with current zoom"""
        if self._destroyed or not self.slides:
            return
        
        try:
            if self.current_index < 0:
                self.current_index = 0
            if self.current_index >= len(self.slides):
                self.current_index = len(self.slides) - 1
            
            pixmap = self.slides[self.current_index]
            if pixmap is None or pixmap.isNull():
                return
            
            base_w = self.screen_w - 150
            base_h = self.screen_h - 250
            
            zoom = self._display_zoom
            zoomed_w = int(base_w * zoom)
            zoomed_h = int(base_h * zoom)
            
            scaled = pixmap.scaled(
                zoomed_w, zoomed_h,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            if hasattr(self, 'slide_display'):
                self.slide_display.setPixmap(scaled)
            
            if hasattr(self, 'slide_frame'):
                frame_w = min(scaled.width() + 10, self.screen_w - 50)
                frame_h = min(scaled.height() + 10, self.screen_h - 180)
                self.slide_frame.setFixedSize(frame_w, frame_h)
            
        except Exception as e:
            print(f"Error updating slide display: {e}")
    
    def _update_slide(self):
        """Update slide and UI"""
        if self._destroyed or not self.slides:
            return
        
        try:
            self._update_slide_display()
            
            total = len(self.slides)
            current = self.current_index + 1
            
            if hasattr(self, 'slide_label'):
                self.slide_label.setText(f"◆ SLIDE {current:02d} / {total:02d}")
            
            if hasattr(self, 'progress_text'):
                self.progress_text.setText(f"SLIDE {current:02d}")
            
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setMaximum(max(total, 1))
                self.progress_bar.setValue(current)
            
            if hasattr(self, 'prev_btn'):
                self.prev_btn.setEnabled(self.current_index > 0)
            
            if hasattr(self, 'next_btn'):
                self.next_btn.setEnabled(self.current_index < len(self.slides) - 1)
            
            self._update_zoom_display_delayed()
            
        except Exception as e:
            print(f"Error updating slide: {e}")
    
    def _prev_slide(self):
        """Go to previous slide"""
        if self._destroyed:
            return
        try:
            if self.current_index > 0:
                self.current_index -= 1
                # Don't reset zoom when changing slides if locked
                if not self.zoom_controller.is_locked:
                    self.zoom_controller.set_target_zoom(1.0, immediate=True)
                self._update_slide()
                print(f"◀ Previous: Slide {self.current_index + 1}")
        except Exception as e:
            print(f"Prev slide error: {e}")
    
    def _next_slide(self):
        """Go to next slide"""
        if self._destroyed:
            return
        try:
            if self.slides and self.current_index < len(self.slides) - 1:
                self.current_index += 1
                # Don't reset zoom when changing slides if locked
                if not self.zoom_controller.is_locked:
                    self.zoom_controller.set_target_zoom(1.0, immediate=True)
                self._update_slide()
                print(f"▶ Next: Slide {self.current_index + 1}")
        except Exception as e:
            print(f"Next slide error: {e}")
    
    def _on_draw_clicked(self):
        """Handle draw button click"""
        if self._destroyed:
            return
        try:
            self.draw_requested.emit()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🚪 CLOSE / CLEANUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _close_presentation(self):
        """Close the presentation"""
        print("🔒 Closing presentation viewer...")
        
        if self._destroyed:
            return
        
        self._destroyed = True
        self._is_active = False
        
        # Cleanup in order
        cleanup_errors = []
        
        try:
            if hasattr(self, 'zoom_controller') and self.zoom_controller:
                self.zoom_controller.cleanup()
        except Exception as e:
            cleanup_errors.append(f"zoom_controller: {e}")
        
        try:
            if hasattr(self, '_zoom_display_timer') and self._zoom_display_timer:
                self._zoom_display_timer.stop()
        except Exception as e:
            cleanup_errors.append(f"zoom_timer: {e}")
        
        try:
            if hasattr(self, '_trail_timer') and self._trail_timer:
                self._trail_timer.stop()
        except Exception as e:
            cleanup_errors.append(f"trail_timer: {e}")
        
        try:
            if hasattr(self, 'gesture_indicator') and self.gesture_indicator:
                self.gesture_indicator.cleanup()
        except Exception as e:
            cleanup_errors.append(f"gesture_indicator: {e}")
        
        try:
            if hasattr(self, 'scanlines') and self.scanlines:
                self.scanlines.stop_animation()
        except Exception as e:
            cleanup_errors.append(f"scanlines: {e}")
        
        for btn_name in ['draw_btn', 'close_btn', 'prev_btn', 'next_btn']:
            try:
                btn = getattr(self, btn_name, None)
                if btn and hasattr(btn, 'cleanup'):
                    btn.cleanup()
            except Exception as e:
                cleanup_errors.append(f"{btn_name}: {e}")
        
        try:
            if self.slides:
                self.slides.clear()
        except:
            pass
        
        if cleanup_errors:
            print(f"⚠️ Cleanup warnings: {', '.join(cleanup_errors)}")
        
        try:
            self.closed.emit()
        except:
            pass
        
        try:
            self.hide()
            self.close()
        except:
            pass
        
        try:
            gc.collect()
        except:
            pass
        
        print("✅ Presentation viewer closed")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         ⌨️ KEYBOARD & MOUSE EVENTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom"""
        if self._destroyed:
            return
        try:
            if self.zoom_controller.is_locked:
                self.gesture_indicator.show_gesture(
                    "ZOOM LOCKED", "🔒",
                    "Use fist to unlock",
                    QColor(FuturisticColors.ORANGE)
                )
                return
            
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
        except:
            pass
    
    def keyPressEvent(self, event):
        """Handle keyboard input"""
        if self._destroyed:
            return
        
        try:
            key = event.key()
            
            if key == Qt.Key_Escape:
                self._close_presentation()
            elif key in [Qt.Key_Left, Qt.Key_Up, Qt.Key_PageUp]:
                self._prev_slide()
            elif key in [Qt.Key_Right, Qt.Key_Down, Qt.Key_PageDown, Qt.Key_Space]:
                self._next_slide()
            elif key == Qt.Key_Home:
                self.current_index = 0
                if not self.zoom_controller.is_locked:
                    self.zoom_controller.set_target_zoom(1.0, immediate=True)
                self._update_slide()
            elif key == Qt.Key_End:
                if self.slides:
                    self.current_index = len(self.slides) - 1
                    if not self.zoom_controller.is_locked:
                        self.zoom_controller.set_target_zoom(1.0, immediate=True)
                    self._update_slide()
            elif key == Qt.Key_D:
                self._on_draw_clicked()
            elif key in [Qt.Key_Plus, Qt.Key_Equal]:
                self._zoom_in()
            elif key == Qt.Key_Minus:
                self._zoom_out()
            elif key == Qt.Key_0:
                self._reset_zoom()
            elif key == Qt.Key_L:  # L = Toggle lock
                self._toggle_zoom_lock()
            else:
                super().keyPressEvent(event)
        except:
            pass
    
    def is_active(self) -> bool:
        """Check if viewer is active"""
        return self._is_active and not self._destroyed
    
    def closeEvent(self, event):
        """Handle close event"""
        if not self._destroyed:
            self._close_presentation()
        event.accept()