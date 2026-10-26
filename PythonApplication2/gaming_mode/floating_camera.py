"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GAMING MODE - FLOATING CAMERA WINDOW                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains:
- FloatingCameraWindow (independent window)
- Stays visible when main app is minimized
- Closes when exiting Gaming Mode
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QFont, QColor
import math

from gaming_mode.constants import CyberColors, Direction
from gaming_mode.camera_widget import UltraHolographicCameraWidget


# ═══════════════════════════════════════════════════════════════════════════════
# ✨ FLOATING CAMERA WINDOW - INDEPENDENT (STAYS VISIBLE WHEN APP MINIMIZED)
# ═══════════════════════════════════════════════════════════════════════════════
class FloatingCameraWindow(QWidget):
    """
    ✨ ULTRA Holographic Camera Preview Window
    
    ✅ KEY FIX: This window is COMPLETELY INDEPENDENT of the main app!
    - Uses Qt.Tool flag to stay visible when main app minimizes
    - No parent reference means it won't hide with parent
    - Stays on top of all windows including games
    - ✅ CLOSES when user exits Gaming Mode
    """
    
    closed = Signal()
    
    def __init__(self, parent=None):
        # ✅ CRITICAL: Pass None as parent to make it independent!
        super().__init__(None)  # No parent = independent window
        
        # ✅ Window flags for independent floating window
        self.setWindowFlags(
            Qt.Window |                    # Independent window
            Qt.WindowStaysOnTopHint |      # Always on top
            Qt.FramelessWindowHint |       # No title bar
            Qt.Tool                        # ✅ Tool window - stays visible when app minimizes!
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Don't steal focus
        
        self.setFixedSize(480, 520)
        
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.width() - 500, geo.height() - 560)
        
        self.dragging = False
        self.drag_pos = QPoint()
        self.is_active = False
        self.animation_frame = 0
        
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate)
        
        self._setup_ui()
        
        print("  ✅ Floating Camera Window Created (INDEPENDENT - stays visible when app minimizes)")
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.container = QFrame()
        self.container.setObjectName("hudContainer")
        self._apply_container_style(False)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)
        
        # Header
        header = QFrame()
        header.setFixedHeight(45)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 20, 40, 250),
                    stop:0.5 rgba(0, 40, 60, 250),
                    stop:1 rgba(0, 20, 40, 250));
                border: 2px solid {CyberColors.CYAN_PRIMARY};
                border-radius: 6px;
            }}
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(10)
        
        self.indicator = QLabel("◉")
        self.indicator.setFont(QFont("Consolas", 16))
        self.indicator.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent; border: none;")
        header_layout.addWidget(self.indicator)
        
        self.title_label = QLabel("✨ HOLOGRAPHIC OPTICS")
        self.title_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {CyberColors.CYAN_BRIGHT}; background: transparent; border: none;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # ✅ Pin indicator to show it stays on top
        pin_label = QLabel("📌")
        pin_label.setFont(QFont("Segoe UI Emoji", 12))
        pin_label.setToolTip("Pinned - Stays visible when app minimizes")
        pin_label.setStyleSheet("background: transparent; border: none;")
        header_layout.addWidget(pin_label)
        
        self.fps_label = QLabel("FPS:--")
        self.fps_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.fps_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent; border: none;")
        header_layout.addWidget(self.fps_label)
        
        min_btn = QPushButton("━")
        min_btn.setFixedSize(32, 32)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setFont(QFont("Arial", 12, QFont.Bold))
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 100, 150, 150);
                color: {CyberColors.CYAN_PRIMARY};
                border: 2px solid {CyberColors.CYAN_DARK};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: rgba(0, 150, 200, 200);
                color: white;
                border-color: {CyberColors.CYAN_PRIMARY};
            }}
        """)
        min_btn.setToolTip("Minimize camera preview")
        min_btn.clicked.connect(self.hide)
        header_layout.addWidget(min_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFont(QFont("Arial", 14, QFont.Bold))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(100, 30, 30, 150);
                color: {CyberColors.ORANGE};
                border: 2px solid {CyberColors.ORANGE};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: rgba(200, 60, 60, 200);
                color: white;
            }}
        """)
        close_btn.setToolTip("Close camera preview")
        close_btn.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(close_btn)
        
        container_layout.addWidget(header)
        
        # Camera widget
        self.camera_widget = UltraHolographicCameraWidget()
        self.camera_widget.setFixedSize(452, 260)
        container_layout.addWidget(self.camera_widget)
        
        # Data Panel
        data_panel = QFrame()
        data_panel.setFixedHeight(85)
        data_panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 40, 60, 200),
                    stop:1 rgba(0, 20, 40, 200));
                border: 2px solid {CyberColors.CYAN_DARK};
                border-radius: 6px;
            }}
        """)
        
        data_layout = QHBoxLayout(data_panel)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.setSpacing(0)
        
        self.gesture_col = self._create_data_column("◢ GESTURE", "---", CyberColors.NEON_GREEN)
        data_layout.addWidget(self.gesture_col, stretch=1)
        
        sep1 = QFrame()
        sep1.setFixedWidth(2)
        sep1.setStyleSheet(f"background: {CyberColors.CYAN_DARK}; border: none;")
        data_layout.addWidget(sep1)
        
        self.direction_col = self._create_data_column("◢ VECTOR", "CENTER", CyberColors.CYAN_PRIMARY)
        data_layout.addWidget(self.direction_col, stretch=1)
        
        sep2 = QFrame()
        sep2.setFixedWidth(2)
        sep2.setStyleSheet(f"background: {CyberColors.CYAN_DARK}; border: none;")
        data_layout.addWidget(sep2)
        
        self.action_col = self._create_data_column("◢ ACTION", "STANDBY", CyberColors.GOLD)
        data_layout.addWidget(self.action_col, stretch=1)
        
        container_layout.addWidget(data_panel)
        
        # Status Bar with pin indicator
        self.status_bar = QLabel("📌 PINNED - Stays visible when app minimizes")
        self.status_bar.setFixedHeight(35)
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setFont(QFont("Consolas", 9, QFont.Bold))
        self.status_bar.setStyleSheet(f"""
            background: rgba(0, 20, 40, 200);
            color: {CyberColors.TEXT_DIM};
            border: 2px solid {CyberColors.CYAN_DARK};
            border-radius: 6px;
        """)
        container_layout.addWidget(self.status_bar)
        
        main_layout.addWidget(self.container)
    
    def _create_data_column(self, title, value, color):
        col = QFrame()
        col.setStyleSheet("background: transparent; border: none;")
        
        layout = QVBoxLayout(col)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Consolas", 8, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        layout.addWidget(title_lbl)
        
        value_lbl = QLabel(value)
        value_lbl.setFont(QFont("Consolas", 13, QFont.Bold))
        value_lbl.setAlignment(Qt.AlignCenter)
        value_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(value_lbl)
        
        col.value_label = value_lbl
        col.base_color = color
        
        return col
    
    def _apply_container_style(self, active):
        if active:
            self.container.setStyleSheet(f"""
                #hudContainer {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 30, 50, 245),
                        stop:0.5 rgba(0, 20, 40, 250),
                        stop:1 rgba(0, 30, 50, 245));
                    border: 3px solid {CyberColors.CYAN_PRIMARY};
                    border-radius: 10px;
                }}
            """)
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(40)
            glow.setColor(QColor(0, 255, 255, 200))
            glow.setOffset(0, 0)
            self.container.setGraphicsEffect(glow)
        else:
            self.container.setStyleSheet(f"""
                #hudContainer {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 20, 35, 240),
                        stop:0.5 rgba(0, 15, 30, 245),
                        stop:1 rgba(0, 20, 35, 240));
                    border: 2px solid {CyberColors.CYAN_DARK};
                    border-radius: 10px;
                }}
            """)
            self.container.setGraphicsEffect(None)
    
    def _animate(self):
        self.animation_frame = (self.animation_frame + 1) % 360
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.15)
        alpha = int(180 + 75 * pulse)
        self.indicator.setStyleSheet(f"color: rgba(0, 255, 200, {alpha}); background: transparent; border: none;")
    
    def _on_close_clicked(self):
        """Handle close button - just hide, don't destroy"""
        self.hide()
        self.closed.emit()
    
    def start_preview(self):
        self.is_active = True
        self._apply_container_style(True)
        self.status_bar.setText("◉ HOLOGRAPHIC FEED ACTIVE - 📌 PINNED")
        self.status_bar.setStyleSheet(f"""
            background: rgba(0, 100, 80, 150);
            color: {CyberColors.NEON_GREEN};
            border: 2px solid {CyberColors.NEON_GREEN};
            border-radius: 6px;
        """)
        self.title_label.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent; border: none;")
        self.anim_timer.start(200)  # ✅ CHANGED: 5 FPS for floating window animation
        self.camera_widget.set_active(True)
    
    def stop_preview(self):
        self.is_active = False
        self.anim_timer.stop()
        self._apply_container_style(False)
        self.camera_widget.clear_frame()
        self.camera_widget.set_active(False)
        self.status_bar.setText("📌 PINNED - Stays visible when app minimizes")
        self.status_bar.setStyleSheet(f"""
            background: rgba(0, 20, 40, 200);
            color: {CyberColors.TEXT_DIM};
            border: 2px solid {CyberColors.CYAN_DARK};
            border-radius: 6px;
        """)
        self.title_label.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent; border: none;")
        self.indicator.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent; border: none;")
        self.fps_label.setText("FPS:--")
        self.fps_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent; border: none;")
        self._reset_data_columns()
    
    def _reset_data_columns(self):
        self.gesture_col.value_label.setText("---")
        self.gesture_col.value_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        self.direction_col.value_label.setText("CENTER")
        self.direction_col.value_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        self.action_col.value_label.setText("STANDBY")
        self.action_col.value_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
    
    def update_frame(self, frame):
        """Update frame - CRASH-SAFE VERSION"""
        if not self.is_active:
            return
        if frame is None:
            return
        try:
            if self.camera_widget:
                self.camera_widget.update_frame(frame)
        except Exception:
            pass
    
    def update_gesture(self, gesture):
        if not self.is_active:
            return
        icons = {"FIST": "✊", "PALM": "✋", "POINT": "☝", "PEACE": "✌",
                 "THUMBS_UP": "👍", "ROCK": "🤘", "OK": "👌"}
        if gesture and gesture != "NONE":
            icon = icons.get(gesture, "●")
            self.gesture_col.value_label.setText(f"{icon} {gesture}")
            self.gesture_col.value_label.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        else:
            self.gesture_col.value_label.setText("---")
            self.gesture_col.value_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
    
    def update_direction(self, direction):
        if not self.is_active:
            return
        icons = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶", "NONE": "◎", "CENTER": "◎"}
        if isinstance(direction, Direction):
            dir_name = direction.value
        elif hasattr(direction, 'value'):
            dir_name = direction.value
        else:
            dir_name = str(direction)
        icon = icons.get(dir_name, "◎")
        display = dir_name if dir_name != "NONE" else "CENTER"
        self.direction_col.value_label.setText(f"{icon} {display}")
        if dir_name not in ["NONE", "CENTER"]:
            self.direction_col.value_label.setStyleSheet(f"color: {CyberColors.CYAN_BRIGHT}; background: transparent;")
        else:
            self.direction_col.value_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
    
    def update_action(self, action):
        if not self.is_active:
            return
        if action:
            self.action_col.value_label.setText(action[:12])
            self.action_col.value_label.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        else:
            self.action_col.value_label.setText("STANDBY")
            self.action_col.value_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
    
    def update_fps(self, fps):
        if not self.is_active:
            return
        self.fps_label.setText(f"FPS:{fps:02d}")
        if fps >= 25:
            color = CyberColors.NEON_GREEN
        elif fps >= 15:
            color = CyberColors.GOLD
        else:
            color = CyberColors.ORANGE
        self.fps_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.setCursor(Qt.OpenHandCursor)