"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GAMING MODE - UI COMPONENTS                               ║
║                    🔮 FUTURISTIC HOLOGRAM DESIGN 🔮                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✅ Perfect alignment - NO overlapping                                       ║
║  ✅ Fixed heights for all elements                                           ║
║  ✅ Futuristic holographic styling                                           ║
║  ✅ Dynamic Internal/External mode                                           ║
║  ✅ Enhanced with hologram scan line effects                                 ║
║  ✅ Pulsing glow animations                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QRadialGradient

from gaming_mode.constants import CyberColors


# ═══════════════════════════════════════════════════════════════════════════════
# CYBER BUTTON COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════
class CyberButton(QPushButton):
    """Cyberpunk HUD-style button with glow effects"""
    
    def __init__(self, text, color=None, parent=None):
        super().__init__(text, parent)
        self.base_color = color or CyberColors.CYAN_PRIMARY
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Consolas", 10, QFont.Bold))
        self._apply_style()
    
    def _apply_style(self):
        c = self.base_color.lstrip('#')
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r},{g},{b}, 0.05),
                    stop:0.5 rgba({r},{g},{b}, 0.15),
                    stop:1 rgba({r},{g},{b}, 0.05));
                color: {self.base_color};
                border: 2px solid {self.base_color};
                border-radius: 6px;
                padding: 8px 16px;
                font-family: Consolas;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r},{g},{b}, 0.2),
                    stop:0.5 rgba({r},{g},{b}, 0.4),
                    stop:1 rgba({r},{g},{b}, 0.2));
                color: white;
                border: 2px solid rgba({r},{g},{b}, 1);
            }}
            QPushButton:pressed {{
                background: rgba({r},{g},{b}, 0.5);
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r},{g},{b}, 0.3),
                    stop:0.5 rgba({r},{g},{b}, 0.5),
                    stop:1 rgba({r},{g},{b}, 0.3));
                color: white;
                border: 3px solid {self.base_color};
            }}
        """)
    
    def add_glow(self, radius=15, alpha=100):
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(radius)
        c = self.base_color.lstrip('#')
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        glow.setColor(QColor(r, g, b, alpha))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)


# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 HOLOGRAPHIC FRAME - Enhanced with scan line and glow effects
# ═══════════════════════════════════════════════════════════════════════════════
class HolographicFrame(QFrame):
    """Base holographic frame with scan line and glow effects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Animation state
        self.scan_offset = 0
        self.glow_intensity = 0
        self.glow_direction = 1
        
        # Timers
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self._update_scan)
        
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._update_glow)
    
    def start_animations(self):
        """Start holographic animations"""
        self.scan_timer.start(40)  # 25 FPS scan line
        self.glow_timer.start(30)   # Glow pulse
    
    def stop_animations(self):
        """Stop all animations"""
        self.scan_timer.stop()
        self.glow_timer.stop()
    
    def _update_scan(self):
        """Update scan line position"""
        self.scan_offset = (self.scan_offset + 3) % (self.height() + 30)
        self.update()
    
    def _update_glow(self):
        """Update glow pulse intensity"""
        self.glow_intensity += 0.05 * self.glow_direction
        if self.glow_intensity >= 1.0:
            self.glow_direction = -1
        elif self.glow_intensity <= 0.0:
            self.glow_direction = 1
        self.update()
    
    def paintEvent(self, event):
        """Paint holographic effects"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Border glow effect
        glow_alpha = int(30 + 40 * self.glow_intensity)
        
        # Corner accents (futuristic style)
        corner_size = 30
        accent_color = QColor(0, 255, 255, glow_alpha)
        pen = QPen(accent_color, 2)
        painter.setPen(pen)
        
        # Top-left corner
        painter.drawLine(0, 0, corner_size, 0)
        painter.drawLine(0, 0, 0, corner_size)
        
        # Top-right corner
        painter.drawLine(self.width() - corner_size, 0, self.width(), 0)
        painter.drawLine(self.width(), 0, self.width(), corner_size)
        
        # Bottom-left corner
        painter.drawLine(0, self.height() - corner_size, 0, self.height())
        painter.drawLine(0, self.height(), corner_size, self.height())
        
        # Bottom-right corner
        painter.drawLine(self.width() - corner_size, self.height(), self.width(), self.height())
        painter.drawLine(self.width(), self.height() - corner_size, self.width(), self.height())
        
        # Scan line effect (moving hologram scan)
        if self.scan_timer.isActive():
            scan_y = self.scan_offset
            if 0 <= scan_y <= self.height():
                gradient = QLinearGradient(0, scan_y - 20, 0, scan_y + 20)
                gradient.setColorAt(0, QColor(0, 255, 255, 0))
                gradient.setColorAt(0.5, QColor(0, 255, 255, 40))
                gradient.setColorAt(1, QColor(0, 255, 255, 0))
                painter.fillRect(0, scan_y - 20, self.width(), 40, gradient)
        
        # Center radial glow (energy effect)
        center_x = self.width() // 2
        center_y = self.height() // 2
        radial = QRadialGradient(center_x, center_y, max(self.width(), self.height()) // 2)
        radial.setColorAt(0, QColor(0, 200, 255, int(10 * self.glow_intensity)))
        radial.setColorAt(0.5, QColor(0, 150, 200, int(5 * self.glow_intensity)))
        radial.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), radial)
        
        painter.end()
    
    def cleanup(self):
        """Cleanup timers"""
        self.stop_animations()
        try:
            self.scan_timer.deleteLater()
            self.glow_timer.deleteLater()
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# GESTURE HUD PANEL - FUTURISTIC HOLOGRAM VERSION
# ═══════════════════════════════════════════════════════════════════════════════
class GestureHUDPanel(QFrame):
    """
    🔮 FUTURISTIC GESTURE HUD PANEL 🔮
    
    Height Breakdown (Total: ~350px minimum):
    - Header:           30px
    - Gesture Display:  80px
    - Mode Indicator:   22px
    - Mappings:         95px
    - Spacer:           Flexible
    - Game Status:      22px
    - System Status:    42px
    - Margins/Spacing:  ~60px
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Fixed dimensions
        self.setFixedWidth(170)
        self.setMinimumHeight(350)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        # State
        self.current_mode = "INTERNAL"
        self.is_active = False
        self._pulse_state = False
        
        # Initialize attributes
        self.pulse_timer = None
        self.sys_indicator = None
        self.trk_indicator = None
        
        # Apply main style
        self.setStyleSheet(f"""
            GestureHUDPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(8, 20, 40, 0.95),
                    stop:0.5 rgba(5, 15, 35, 0.98),
                    stop:1 rgba(3, 10, 25, 0.95));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {CyberColors.CYAN_PRIMARY},
                    stop:0.5 {CyberColors.CYAN_DARK},
                    stop:1 {CyberColors.CYAN_PRIMARY});
                border-radius: 12px;
            }}
        """)
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_animations(self):
        """Setup pulse animation timer"""
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse_update)
        self.pulse_timer.start(700)
    
    def _pulse_update(self):
        """Pulse animation for indicators"""
        if self.is_active and self.sys_indicator:
            self._pulse_state = not self._pulse_state
            char = "◉" if self._pulse_state else "◎"
            self.sys_indicator.setText(char)
    
    def _setup_ui(self):
        """Setup all UI components with fixed heights"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # ═══════════════════════════════════════════════════════════════
        # HEADER - 30px
        # ═══════════════════════════════════════════════════════════════
        header = QFrame()
        header.setFixedHeight(30)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.2 rgba(255, 215, 0, 0.2),
                    stop:0.5 rgba(255, 215, 0, 0.3),
                    stop:0.8 rgba(255, 215, 0, 0.2),
                    stop:1 transparent);
                border: none;
                border-bottom: 1px solid {CyberColors.GOLD};
            }}
        """)
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(4, 0, 4, 0)
        h_layout.setSpacing(0)
        
        h_left = QLabel("◢")
        h_left.setFont(QFont("Consolas", 10, QFont.Bold))
        h_left.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        h_layout.addWidget(h_left)
        
        h_title = QLabel("HUD")
        h_title.setFont(QFont("Consolas", 11, QFont.Bold))
        h_title.setAlignment(Qt.AlignCenter)
        h_title.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        h_layout.addWidget(h_title, 1)
        
        h_right = QLabel("◣")
        h_right.setFont(QFont("Consolas", 10, QFont.Bold))
        h_right.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        h_layout.addWidget(h_right)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════════
        # GESTURE DISPLAY - 80px
        # ═══════════════════════════════════════════════════════════════
        self.gesture_frame = QFrame()
        self.gesture_frame.setFixedHeight(80)
        self._set_gesture_style(False)
        
        g_layout = QVBoxLayout(self.gesture_frame)
        g_layout.setContentsMargins(4, 4, 4, 4)
        g_layout.setSpacing(0)
        
        # Icon - 45px
        self.gesture_icon = QLabel("◎")
        self.gesture_icon.setFixedHeight(45)
        self.gesture_icon.setFont(QFont("Segoe UI Emoji", 28))
        self.gesture_icon.setAlignment(Qt.AlignCenter)
        self.gesture_icon.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        g_layout.addWidget(self.gesture_icon)
        
        # Name - 20px
        self.gesture_name = QLabel("AWAITING")
        self.gesture_name.setFixedHeight(20)
        self.gesture_name.setFont(QFont("Consolas", 10, QFont.Bold))
        self.gesture_name.setAlignment(Qt.AlignCenter)
        self.gesture_name.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        g_layout.addWidget(self.gesture_name)
        
        layout.addWidget(self.gesture_frame)
        
        # ═══════════════════════════════════════════════════════════════
        # MODE INDICATOR - 22px
        # ═══════════════════════════════════════════════════════════════
        self.mode_frame = QFrame()
        self.mode_frame.setFixedHeight(22)
        self._set_mode_style("INTERNAL")
        
        m_layout = QHBoxLayout(self.mode_frame)
        m_layout.setContentsMargins(8, 0, 8, 0)
        m_layout.setSpacing(4)
        
        self.mode_icon = QLabel("▶")
        self.mode_icon.setFont(QFont("Consolas", 8))
        self.mode_icon.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        m_layout.addWidget(self.mode_icon)
        
        self.mode_label = QLabel("INTERNAL")
        self.mode_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.mode_label.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        m_layout.addWidget(self.mode_label)
        
        m_layout.addStretch()
        
        layout.addWidget(self.mode_frame)
        
        # ═══════════════════════════════════════════════════════════════
        # INTERNAL MAPPINGS - 95px
        # ═══════════════════════════════════════════════════════════════
        self.internal_frame = QFrame()
        self.internal_frame.setFixedHeight(95)
        self.internal_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 255, 136, 0.03);
                border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 6px;
            }}
        """)
        
        i_layout = QVBoxLayout(self.internal_frame)
        i_layout.setContentsMargins(6, 4, 6, 4)
        i_layout.setSpacing(1)
        
        # Header - 14px
        i_header = QLabel("▸ GAME ACTIONS")
        i_header.setFixedHeight(14)
        i_header.setFont(QFont("Consolas", 7, QFont.Bold))
        i_header.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        i_layout.addWidget(i_header)
        
        # Mappings - 4 rows x 18px = 72px
        internal_map = [
            ("▲", "UP", "JUMP", CyberColors.NEON_GREEN),
            ("▼", "DOWN", "SLIDE", CyberColors.ORANGE),
            ("◀", "LEFT", "DODGE L", CyberColors.CYAN_PRIMARY),
            ("▶", "RIGHT", "DODGE R", CyberColors.MAGENTA),
        ]
        
        for icon, dir_name, action, color in internal_map:
            row = self._create_map_row(icon, dir_name, action, color, 18)
            i_layout.addWidget(row)
        
        layout.addWidget(self.internal_frame)
        
        # ═══════════════════════════════════════════════════════════════
        # EXTERNAL MAPPINGS - 95px (Hidden by default)
        # ═══════════════════════════════════════════════════════════════
        self.external_frame = QFrame()
        self.external_frame.setFixedHeight(95)
        self.external_frame.setVisible(False)
        self.external_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 165, 0, 0.03);
                border: 1px solid rgba(255, 165, 0, 0.3);
                border-radius: 6px;
            }}
        """)
        
        e_layout = QVBoxLayout(self.external_frame)
        e_layout.setContentsMargins(6, 4, 6, 4)
        e_layout.setSpacing(1)
        
        # Header - 14px
        e_header = QLabel("▸ KEYBOARD")
        e_header.setFixedHeight(14)
        e_header.setFont(QFont("Consolas", 7, QFont.Bold))
        e_header.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent;")
        e_layout.addWidget(e_header)
        
        # Mappings
        external_map = [
            ("▲", "UP", "W", CyberColors.NEON_GREEN),
            ("▼", "DOWN", "S", CyberColors.ORANGE),
            ("◀", "LEFT", "A", CyberColors.CYAN_PRIMARY),
            ("▶", "RIGHT", "D", CyberColors.MAGENTA),
        ]
        
        for icon, dir_name, action, color in external_map:
            row = self._create_map_row(icon, dir_name, action, color, 18)
            e_layout.addWidget(row)
        
        layout.addWidget(self.external_frame)
        
        # ═══════════════════════════════════════════════════════════════
        # FLEXIBLE SPACER
        # ═══════════════════════════════════════════════════════════════
        layout.addStretch(1)
        
        # ═══════════════════════════════════════════════════════════════
        # GAME STATUS - 22px
        # ═══════════════════════════════════════════════════════════════
        self.game_frame = QFrame()
        self.game_frame.setFixedHeight(22)
        self.game_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 100, 150, 0.2);
                border: 1px solid {CyberColors.CYAN_DARK};
                border-radius: 4px;
            }}
        """)
        
        gm_layout = QHBoxLayout(self.game_frame)
        gm_layout.setContentsMargins(6, 0, 6, 0)
        gm_layout.setSpacing(4)
        
        gm_icon = QLabel("🎮")
        gm_icon.setFont(QFont("Segoe UI Emoji", 9))
        gm_icon.setStyleSheet("background: transparent;")
        gm_layout.addWidget(gm_icon)
        
        self.game_label = QLabel("NO GAME")
        self.game_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.game_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        gm_layout.addWidget(self.game_label)
        
        gm_layout.addStretch()
        
        layout.addWidget(self.game_frame)
        
        # ═══════════════════════════════════════════════════════════════
        # SYSTEM STATUS - 42px
        # ═══════════════════════════════════════════════════════════════
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(42)
        self._set_status_style(False)
        
        s_layout = QVBoxLayout(self.status_frame)
        s_layout.setContentsMargins(6, 3, 6, 3)
        s_layout.setSpacing(0)
        
        # SYS Row - 18px
        sys_row = QWidget()
        sys_row.setFixedHeight(18)
        sys_row.setStyleSheet("background: transparent;")
        sr_layout = QHBoxLayout(sys_row)
        sr_layout.setContentsMargins(0, 0, 0, 0)
        sr_layout.setSpacing(3)
        
        self.sys_indicator = QLabel("○")
        self.sys_indicator.setFixedWidth(10)
        self.sys_indicator.setFont(QFont("Consolas", 8))
        self.sys_indicator.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        sr_layout.addWidget(self.sys_indicator)
        
        sys_lbl = QLabel("SYS:")
        sys_lbl.setFixedWidth(25)
        sys_lbl.setFont(QFont("Consolas", 7, QFont.Bold))
        sys_lbl.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
        sr_layout.addWidget(sys_lbl)
        
        self.sys_status = QLabel("READY")
        self.sys_status.setFont(QFont("Consolas", 7, QFont.Bold))
        self.sys_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        sr_layout.addWidget(self.sys_status)
        sr_layout.addStretch()
        
        s_layout.addWidget(sys_row)
        
        # TRK Row - 18px
        trk_row = QWidget()
        trk_row.setFixedHeight(18)
        trk_row.setStyleSheet("background: transparent;")
        tr_layout = QHBoxLayout(trk_row)
        tr_layout.setContentsMargins(0, 0, 0, 0)
        tr_layout.setSpacing(3)
        
        self.trk_indicator = QLabel("○")
        self.trk_indicator.setFixedWidth(10)
        self.trk_indicator.setFont(QFont("Consolas", 8))
        self.trk_indicator.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        tr_layout.addWidget(self.trk_indicator)
        
        trk_lbl = QLabel("TRK:")
        trk_lbl.setFixedWidth(25)
        trk_lbl.setFont(QFont("Consolas", 7, QFont.Bold))
        trk_lbl.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
        tr_layout.addWidget(trk_lbl)
        
        self.track_status = QLabel("STANDBY")
        self.track_status.setFont(QFont("Consolas", 7, QFont.Bold))
        self.track_status.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        tr_layout.addWidget(self.track_status)
        tr_layout.addStretch()
        
        s_layout.addWidget(trk_row)
        
        layout.addWidget(self.status_frame)
    
    def _create_map_row(self, icon, direction, action, color, height):
        """Create a mapping row"""
        row = QWidget()
        row.setFixedHeight(height)
        row.setStyleSheet("background: transparent;")
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(3)
        
        # Icon
        i_lbl = QLabel(icon)
        i_lbl.setFixedWidth(12)
        i_lbl.setFont(QFont("Consolas", 9, QFont.Bold))
        i_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(i_lbl)
        
        # Direction
        d_lbl = QLabel(direction)
        d_lbl.setFixedWidth(35)
        d_lbl.setFont(QFont("Consolas", 7, QFont.Bold))
        d_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(d_lbl)
        
        # Arrow
        a_lbl = QLabel("→")
        a_lbl.setFixedWidth(10)
        a_lbl.setFont(QFont("Consolas", 7))
        a_lbl.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        layout.addWidget(a_lbl)
        
        # Action
        act_lbl = QLabel(action)
        act_lbl.setFont(QFont("Consolas", 7))
        act_lbl.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
        layout.addWidget(act_lbl)
        
        layout.addStretch()
        
        return row
    
    def _set_gesture_style(self, active):
        """Set gesture frame style"""
        if active:
            self.gesture_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 255, 136, 0.15),
                        stop:1 rgba(0, 255, 136, 0.05));
                    border: 2px solid {CyberColors.NEON_GREEN};
                    border-radius: 8px;
                }}
            """)
        else:
            self.gesture_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 150, 200, 0.08),
                        stop:1 rgba(0, 100, 150, 0.03));
                    border: 2px solid {CyberColors.CYAN_DARK};
                    border-radius: 8px;
                }}
            """)
    
    def _set_mode_style(self, mode):
        """Set mode frame style"""
        if mode == "INTERNAL":
            self.mode_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(0, 200, 255, 0.1);
                    border: 1px solid {CyberColors.CYAN_PRIMARY};
                    border-radius: 4px;
                }}
            """)
        else:
            self.mode_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(255, 165, 0, 0.1);
                    border: 1px solid {CyberColors.ORANGE};
                    border-radius: 4px;
                }}
            """)
    
    def _set_status_style(self, active):
        """Set status frame style"""
        if active:
            self.status_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 100, 80, 0.4),
                        stop:1 rgba(0, 60, 50, 0.4));
                    border: 1px solid {CyberColors.NEON_GREEN};
                    border-radius: 5px;
                }}
            """)
        else:
            self.status_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 50, 80, 0.4),
                        stop:1 rgba(0, 30, 50, 0.4));
                    border: 1px solid {CyberColors.CYAN_DARK};
                    border-radius: 5px;
                }}
            """)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def set_gesture(self, gesture):
        """Update gesture display"""
        icons = {
            "FIST": "✊", "PALM": "✋", "POINT": "☝", "PEACE": "✌",
            "THUMBS_UP": "👍", "ROCK": "🤘", "OK": "👌",
            "MOVE": "👆", "SCROLL": "✌", "DRAG": "🤟",
            "OPEN": "✋", "NONE": "◎"
        }
        
        if gesture and gesture.upper() != "NONE":
            self.gesture_icon.setText(icons.get(gesture.upper(), "●"))
            self.gesture_icon.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
            self.gesture_name.setText(gesture.upper()[:8])
            self.gesture_name.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
            self._set_gesture_style(True)
            
            self.trk_indicator.setText("◉")
            self.trk_indicator.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
            self.track_status.setText("ACTIVE")
            self.track_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        else:
            self.gesture_icon.setText("◎")
            self.gesture_icon.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            self.gesture_name.setText("AWAITING")
            self.gesture_name.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            self._set_gesture_style(False)
            
            if self.is_active:
                self.trk_indicator.setText("◎")
                self.trk_indicator.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
                self.track_status.setText("SEARCH")
                self.track_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
    
    def set_mode(self, mode):
        """Set mode (INTERNAL/EXTERNAL)"""
        self.current_mode = mode
        
        if mode == "INTERNAL":
            self.mode_icon.setText("▶")
            self.mode_icon.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
            self.mode_label.setText("INTERNAL")
            self.mode_label.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
            self._set_mode_style("INTERNAL")
            self.internal_frame.setVisible(True)
            self.external_frame.setVisible(False)
        else:
            self.mode_icon.setText("◆")
            self.mode_icon.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent;")
            self.mode_label.setText("EXTERNAL")
            self.mode_label.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent;")
            self._set_mode_style("EXTERNAL")
            self.internal_frame.setVisible(False)
            self.external_frame.setVisible(True)
    
    def set_active(self, active):
        """Set active state"""
        self.is_active = active
        
        if active:
            self.sys_indicator.setText("◉")
            self.sys_indicator.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
            self.sys_status.setText("ONLINE")
            self.sys_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
            
            self.trk_indicator.setText("◎")
            self.trk_indicator.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
            self.track_status.setText("SEARCH")
            self.track_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
            
            self._set_status_style(True)
        else:
            self.sys_indicator.setText("○")
            self.sys_indicator.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            self.sys_status.setText("READY")
            self.sys_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
            
            self.trk_indicator.setText("○")
            self.trk_indicator.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            self.track_status.setText("STANDBY")
            self.track_status.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            
            self._set_status_style(False)
    
    def set_game(self, game_name):
        """Set game name"""
        if game_name:
            name = game_name[:10] if len(game_name) > 10 else game_name
            self.game_label.setText(name.upper())
            self.game_label.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
            self.game_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(0, 255, 136, 0.1);
                    border: 1px solid {CyberColors.NEON_GREEN};
                    border-radius: 4px;
                }}
            """)
        else:
            self.game_label.setText("NO GAME")
            self.game_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            self.game_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(0, 100, 150, 0.2);
                    border: 1px solid {CyberColors.CYAN_DARK};
                    border-radius: 4px;
                }}
            """)
    
    def cleanup(self):
        """Cleanup"""
        try:
            if self.pulse_timer:
                self.pulse_timer.stop()
                self.pulse_timer.deleteLater()
                self.pulse_timer = None
        except:
            pass