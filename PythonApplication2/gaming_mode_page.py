"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  █████╗ ██╗   ██╗██████╗ ███████╗██╗   ██╗██╗██╗  ██╗                      ║
║ ██╔══██╗██║   ██║██╔══██╗██╔════╝██║   ██║██║╚██╗██╔╝                      ║
║ ███████║██║   ██║██████╔╝█████╗  ██║   ██║██║ ╚███╔╝                       ║
║ ██╔══██║██║   ██║██╔══██╗██╔══╝  ╚██╗ ██╔╝██║ ██╔██╗                       ║
║ ██║  ██║╚██████╔╝██║  ██║███████╗ ╚████╔╝ ██║██╔╝ ██╗                      ║
║ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═╝                      ║
║                                                                              ║
║        ◢◤ ULTRA CYBERPUNK HOLOGRAPHIC GAMING INTERFACE v3.5 ◢◤             ║
║                    🎮 GAMING CONTROLLER HUD VERSION 🎮                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✅ CHANGE 1: HologramCenterPanel - grid, hex corners, radar sweep         ║
║  ✅ CHANGE 2: Center panel header - aggressive gaming style                 ║
║  ✅ CHANGE 3: No-game placeholder - controller HUD with D-pad & buttons    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import time
import gc
import math
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QApplication, QComboBox,
    QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, Property, QRectF, QPointF
from PySide6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPen, QRadialGradient,
    QConicalGradient, QPainterPath, QBrush
)

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT FROM GAMING MODE PACKAGE
# ═══════════════════════════════════════════════════════════════════════════════
from gaming_mode import (
    Direction,
    CyberColors,
    DIRECTION_THRESHOLD,
    MAX_EMPTY_FRAMES,
    VERSION,
    VERSION_FEATURES,
    GAMING_CANVAS_AVAILABLE,
    GAME_CONTROLLER_AVAILABLE,
    GamingCanvas,
    game_controller,
    safe_execute,
    CyberButton,
    CyberpunkDirectionController,
    FloatingCameraWindow,
)

# ═══════════════════════════════════════════════════════════════════════════════
# TIMER INTERVALS
# ═══════════════════════════════════════════════════════════════════════════════
CAMERA_TIMER_INTERVAL = 33
ANIMATION_TIMER_INTERVAL = 50
FPS_UPDATE_INTERVAL = 1000
HEALTH_CHECK_INTERVAL = 3000
GESTURE_THROTTLE = 0.15
DIRECTION_THROTTLE = 0.05

# ═══════════════════════════════════════════════════════════════════════════════
# EXTERNAL IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════
import mode_manager
import config
import hand_tracker


# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 ENHANCED HOLOGRAPHIC CENTER PANEL — FUTURISTIC OVERLAY EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════
import math

class HologramCenterPanel(QFrame):
    """Ultra-futuristic center panel with layered holographic effects"""
   
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("centerPanel")
       
        self.scan_offset = 0
        self.glow_intensity = 0.0
        self.glow_direction = 1
        self.radar_angle = 0.0
        self.grid_pulse = 0.0
        self.grid_pulse_dir = 1
        self.hex_phase = 0.0
        self.particle_phase = 0.0
       
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self._update_scan)
       
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._update_glow)
       
        self.radar_timer = QTimer(self)
        self.radar_timer.timeout.connect(self._update_radar)
       
        self.setStyleSheet("HologramCenterPanel { background: transparent; }")
        # ✅ ADD THIS — Auto-start idle animations
        QTimer.singleShot(100, self.start_animations)

    def start_animations(self):
        self.scan_timer.start(40)
        self.glow_timer.start(30)
        self.radar_timer.start(25)
   
    def stop_animations(self):
        self.scan_timer.stop()
        self.glow_timer.stop()
        self.radar_timer.stop()
   
    def _update_scan(self):
        self.scan_offset = (self.scan_offset + 2) % max(self.height(), 1)
        self.update()
   
    def _update_glow(self):
        self.glow_intensity += 0.04 * self.glow_direction
        if self.glow_intensity >= 1.0:
            self.glow_direction = -1
        elif self.glow_intensity <= 0.0:
            self.glow_direction = 1
       
        self.grid_pulse += 0.03 * self.grid_pulse_dir
        if self.grid_pulse >= 1.0:
            self.grid_pulse_dir = -1
        elif self.grid_pulse <= 0.0:
            self.grid_pulse_dir = 1
       
        self.hex_phase += 0.02
        if self.hex_phase > 2 * math.pi:
            self.hex_phase -= 2 * math.pi
       
        self.particle_phase += 0.05
        if self.particle_phase > 2 * math.pi:
            self.particle_phase -= 2 * math.pi
   
    def _update_radar(self):
        self.radar_angle = (self.radar_angle + 2.5) % 360
        self.update()
   
    def paintEvent(self, event):
        super().paintEvent(event)
       
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
       
        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2
       
        # ── 1) SUBTLE GRID OVERLAY ──
        grid_alpha = int(6 + 10 * self.grid_pulse)
        grid_pen = QPen(QColor(0, 255, 255, grid_alpha), 1, Qt.DotLine)
        painter.setPen(grid_pen)
       
        spacing = 50
        for x in range(0, w, spacing):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, spacing):
            painter.drawLine(0, y, w, y)
       
        # ── 2) HEX CORNER BRACKETS ──
        bracket_len = 45
        bi = 12  # bracket inset
        hex_alpha = int(60 + 120 * abs(math.sin(self.hex_phase)))
        hex_pen = QPen(QColor(0, 255, 255, hex_alpha), 2)
        painter.setPen(hex_pen)
       
        # Top-left
        painter.drawLine(bi, 2, bi + bracket_len, 2)
        painter.drawLine(2, bi, 2, bi + bracket_len)
        painter.drawLine(2, bi, bi, 2)
       
        # Top-right
        painter.drawLine(w - bi - bracket_len, 2, w - bi, 2)
        painter.drawLine(w - 2, bi, w - 2, bi + bracket_len)
        painter.drawLine(w - bi, 2, w - 2, bi)
       
        # Bottom-left
        painter.drawLine(bi, h - 2, bi + bracket_len, h - 2)
        painter.drawLine(2, h - bi - bracket_len, 2, h - bi)
        painter.drawLine(2, h - bi, bi, h - 2)
       
        # Bottom-right
        painter.drawLine(w - bi - bracket_len, h - 2, w - bi, h - 2)
        painter.drawLine(w - 2, h - bi - bracket_len, w - 2, h - bi)
        painter.drawLine(w - bi, h - 2, w - 2, h - bi)
       
        # ── 3) INNER BORDER GLOW LINES (secondary brackets) ──
        inner_alpha = int(20 + 30 * self.glow_intensity)
        inner_pen = QPen(QColor(0, 200, 255, inner_alpha), 1)
        painter.setPen(inner_pen)
        inner_offset = 8
        inner_len = 30
       
        # Top-left inner
        painter.drawLine(inner_offset + bi, inner_offset, inner_offset + bi + inner_len, inner_offset)
        painter.drawLine(inner_offset, inner_offset + bi, inner_offset, inner_offset + bi + inner_len)
       
        # Top-right inner
        painter.drawLine(w - inner_offset - bi - inner_len, inner_offset, w - inner_offset - bi, inner_offset)
        painter.drawLine(w - inner_offset, inner_offset + bi, w - inner_offset, inner_offset + bi + inner_len)
       
        # Bottom-left inner
        painter.drawLine(inner_offset + bi, h - inner_offset, inner_offset + bi + inner_len, h - inner_offset)
        painter.drawLine(inner_offset, h - inner_offset - bi - inner_len, inner_offset, h - inner_offset - bi)
       
        # Bottom-right inner
        painter.drawLine(w - inner_offset - bi - inner_len, h - inner_offset, w - inner_offset - bi, h - inner_offset)
        painter.drawLine(w - inner_offset, h - inner_offset - bi - inner_len, w - inner_offset, h - inner_offset - bi)
       
        # ── 4) CENTER CROSSHAIR ──
        cross_alpha = int(15 + 25 * self.glow_intensity)
        cross_pen = QPen(QColor(0, 255, 255, cross_alpha), 1)
        painter.setPen(cross_pen)
        cross_size = 20
        gap = 6
       
        painter.drawLine(cx - cross_size, cy, cx - gap, cy)
        painter.drawLine(cx + gap, cy, cx + cross_size, cy)
        painter.drawLine(cx, cy - cross_size, cx, cy - gap)
        painter.drawLine(cx, cy + gap, cx, cy + cross_size)
       
        # Small corner ticks on crosshair
        tick = 5
        for dx, dy in [(-gap, -gap), (gap, -gap), (-gap, gap), (gap, gap)]:
            tx, ty = cx + dx, cy + dy
            painter.drawLine(tx, ty, tx + (tick if dx > 0 else -tick), ty)
            painter.drawLine(tx, ty, tx, ty + (tick if dy > 0 else -tick))
       
        # ── 5) RADAR SWEEP (bottom-right) — ENHANCED & BIGGER ──
        radar_cx = w - 75
        radar_cy = h - 75
        radar_r = 50
       
        # Outer ring (pulsing)
        outer_alpha = int(15 + 20 * self.glow_intensity)
        outer_pen = QPen(QColor(0, 255, 200, outer_alpha), 2)
        painter.setPen(outer_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(radar_cx, radar_cy), radar_r + 8, radar_r + 8)
       
        # Inner rings
        ring_pen = QPen(QColor(0, 255, 200, 18), 1)
        painter.setPen(ring_pen)
        for r in [radar_r, radar_r * 0.66, radar_r * 0.33]:
            painter.drawEllipse(QPointF(radar_cx, radar_cy), r, r)
       
        # Cross lines
        painter.drawLine(radar_cx - radar_r, radar_cy, radar_cx + radar_r, radar_cy)
        painter.drawLine(radar_cx, radar_cy - radar_r, radar_cx, radar_cy + radar_r)
       
        # Diagonal lines (subtle)
        diag_pen = QPen(QColor(0, 255, 200, 8), 1)
        painter.setPen(diag_pen)
        diag_len = radar_r * 0.7
        for angle_offset in [45, 135, 225, 315]:
            rad = math.radians(angle_offset)
            painter.drawLine(
                int(radar_cx), int(radar_cy),
                int(radar_cx + math.cos(rad) * diag_len),
                int(radar_cy + math.sin(rad) * diag_len)
            )
       
        # SWEEP ARC — BRIGHT & VISIBLE
        sweep_grad = QConicalGradient(radar_cx, radar_cy, -self.radar_angle)
        sweep_grad.setColorAt(0, QColor(0, 255, 200, 120))
        sweep_grad.setColorAt(0.08, QColor(0, 255, 200, 60))
        sweep_grad.setColorAt(0.15, QColor(0, 255, 200, 20))
        sweep_grad.setColorAt(0.25, QColor(0, 255, 200, 0))
        sweep_grad.setColorAt(1, QColor(0, 255, 200, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sweep_grad))
        painter.drawEllipse(QPointF(radar_cx, radar_cy), radar_r, radar_r)
       
        # Sweep line (bright leading edge)
        sweep_rad = math.radians(-self.radar_angle)
        sweep_end_x = radar_cx + math.cos(sweep_rad) * radar_r
        sweep_end_y = radar_cy + math.sin(sweep_rad) * radar_r
        sweep_line_pen = QPen(QColor(0, 255, 200, 180), 2)
        painter.setPen(sweep_line_pen)
        painter.drawLine(int(radar_cx), int(radar_cy), int(sweep_end_x), int(sweep_end_y))
       
        # Radar blips (moving dots)
        painter.setPen(Qt.NoPen)
        for i in range(4):
            angle_rad = math.radians(self.radar_angle * 0.7 + i * 90)
            dist = radar_r * (0.3 + 0.4 * abs(math.sin(self.particle_phase + i * 1.5)))
            bx = radar_cx + math.cos(angle_rad) * dist
            by = radar_cy + math.sin(angle_rad) * dist
            blip_alpha = int(60 + 140 * abs(math.sin(self.particle_phase + i * 0.8)))
            blip_size = 2 + abs(math.sin(self.particle_phase + i)) * 1.5
           
            # Blip glow
            painter.setBrush(QColor(0, 255, 200, blip_alpha // 3))
            painter.drawEllipse(QPointF(bx, by), blip_size + 3, blip_size + 3)
            # Blip core
            painter.setBrush(QColor(0, 255, 200, blip_alpha))
            painter.drawEllipse(QPointF(bx, by), blip_size, blip_size)
       
        # Radar center dot (pulsing)
        center_alpha = int(150 + 100 * self.glow_intensity)
        painter.setBrush(QColor(0, 255, 200, center_alpha))
        painter.drawEllipse(QPointF(radar_cx, radar_cy), 3, 3)
        # Center glow
        painter.setBrush(QColor(0, 255, 200, center_alpha // 4))
        painter.drawEllipse(QPointF(radar_cx, radar_cy), 6, 6)
       
        # Radar label
        radar_label_pen = QPen(QColor(0, 255, 200, int(40 + 30 * self.glow_intensity)), 1)
        painter.setPen(radar_label_pen)
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(int(radar_cx - radar_r - 5), int(radar_cy - radar_r - 14), "◉ RADAR")
        painter.drawText(int(radar_cx - 15), int(radar_cy + radar_r + 18), f"{self.radar_angle:05.1f}°")
       
        # ── 6) HORIZONTAL SCAN LINE ──
        if self.scan_timer.isActive():
            scan_y = self.scan_offset
            scan_grad = QLinearGradient(0, scan_y - 12, 0, scan_y + 12)
            scan_grad.setColorAt(0, QColor(0, 255, 255, 0))
            scan_grad.setColorAt(0.4, QColor(0, 255, 255, 25))
            scan_grad.setColorAt(0.5, QColor(0, 255, 255, 45))
            scan_grad.setColorAt(0.6, QColor(0, 255, 255, 25))
            scan_grad.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(scan_grad)
            painter.drawRect(0, scan_y - 12, w, 24)
           
            # Bright center line
            line_pen = QPen(QColor(0, 255, 255, 35), 1)
            painter.setPen(line_pen)
            painter.drawLine(0, scan_y, w, scan_y)
       
        # ── 7) FLOATING PARTICLES ──
        for i in range(6):
            px = (w * 0.15) + (w * 0.7) * abs(math.sin(self.particle_phase * 0.3 + i * 1.2))
            py = (h * 0.1) + (h * 0.8) * abs(math.cos(self.particle_phase * 0.2 + i * 0.9))
            p_alpha = int(20 + 40 * abs(math.sin(self.particle_phase + i * 0.8)))
            p_size = 1.5 + abs(math.sin(self.particle_phase + i)) * 1.5
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 255, 255, p_alpha))
            painter.drawEllipse(QPointF(px, py), p_size, p_size)
       
        # ── 8) AMBIENT RADIAL GLOW ──
        radial = QRadialGradient(cx, cy, max(w, h) * 0.45)
        radial.setColorAt(0, QColor(0, 200, 255, int(15 * self.glow_intensity)))
        radial.setColorAt(0.3, QColor(0, 150, 220, int(8 * self.glow_intensity)))
        radial.setColorAt(0.7, QColor(0, 80, 150, int(3 * self.glow_intensity)))
        radial.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(radial)
        painter.drawRect(self.rect())
       
        # ── 9) HUD TEXT OVERLAYS ──
        hud_alpha = int(30 + 25 * self.glow_intensity)
        hud_pen = QPen(QColor(0, 255, 255, hud_alpha), 1)
        painter.setPen(hud_pen)
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(bi + 6, bi + 20, "SYS://VIEWPORT.ACTIVE")
        painter.drawText(bi + 6, bi + 33, f"SCAN {self.scan_offset:03d}")
       
        # Top-right — scan info
        painter.drawText(w - 120, bi + 20, f"FRM {self.scan_offset:04d}")
       
        # Bottom-left
        painter.drawText(bi + 6, h - bi - 8, "◉ AUREVIX.GAMING.HUD")
       
        # ── 10) EDGE GLOW LINES (top & bottom) ──
        edge_alpha = int(10 + 20 * self.glow_intensity)
        edge_grad_top = QLinearGradient(0, 0, w, 0)
        edge_grad_top.setColorAt(0, QColor(0, 255, 255, 0))
        edge_grad_top.setColorAt(0.3, QColor(0, 255, 255, edge_alpha))
        edge_grad_top.setColorAt(0.5, QColor(0, 255, 200, edge_alpha + 10))
        edge_grad_top.setColorAt(0.7, QColor(0, 255, 255, edge_alpha))
        edge_grad_top.setColorAt(1, QColor(0, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(edge_grad_top)
        painter.drawRect(0, 0, w, 3)
       
        edge_grad_bot = QLinearGradient(0, 0, w, 0)
        edge_grad_bot.setColorAt(0, QColor(0, 255, 200, 0))
        edge_grad_bot.setColorAt(0.3, QColor(0, 255, 200, edge_alpha))
        edge_grad_bot.setColorAt(0.5, QColor(0, 255, 255, edge_alpha + 10))
        edge_grad_bot.setColorAt(0.7, QColor(0, 255, 200, edge_alpha))
        edge_grad_bot.setColorAt(1, QColor(0, 255, 200, 0))
        painter.setBrush(edge_grad_bot)
        painter.drawRect(0, h - 3, w, 3)
       
        painter.end()
   
    def cleanup(self):
        self.stop_animations()


# ═══════════════════════════════════════════════════════════════════════════════
# GAMING MODE PAGE - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════
class GamingModePage(QWidget):
    """Complete Cyberpunk Gaming Mode"""
   
    mode_closed = Signal()
    switch_to_desktop = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AUREVIX // GAMING SYSTEM")
        self.setMinimumSize(1200, 750)
       
        # State
        self.is_gaming_active = False
        self.current_game = None
        self.current_mode = "INTERNAL"
        self.gaming_canvas = None
        self.camera_started_by_gaming = False
        self.is_closing = False
       
        self.camera_was_active_before_entry = False
        self.floating_camera = None
        self.last_processed_frame_id = None
        self.last_frame_time = time.time()
       
        self.frame_count = 0
        self.current_fps = 0
        self.animation_frame = 0
       
        self.last_hand_x = 0.5
        self.last_hand_y = 0.5
        self.current_direction = Direction.NONE
        self.direction_threshold = DIRECTION_THRESHOLD
       
        self._last_gesture_time = 0
        self._last_direction_time = 0
        self.last_gesture = None
       
        self.setup_ui()
        self.apply_styles()
       
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self._safe_update_camera)
       
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.calculate_fps)
        self.fps_timer.start(FPS_UPDATE_INTERVAL)
       
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.check_camera_health)
       
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate)
       
        print("◉ Gaming Mode Page Initialized (CONTROLLER HUD v3.5)")

    def _animate(self):
        if self.is_closing:
            return
        self.animation_frame = (self.animation_frame + 1) % 360

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
       
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
       
        container_layout.addWidget(self._create_top_bar())
       
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
       
        content_layout.addWidget(self._create_left_panel())
        content_layout.addWidget(self._create_center_panel(), stretch=1)
       
        """self.gesture_hud = GestureHUDPanel()
        content_layout.addWidget(self.gesture_hud)"""
       
        container_layout.addWidget(content, stretch=1)
        main_layout.addWidget(container)

    def _create_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(55)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CyberColors.NAVY_DARKEST},
                    stop:0.3 {CyberColors.NAVY_DARKER},
                    stop:0.7 {CyberColors.NAVY_DARKER},
                    stop:1 {CyberColors.NAVY_DARKEST});
                border-bottom: 2px solid {CyberColors.CYAN_PRIMARY};
            }}
        """)
       
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 15, 0)
       
        logo = QLabel("◉")
        logo.setFont(QFont("Consolas", 20))
        logo.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        layout.addWidget(logo)
       
        title = QLabel("AUREVIX GAMING SYSTEM")
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        layout.addWidget(title)
       
        ver = QLabel(f"{VERSION} {VERSION_FEATURES} [HUD]")
        ver.setFont(QFont("Consolas", 9))
        ver.setStyleSheet(f"color: {CyberColors.NEON_PINK}; background: transparent; margin-left: 10px;")
        layout.addWidget(ver)
       
        layout.addStretch()
       
        self.top_status = QLabel("◈ SYSTEM READY ◈")
        self.top_status.setFont(QFont("Consolas", 11))
        self.top_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        layout.addWidget(self.top_status)
       
        layout.addStretch()
       
        exit_btn = QPushButton("✕ EXIT")
        exit_btn.setFixedSize(160, 36)
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setFont(QFont("Consolas", 10, QFont.Bold))
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 51, 51, 0.1),
                    stop:0.5 rgba(255, 51, 51, 0.3),
                    stop:1 rgba(255, 51, 51, 0.1));
                color: {CyberColors.RED};
                border: 2px solid {CyberColors.RED};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: rgba(255, 51, 51, 0.5);
                color: white;
            }}
        """)
        exit_btn.clicked.connect(self.exit_to_desktop)
       
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(15)
        glow.setColor(QColor(255, 51, 51, 100))
        glow.setOffset(0, 0)
        exit_btn.setGraphicsEffect(glow)
       
        layout.addWidget(exit_btn)
        return bar

    def _create_left_panel(self):
        """Left panel - unchanged from original"""
       
        panel_frame = QFrame()
        panel_frame.setFixedWidth(280)
        panel_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(13, 27, 42, 0.95),
                    stop:1 rgba(5, 10, 21, 0.95));
                border: 2px solid {CyberColors.CYAN_DARK};
                border-radius: 8px;
            }}
        """)
       
        panel_layout = QVBoxLayout(panel_frame)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
       
        header = QLabel("◉ CONTROL PANEL")
        header.setFont(QFont("Consolas", 11, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(35)
        header.setStyleSheet(f"""
            color: {CyberColors.CYAN_PRIMARY};
            background: {CyberColors.NAVY_DARKEST};
            border-bottom: 1px solid {CyberColors.CYAN_DARK};
            border-radius: 0px;
        """)
        panel_layout.addWidget(header)
       
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {CyberColors.NAVY_DARKEST}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {CyberColors.CYAN_DARK}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {CyberColors.CYAN_PRIMARY}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
       
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
       
        self.camera_btn = CyberButton("◎ CAMERA FEED 📌", CyberColors.ELECTRIC_BLUE)
        self.camera_btn.setFixedHeight(36)
        self.camera_btn.setCheckable(True)
        self.camera_btn.clicked.connect(self.toggle_floating_camera)
        content_layout.addWidget(self.camera_btn)
       
        self.direction_hud = CyberpunkDirectionController()
        dir_wrapper = QHBoxLayout()
        dir_wrapper.addStretch()
        dir_wrapper.addWidget(self.direction_hud)
        dir_wrapper.addStretch()
        content_layout.addLayout(dir_wrapper)
       
        self.gesture_status = QLabel("◈ READY ◈")
        self.gesture_status.setFixedHeight(20)
        self.gesture_status.setFont(QFont("Consolas", 9))
        self.gesture_status.setAlignment(Qt.AlignCenter)
        self.gesture_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY};")
        content_layout.addWidget(self.gesture_status)
       
        sep1 = QFrame()
        sep1.setFixedHeight(2)
        sep1.setStyleSheet(f"background: {CyberColors.CYAN_DARK};")
        content_layout.addWidget(sep1)
       
        mode_label = QLabel("◢ CONTROL MODE ◣")
        mode_label.setFixedHeight(22)
        mode_label.setFont(QFont("Consolas", 9, QFont.Bold))
        mode_label.setAlignment(Qt.AlignCenter)
        mode_label.setStyleSheet(f"color: {CyberColors.MAGENTA};")
        content_layout.addWidget(mode_label)
       
        # MODE SELECTION FRAME
        self.mode_selection_frame = QFrame()
        self.mode_selection_frame.setStyleSheet("background: transparent;")
        mode_sel_layout = QVBoxLayout(self.mode_selection_frame)
        mode_sel_layout.setContentsMargins(0, 0, 0, 0)
        mode_sel_layout.setSpacing(8)
       
        self.internal_btn = CyberButton("▶ INTERNAL", CyberColors.NEON_GREEN)
        self.internal_btn.setFixedHeight(38)
        self.internal_btn.clicked.connect(self.show_internal_games)
        mode_sel_layout.addWidget(self.internal_btn)
       
        self.external_btn = CyberButton("◆ EXTERNAL", CyberColors.ORANGE)
        self.external_btn.setFixedHeight(38)
        self.external_btn.clicked.connect(self.show_external_options)
        mode_sel_layout.addWidget(self.external_btn)
       
        content_layout.addWidget(self.mode_selection_frame)
       
        # INTERNAL GAMES FRAME
        self.internal_games_frame = QFrame()
        self.internal_games_frame.setVisible(False)
        self.internal_games_frame.setStyleSheet("background: transparent;")
        games_layout = QVBoxLayout(self.internal_games_frame)
        games_layout.setContentsMargins(0, 0, 0, 0)
        games_layout.setSpacing(8)
       
        back_int = QPushButton("◀ BACK")
        back_int.setFixedHeight(28)
        back_int.setCursor(Qt.PointingHandCursor)
        back_int.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {CyberColors.CYAN_PRIMARY};
                border: 1px solid {CyberColors.CYAN_DARK}; border-radius: 4px;
                font-family: Consolas; font-size: 9pt;
            }}
            QPushButton:hover {{ background: rgba(0,200,255,0.2); }}
        """)
        back_int.clicked.connect(self.show_mode_selection)
        games_layout.addWidget(back_int)
       
        games_title = QLabel("◢ SELECT GAME ◣")
        games_title.setFixedHeight(22)
        games_title.setFont(QFont("Consolas", 9, QFont.Bold))
        games_title.setAlignment(Qt.AlignCenter)
        games_title.setStyleSheet(f"color: {CyberColors.GOLD};")
        games_layout.addWidget(games_title)
       
        self.ai_trainer_btn = CyberButton("🎓 AI TRAINER", CyberColors.NEON_PURPLE)
        self.ai_trainer_btn.setFixedHeight(40)
        self.ai_trainer_btn.clicked.connect(self.show_ai_trainer_details)
        games_layout.addWidget(self.ai_trainer_btn)
       
        self.cyber_runner_btn = CyberButton("🏃 CYBER RUNNER", CyberColors.NEON_GREEN)
        self.cyber_runner_btn.setFixedHeight(40)
        self.cyber_runner_btn.clicked.connect(self.show_cyber_runner_details)
        games_layout.addWidget(self.cyber_runner_btn)
       
        games_layout.addStretch()
        content_layout.addWidget(self.internal_games_frame)
       
        # AI TRAINER DETAILS FRAME
        self.ai_trainer_details_frame = QFrame()
        self.ai_trainer_details_frame.setVisible(False)
        self.ai_trainer_details_frame.setStyleSheet("background: transparent;")
        ai_layout = QVBoxLayout(self.ai_trainer_details_frame)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(12)
       
        back_ai = QPushButton("◀ BACK")
        back_ai.setFixedHeight(28)
        back_ai.setCursor(Qt.PointingHandCursor)
        back_ai.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {CyberColors.CYAN_PRIMARY};
                border: 1px solid {CyberColors.CYAN_DARK}; border-radius: 4px;
                font-family: Consolas; font-size: 9pt;
            }}
            QPushButton:hover {{ background: rgba(0,200,255,0.2); }}
        """)
        back_ai.clicked.connect(self.show_internal_games)
        ai_layout.addWidget(back_ai)
       
        ai_card = QFrame()
        ai_card.setStyleSheet(f"""
            QFrame {{
                background: rgba(191, 0, 255, 0.1);
                border: 2px solid {CyberColors.NEON_PURPLE}; border-radius: 10px;
            }}
        """)
        ai_card_layout = QVBoxLayout(ai_card)
        ai_card_layout.setContentsMargins(15, 20, 15, 20)
        ai_card_layout.setSpacing(10)
       
        ai_icon = QLabel("🎓")
        ai_icon.setFont(QFont("Segoe UI Emoji", 45))
        ai_icon.setAlignment(Qt.AlignCenter)
        ai_icon.setStyleSheet("background: transparent;")
        ai_card_layout.addWidget(ai_icon)
       
        ai_title = QLabel("AI TRAINER")
        ai_title.setFont(QFont("Consolas", 16, QFont.Bold))
        ai_title.setAlignment(Qt.AlignCenter)
        ai_title.setStyleSheet(f"color: {CyberColors.NEON_PURPLE}; background: transparent;")
        ai_card_layout.addWidget(ai_title)
       
        ai_line = QFrame()
        ai_line.setFixedHeight(2)
        ai_line.setStyleSheet(f"background: {CyberColors.NEON_PURPLE};")
        ai_card_layout.addWidget(ai_line)
       
        ai_sub = QLabel("Learn gestures interactively!\nGame pauses to teach you.")
        ai_sub.setFont(QFont("Consolas", 9))
        ai_sub.setAlignment(Qt.AlignCenter)
        ai_sub.setWordWrap(True)
        ai_sub.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
        ai_card_layout.addWidget(ai_sub)
       
        ai_layout.addWidget(ai_card)
       
        self.start_ai_trainer_btn = QPushButton("▶  START TRAINING")
        self.start_ai_trainer_btn.setFixedHeight(50)
        self.start_ai_trainer_btn.setCursor(Qt.PointingHandCursor)
        self.start_ai_trainer_btn.setFont(QFont("Consolas", 12, QFont.Bold))
        self.start_ai_trainer_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(191, 0, 255, 0.25); color: {CyberColors.NEON_PURPLE};
                border: 3px solid {CyberColors.NEON_PURPLE}; border-radius: 8px;
            }}
            QPushButton:hover {{ background: rgba(191, 0, 255, 0.5); color: white; }}
        """)
        self.start_ai_trainer_btn.clicked.connect(lambda: self.launch_mini_game("ai_trainer"))
        ai_layout.addWidget(self.start_ai_trainer_btn)
        ai_layout.addStretch()
        content_layout.addWidget(self.ai_trainer_details_frame)
       
        # CYBER RUNNER DETAILS FRAME
        self.cyber_runner_details_frame = QFrame()
        self.cyber_runner_details_frame.setVisible(False)
        self.cyber_runner_details_frame.setStyleSheet("background: transparent;")
        runner_layout = QVBoxLayout(self.cyber_runner_details_frame)
        runner_layout.setContentsMargins(0, 0, 0, 0)
        runner_layout.setSpacing(12)
       
        back_runner = QPushButton("◀ BACK")
        back_runner.setFixedHeight(28)
        back_runner.setCursor(Qt.PointingHandCursor)
        back_runner.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {CyberColors.CYAN_PRIMARY};
                border: 1px solid {CyberColors.CYAN_DARK}; border-radius: 4px;
                font-family: Consolas; font-size: 9pt;
            }}
            QPushButton:hover {{ background: rgba(0,200,255,0.2); }}
        """)
        back_runner.clicked.connect(self.show_internal_games)
        runner_layout.addWidget(back_runner)
       
        runner_card = QFrame()
        runner_card.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 255, 136, 0.1);
                border: 2px solid {CyberColors.NEON_GREEN}; border-radius: 10px;
            }}
        """)
        runner_card_layout = QVBoxLayout(runner_card)
        runner_card_layout.setContentsMargins(15, 20, 15, 20)
        runner_card_layout.setSpacing(10)
       
        runner_icon = QLabel("🏃")
        runner_icon.setFont(QFont("Segoe UI Emoji", 45))
        runner_icon.setAlignment(Qt.AlignCenter)
        runner_icon.setStyleSheet("background: transparent;")
        runner_card_layout.addWidget(runner_icon)
       
        runner_title = QLabel("CYBER RUNNER")
        runner_title.setFont(QFont("Consolas", 16, QFont.Bold))
        runner_title.setAlignment(Qt.AlignCenter)
        runner_title.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        runner_card_layout.addWidget(runner_title)
       
        runner_line = QFrame()
        runner_line.setFixedHeight(2)
        runner_line.setStyleSheet(f"background: {CyberColors.NEON_GREEN};")
        runner_card_layout.addWidget(runner_line)
       
        runner_sub = QLabel("Endless runner game!\nDodge obstacles with gestures.")
        runner_sub.setFont(QFont("Consolas", 9))
        runner_sub.setAlignment(Qt.AlignCenter)
        runner_sub.setWordWrap(True)
        runner_sub.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
        runner_card_layout.addWidget(runner_sub)
       
        runner_layout.addWidget(runner_card)
       
        self.start_runner_btn = QPushButton("▶  START GAME")
        self.start_runner_btn.setFixedHeight(50)
        self.start_runner_btn.setCursor(Qt.PointingHandCursor)
        self.start_runner_btn.setFont(QFont("Consolas", 12, QFont.Bold))
        self.start_runner_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 255, 136, 0.25); color: {CyberColors.NEON_GREEN};
                border: 3px solid {CyberColors.NEON_GREEN}; border-radius: 8px;
            }}
            QPushButton:hover {{ background: rgba(0, 255, 136, 0.5); color: white; }}
        """)
        self.start_runner_btn.clicked.connect(lambda: self.launch_mini_game("runner"))
        runner_layout.addWidget(self.start_runner_btn)
        runner_layout.addStretch()
        content_layout.addWidget(self.cyber_runner_details_frame)
       
        # EXTERNAL MODE FRAME
        self.external_frame = QFrame()
        self.external_frame.setVisible(False)
        self.external_frame.setStyleSheet("background: transparent;")
        self.external_frame.setMaximumWidth(260)
        ext_layout = QVBoxLayout(self.external_frame)
        ext_layout.setContentsMargins(0, 0, 0, 0)
        ext_layout.setSpacing(10)
        ext_layout.setAlignment(Qt.AlignTop)
       
        back_ext = QPushButton("◀ BACK TO MODES")
        back_ext.setFixedHeight(30)
        back_ext.setCursor(Qt.PointingHandCursor)
        back_ext.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {CyberColors.CYAN_PRIMARY};
                border: 1px solid {CyberColors.CYAN_DARK}; border-radius: 6px;
                font-family: Consolas; font-size: 9pt; font-weight: bold;
            }}
            QPushButton:hover {{ background: rgba(0,200,255,0.2); }}
        """)
        back_ext.clicked.connect(self.show_mode_selection)
        ext_layout.addWidget(back_ext)
       
        ext_card = QFrame()
        ext_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 165, 0, 0.15), stop:1 rgba(255, 100, 0, 0.05));
                border: 2px solid {CyberColors.ORANGE}; border-radius: 10px;
            }}
        """)
        ext_card_layout = QVBoxLayout(ext_card)
        ext_card_layout.setContentsMargins(12, 15, 12, 15)
        ext_card_layout.setSpacing(8)
       
        ext_icon = QLabel("🎮")
        ext_icon.setFont(QFont("Segoe UI Emoji", 35))
        ext_icon.setAlignment(Qt.AlignCenter)
        ext_icon.setStyleSheet("background: transparent;")
        ext_card_layout.addWidget(ext_icon)
       
        ext_title = QLabel("EXTERNAL MODE")
        ext_title.setFont(QFont("Consolas", 13, QFont.Bold))
        ext_title.setAlignment(Qt.AlignCenter)
        ext_title.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent;")
        ext_card_layout.addWidget(ext_title)
       
        ext_line = QFrame()
        ext_line.setFixedHeight(2)
        ext_line.setStyleSheet(f"background: {CyberColors.ORANGE};")
        ext_card_layout.addWidget(ext_line)
       
        ext_desc = QLabel("Control external games\nwith hand gestures")
        ext_desc.setFont(QFont("Consolas", 9))
        ext_desc.setAlignment(Qt.AlignCenter)
        ext_desc.setWordWrap(True)
        ext_desc.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
        ext_card_layout.addWidget(ext_desc)
       
        ext_layout.addWidget(ext_card)
       
        preset_label = QLabel("◢ GAME PRESET ◣")
        preset_label.setFont(QFont("Consolas", 9, QFont.Bold))
        preset_label.setAlignment(Qt.AlignCenter)
        preset_label.setFixedHeight(22)
        preset_label.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        ext_layout.addWidget(preset_label)
       
        self.preset_combo = QComboBox()
        self.preset_combo.setFixedHeight(34)
        self.preset_combo.setMaximumWidth(240)
        self.preset_combo.setFont(QFont("Consolas", 9))
        self.preset_combo.setStyleSheet(f"""
            QComboBox {{
                background: {CyberColors.NAVY_DARKEST}; color: {CyberColors.CYAN_PRIMARY};
                border: 2px solid {CyberColors.CYAN_DARK}; padding: 5px 10px; border-radius: 6px;
            }}
            QComboBox:hover {{ border-color: {CyberColors.CYAN_PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: 25px; }}
            QComboBox::down-arrow {{
                image: none; border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {CyberColors.CYAN_PRIMARY}; margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {CyberColors.NAVY_DARKER}; color: {CyberColors.TEXT_WHITE};
                selection-background-color: {CyberColors.CYAN_DARK};
                border: 1px solid {CyberColors.CYAN_DARK}; border-radius: 4px; padding: 4px;
            }}
        """)
        self.preset_combo.addItems([
            "🎯 Default", "🔫 FPS Games", "🎯 Valorant",
            "🏎️ Racing", "⛏️ Minecraft", "🕹️ Platformer"
        ])
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        ext_layout.addWidget(self.preset_combo)
       
        ext_info = QFrame()
        ext_info.setMaximumWidth(240)
        ext_info.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 255, 136, 0.08);
                border: 1px solid {CyberColors.NEON_GREEN}; border-radius: 8px;
            }}
        """)
        ext_info_layout = QVBoxLayout(ext_info)
        ext_info_layout.setContentsMargins(10, 10, 10, 10)
        ext_info_layout.setSpacing(4)
       
        info_icon = QLabel("📌")
        info_icon.setFont(QFont("Segoe UI Emoji", 16))
        info_icon.setAlignment(Qt.AlignCenter)
        info_icon.setStyleSheet("background: transparent;")
        ext_info_layout.addWidget(info_icon)
       
        info_text = QLabel("Camera stays visible\nwhile playing games!")
        info_text.setFont(QFont("Consolas", 8))
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        ext_info_layout.addWidget(info_text)
       
        ext_layout.addWidget(ext_info)
       
        mapping_label = QLabel("◢ GESTURE MAP ◣")
        mapping_label.setFont(QFont("Consolas", 9, QFont.Bold))
        mapping_label.setAlignment(Qt.AlignCenter)
        mapping_label.setFixedHeight(22)
        mapping_label.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        ext_layout.addWidget(mapping_label)
       
        mapping_frame = QFrame()
        mapping_frame.setMaximumWidth(240)
        mapping_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 80, 120, 0.15);
                border: 1px solid {CyberColors.CYAN_DARK}; border-radius: 8px;
            }}
        """)
        mapping_layout = QVBoxLayout(mapping_frame)
        mapping_layout.setContentsMargins(8, 8, 8, 8)
        mapping_layout.setSpacing(3)
       
        mappings = [
            ("▲ UP", "W / Jump", CyberColors.NEON_GREEN),
            ("▼ DOWN", "S / Duck", CyberColors.ORANGE),
            ("◀ LEFT", "A / Left", CyberColors.CYAN_PRIMARY),
            ("▶ RIGHT", "D / Right", CyberColors.MAGENTA),
        ]
       
        for gesture, action, color in mappings:
            row = QWidget()
            row.setFixedHeight(22)
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(5, 0, 5, 0)
            row_layout.setSpacing(8)
           
            gesture_lbl = QLabel(gesture)
            gesture_lbl.setFont(QFont("Consolas", 9, QFont.Bold))
            gesture_lbl.setStyleSheet(f"color: {color}; background: transparent;")
            gesture_lbl.setFixedWidth(65)
            row_layout.addWidget(gesture_lbl)
           
            arrow_lbl = QLabel("→")
            arrow_lbl.setFont(QFont("Consolas", 9))
            arrow_lbl.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
            arrow_lbl.setFixedWidth(18)
            arrow_lbl.setAlignment(Qt.AlignCenter)
            row_layout.addWidget(arrow_lbl)
           
            action_lbl = QLabel(action)
            action_lbl.setFont(QFont("Consolas", 9))
            action_lbl.setStyleSheet(f"color: {CyberColors.TEXT_LIGHT}; background: transparent;")
            row_layout.addWidget(action_lbl)
            row_layout.addStretch()
           
            mapping_layout.addWidget(row)
       
        ext_layout.addWidget(mapping_frame)
        ext_layout.addStretch()
        content_layout.addWidget(self.external_frame)
       
        self.game_buttons = {
            "runner": self.start_runner_btn,
            "ai_trainer": self.start_ai_trainer_btn
        }
       
        content_layout.addStretch()
       
        sep2 = QFrame()
        sep2.setFixedHeight(2)
        sep2.setStyleSheet(f"background: {CyberColors.CYAN_DARK};")
        content_layout.addWidget(sep2)
       
        self.toggle_btn = CyberButton("◉ ENGAGE SYSTEM", CyberColors.NEON_GREEN)
        self.toggle_btn.setFixedHeight(48)
        self.toggle_btn.clicked.connect(self.toggle_gaming_mode)
        content_layout.addWidget(self.toggle_btn)
       
        scroll.setWidget(scroll_content)
        panel_layout.addWidget(scroll, stretch=1)
       
        return panel_frame

    # ═══════════════════════════════════════════════════════════════════════════
    # ██████████████████████████████████████████████████████████████████████████
    # ██  CHANGE 2 & 3: COMPLETELY REDESIGNED _create_center_panel           ██
    # ██  — Gaming controller HUD header                                     ██
    # ██  — No-game placeholder with controller shape, D-pad, ABXY buttons   ██
    # ██  — Animated scan lines and status indicators                        ██
    # ██████████████████████████████████████████████████████████████████████████
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_center_panel(self):
        # ═══════════════════════════════════════════════════════════════
        # MAIN CONTAINER — HologramCenterPanel with paint overlays
        # ═══════════════════════════════════════════════════════════════
        self.hologram_panel = HologramCenterPanel()
        self.hologram_panel.setObjectName("hologramPanel")
        self.hologram_panel.setStyleSheet(f"""
            #hologramPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
                    stop:0 rgba(2, 6, 18, 0.99),
                    stop:0.2 rgba(4, 12, 30, 0.98),
                    stop:0.4 rgba(6, 18, 42, 0.96),
                    stop:0.6 rgba(8, 22, 48, 0.95),
                    stop:0.8 rgba(5, 14, 35, 0.97),
                    stop:1 rgba(2, 6, 18, 0.99));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 180, 255, 0.3),
                    stop:0.25 rgba(0, 255, 200, 0.7),
                    stop:0.5 rgba(0, 255, 255, 0.9),
                    stop:0.75 rgba(0, 255, 200, 0.7),
                    stop:1 rgba(0, 180, 255, 0.3));
                border-radius: 14px;
            }}
        """)

        panel_glow = QGraphicsDropShadowEffect()
        panel_glow.setBlurRadius(35)
        panel_glow.setColor(QColor(0, 255, 220, 90))
        panel_glow.setOffset(0, 0)
        self.hologram_panel.setGraphicsEffect(panel_glow)

        main_layout = QVBoxLayout(self.hologram_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════════════════════════════════════════════════
        # HEADER — ENHANCED FUTURISTIC (48px)
        # ═══════════════════════════════════════════════════════════════
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 8, 20, 0.98),
                    stop:0.1 rgba(0, 30, 60, 0.85),
                    stop:0.25 rgba(0, 60, 100, 0.6),
                    stop:0.4 rgba(0, 100, 140, 0.4),
                    stop:0.5 rgba(0, 180, 200, 0.25),
                    stop:0.6 rgba(0, 100, 140, 0.4),
                    stop:0.75 rgba(0, 60, 100, 0.6),
                    stop:0.9 rgba(0, 30, 60, 0.85),
                    stop:1 rgba(0, 8, 20, 0.98));
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 255, 200, 0.05),
                    stop:0.2 rgba(0, 255, 200, 0.5),
                    stop:0.4 rgba(0, 255, 255, 0.9),
                    stop:0.5 rgba(0, 255, 255, 1.0),
                    stop:0.6 rgba(0, 255, 255, 0.9),
                    stop:0.8 rgba(0, 255, 200, 0.5),
                    stop:1 rgba(0, 255, 200, 0.05));
            }}
        """)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(18, 0, 18, 0)
        h_layout.setSpacing(8)

        # LED indicator dots
        led_colors = ["#00ff88", "#00e5ff", "#00ffcc"]
        for color in led_colors:
            dot = QFrame()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet(f"""
                background: {color};
                border-radius: 3px;
                border: 1px solid rgba(255,255,255,0.2);
            """)
            dot_glow = QGraphicsDropShadowEffect()
            dot_glow.setBlurRadius(12)
            dot_glow.setColor(QColor(color))
            dot_glow.setOffset(0, 0)
            dot.setGraphicsEffect(dot_glow)
            h_layout.addWidget(dot)

        spacer_w = QWidget()
        spacer_w.setFixedWidth(6)
        spacer_w.setStyleSheet("background: transparent;")
        h_layout.addWidget(spacer_w)

        # Left deco
        h_deco_l = QLabel("◢◤")
        h_deco_l.setFont(QFont("Consolas", 11, QFont.Bold))
        h_deco_l.setStyleSheet(f"color: rgba(0, 255, 220, 0.6); background: transparent;")
        h_layout.addWidget(h_deco_l)

        # Icon
        h_icon = QLabel("🔮")
        h_icon.setFont(QFont("Segoe UI Emoji", 15))
        h_icon.setStyleSheet("background: transparent;")
        h_layout.addWidget(h_icon)

        # Title
        h_title = QLabel("GAMING VIEWPORT")
        h_title.setFont(QFont("Consolas", 14, QFont.Bold))
        h_title.setStyleSheet(f"""
            color: {CyberColors.CYAN_PRIMARY};
            background: transparent;
            letter-spacing: 4px;
        """)
        title_glow = QGraphicsDropShadowEffect()
        title_glow.setBlurRadius(20)
        title_glow.setColor(QColor(0, 255, 255, 100))
        title_glow.setOffset(0, 0)
        h_title.setGraphicsEffect(title_glow)
        h_layout.addWidget(h_title)

        # Right deco
        h_deco_r = QLabel("◢◤")
        h_deco_r.setFont(QFont("Consolas", 11, QFont.Bold))
        h_deco_r.setStyleSheet(f"color: rgba(0, 255, 220, 0.6); background: transparent;")
        h_layout.addWidget(h_deco_r)

        h_layout.addStretch()

        # Status pill
        status_pill = QFrame()
        status_pill.setFixedSize(120, 26)
        status_pill.setStyleSheet(f"""
            QFrame {{
                background: rgba(0, 255, 200, 0.06);
                border: 1px solid rgba(0, 255, 200, 0.25);
                border-radius: 13px;
            }}
        """)
        sp_layout = QHBoxLayout(status_pill)
        sp_layout.setContentsMargins(10, 0, 10, 0)
        sp_layout.setSpacing(5)

        self._status_dot = QFrame()
        self._status_dot.setFixedSize(7, 7)
        self._status_dot.setStyleSheet(f"background: {CyberColors.TEXT_DIM}; border-radius: 3px;")
        sp_layout.addWidget(self._status_dot)

        self.viewport_status = QLabel("STANDBY")
        self.viewport_status.setFont(QFont("Consolas", 9, QFont.Bold))
        self.viewport_status.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        sp_layout.addWidget(self.viewport_status)

        h_layout.addWidget(status_pill)

        # FPS badge
        fps_badge = QFrame()
        fps_badge.setFixedSize(72, 26)
        fps_badge.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 215, 0, 0.06);
                border: 1px solid rgba(255, 215, 0, 0.25);
                border-radius: 13px;
            }}
        """)
        fb_layout = QHBoxLayout(fps_badge)
        fb_layout.setContentsMargins(8, 0, 8, 0)
        fb_layout.setSpacing(4)

        fps_icon = QLabel("⚡")
        fps_icon.setFont(QFont("Segoe UI Emoji", 9))
        fps_icon.setStyleSheet("background: transparent;")
        fb_layout.addWidget(fps_icon)

        self.fps_label = QLabel("0")
        self.fps_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.fps_label.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        fb_layout.addWidget(self.fps_label)

        h_layout.addWidget(fps_badge)

        main_layout.addWidget(header)

        # ═══════════════════════════════════════════════════════════════
        # CANVAS CONTAINER
        # ═══════════════════════════════════════════════════════════════
        self.canvas_container = QFrame()
        self.canvas_container.setStyleSheet("QFrame { background: transparent; }")

        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_layout.setSpacing(0)

        # Game canvases
        self.gaming_canvas = None
        self.ai_trainer_canvas = None

        if GAMING_CANVAS_AVAILABLE:
            try:
                from gaming_canvas import GamingCanvas
                self.gaming_canvas = GamingCanvas()
                self.gaming_canvas.game_over.connect(self._on_game_over)
                self.gaming_canvas.game_started.connect(self._on_game_started)
                self.gaming_canvas.setVisible(False)
                self.canvas_layout.addWidget(self.gaming_canvas)
                print("  ✅ Cyber Runner Canvas Ready")
            except Exception as e:
                print(f"  ⚠️ Cyber Runner Error: {e}")

        try:
            from ai_trainer_game import AITrainerGame
            self.ai_trainer_canvas = AITrainerGame()
            self.ai_trainer_canvas.game_over.connect(self._on_game_over)
            self.ai_trainer_canvas.game_started.connect(self._on_game_started)
            self.ai_trainer_canvas.setVisible(False)
            self.canvas_layout.addWidget(self.ai_trainer_canvas)
            print("  ✅ AI Trainer Canvas Ready")
        except Exception as e:
            print(f"  ⚠️ AI Trainer Error: {e}")

        # ───────────────────────────────────────────────────────────────
        # NO GAME PLACEHOLDER — ENHANCED FUTURISTIC
        # ───────────────────────────────────────────────────────────────
        self.no_game_widget = QWidget()
        self.no_game_widget.setStyleSheet("background: transparent;")

        ng_layout = QVBoxLayout(self.no_game_widget)
        ng_layout.setContentsMargins(30, 20, 30, 20)
        ng_layout.setSpacing(0)

        ng_layout.addStretch(1)

        # ═══════════════════════════════════════════════════════════════
        # TOP — SYSTEM TITLE BAR
        # ═══════════════════════════════════════════════════════════════
        title_frame = QFrame()
        title_frame.setFixedHeight(50)
        title_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 200, 255, 0.0),
                    stop:0.2 rgba(0, 200, 255, 0.08),
                    stop:0.5 rgba(0, 255, 220, 0.12),
                    stop:0.8 rgba(0, 200, 255, 0.08),
                    stop:1 rgba(0, 200, 255, 0.0));
                border: 1px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.3 rgba(0, 255, 255, 0.3),
                    stop:0.5 rgba(0, 255, 255, 0.5),
                    stop:0.7 rgba(0, 255, 255, 0.3),
                    stop:1 transparent);
                border-radius: 8px;
            }}
        """)
        tf_layout = QHBoxLayout(title_frame)
        tf_layout.setContentsMargins(20, 0, 20, 0)
        tf_layout.setSpacing(10)

        sys_dot = QFrame()
        sys_dot.setFixedSize(10, 10)
        sys_dot.setStyleSheet(f"background: {CyberColors.CYAN_PRIMARY}; border-radius: 5px;")
        sys_glow = QGraphicsDropShadowEffect()
        sys_glow.setBlurRadius(15)
        sys_glow.setColor(QColor(0, 255, 255, 180))
        sys_glow.setOffset(0, 0)
        sys_dot.setGraphicsEffect(sys_glow)
        tf_layout.addWidget(sys_dot)

        sys_title = QLabel("GESTURE CONTROL SYSTEM")
        sys_title.setFont(QFont("Consolas", 16, QFont.Bold))
        sys_title.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent; letter-spacing: 3px;")
        sys_title_glow = QGraphicsDropShadowEffect()
        sys_title_glow.setBlurRadius(18)
        sys_title_glow.setColor(QColor(0, 255, 255, 80))
        sys_title_glow.setOffset(0, 0)
        sys_title.setGraphicsEffect(sys_title_glow)
        tf_layout.addWidget(sys_title)

        tf_layout.addStretch()

        sys_badge = QLabel("◈ AWAITING GAME ◈")
        sys_badge.setFont(QFont("Consolas", 9))
        sys_badge.setStyleSheet(f"color: rgba(0, 255, 200, 0.4); background: transparent;")
        tf_layout.addWidget(sys_badge)

        ng_layout.addWidget(title_frame)
        ng_layout.addSpacing(20)

        # ═══════════════════════════════════════════════════════════════
        # MIDDLE — DIRECTION + MODE PANELS
        # ═══════════════════════════════════════════════════════════════
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(20)

        # ╔═══════════════════════════════════════════════╗
        # ║  LEFT — 4 DIRECTION CONTROL                  ║
        # ╚═══════════════════════════════════════════════╝
        dir_frame = QFrame()
        dir_frame.setFixedSize(220, 270)
        dir_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 200, 255, 0.06),
                    stop:0.5 rgba(0, 180, 220, 0.03),
                    stop:1 rgba(0, 200, 255, 0.06));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 255, 255, 0.3),
                    stop:0.5 rgba(0, 200, 255, 0.15),
                    stop:1 rgba(0, 255, 255, 0.3));
                border-radius: 14px;
            }}
        """)
        dir_glow = QGraphicsDropShadowEffect()
        dir_glow.setBlurRadius(20)
        dir_glow.setColor(QColor(0, 200, 255, 40))
        dir_glow.setOffset(0, 0)
        dir_frame.setGraphicsEffect(dir_glow)

        dir_layout = QVBoxLayout(dir_frame)
        dir_layout.setContentsMargins(15, 12, 15, 12)
        dir_layout.setSpacing(6)

        dir_title = QLabel("✋ HAND DIRECTIONS")
        dir_title.setFont(QFont("Consolas", 10, QFont.Bold))
        dir_title.setAlignment(Qt.AlignCenter)
        dir_title.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
        dir_layout.addWidget(dir_title)

        dir_sep = QFrame()
        dir_sep.setFixedHeight(2)
        dir_sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.2 rgba(0, 255, 255, 0.6),
                stop:0.5 rgba(0, 255, 200, 0.9),
                stop:0.8 rgba(0, 255, 255, 0.6),
                stop:1 transparent);
        """)
        dir_layout.addWidget(dir_sep)
        dir_layout.addSpacing(6)

        # Direction box helper
        def make_dir_box(arrow, label, color_hex):
            box = QFrame()
            box.setFixedSize(65, 48)
            c = QColor(color_hex)
            r, g, b = c.red(), c.green(), c.blue()
            box.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({r},{g},{b}, 0.15),
                        stop:1 rgba({r},{g},{b}, 0.05));
                    border: 2px solid rgba({r},{g},{b}, 0.5);
                    border-radius: 10px;
                }}
            """)
            box_glow = QGraphicsDropShadowEffect()
            box_glow.setBlurRadius(12)
            box_glow.setColor(QColor(r, g, b, 60))
            box_glow.setOffset(0, 0)
            box.setGraphicsEffect(box_glow)

            inner = QVBoxLayout(box)
            inner.setContentsMargins(0, 3, 0, 3)
            inner.setSpacing(0)
            arr_lbl = QLabel(arrow)
            arr_lbl.setFont(QFont("Consolas", 17, QFont.Bold))
            arr_lbl.setAlignment(Qt.AlignCenter)
            arr_lbl.setStyleSheet(f"color: {color_hex}; background: transparent;")
            inner.addWidget(arr_lbl)
            txt_lbl = QLabel(label)
            txt_lbl.setFont(QFont("Consolas", 7, QFont.Bold))
            txt_lbl.setAlignment(Qt.AlignCenter)
            txt_lbl.setStyleSheet(f"color: rgba({r},{g},{b}, 0.7); background: transparent;")
            inner.addWidget(txt_lbl)
            return box

        # UP
        up_row = QHBoxLayout()
        up_row.setAlignment(Qt.AlignCenter)
        up_row.addWidget(make_dir_box("▲", "UP", CyberColors.NEON_GREEN))
        dir_layout.addLayout(up_row)

        # LEFT — HAND — RIGHT
        lcr_row = QHBoxLayout()
        lcr_row.setSpacing(12)
        lcr_row.setAlignment(Qt.AlignCenter)

        lcr_row.addWidget(make_dir_box("◄", "LEFT", CyberColors.CYAN_PRIMARY))

        # Center hand
        hand_frame = QFrame()
        hand_frame.setFixedSize(60, 60)
        hand_frame.setStyleSheet(f"""
            QFrame {{
                background: qradial-gradient(ellipse at center,
                    rgba(0, 255, 220, 0.1) 0%,
                    rgba(0, 200, 255, 0.05) 50%,
                    transparent 70%);
                border: 2px solid rgba(0, 255, 255, 0.2);
                border-radius: 30px;
            }}
        """)
        hand_inner = QVBoxLayout(hand_frame)
        hand_inner.setContentsMargins(0, 0, 0, 0)
        hand_icon = QLabel("🖐️")
        hand_icon.setFont(QFont("Segoe UI Emoji", 26))
        hand_icon.setAlignment(Qt.AlignCenter)
        hand_icon.setStyleSheet("background: transparent;")
        hand_inner.addWidget(hand_icon)
        lcr_row.addWidget(hand_frame)

        lcr_row.addWidget(make_dir_box("►", "RIGHT", CyberColors.MAGENTA))

        dir_layout.addLayout(lcr_row)

        # DOWN
        down_row = QHBoxLayout()
        down_row.setAlignment(Qt.AlignCenter)
        down_row.addWidget(make_dir_box("▼", "DOWN", CyberColors.ORANGE))
        dir_layout.addLayout(down_row)

        dir_layout.addSpacing(6)

        dir_hint = QLabel("Move hand to control direction")
        dir_hint.setFont(QFont("Consolas", 8))
        dir_hint.setAlignment(Qt.AlignCenter)
        dir_hint.setStyleSheet(f"color: rgba(0, 255, 220, 0.35); background: transparent;")
        dir_layout.addWidget(dir_hint)

        mid_layout.addWidget(dir_frame)

        # ╔═══════════════════════════════════════════════╗
        # ║  RIGHT — INTERNAL + EXTERNAL MODE PANELS     ║
        # ╚═══════════════════════════════════════════════╝
        modes_frame = QFrame()
        modes_frame.setStyleSheet("background: transparent;")
        modes_layout = QVBoxLayout(modes_frame)
        modes_layout.setContentsMargins(0, 0, 0, 0)
        modes_layout.setSpacing(12)

        # ── INTERNAL MODE CARD ──
        int_card = QFrame()
        int_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 255, 136, 0.08),
                    stop:0.5 rgba(0, 255, 136, 0.03),
                    stop:1 rgba(0, 255, 136, 0.08));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 255, 136, 0.4),
                    stop:0.5 rgba(0, 255, 136, 0.15),
                    stop:1 rgba(0, 255, 136, 0.4));
                border-radius: 12px;
            }}
        """)
        int_card_glow = QGraphicsDropShadowEffect()
        int_card_glow.setBlurRadius(18)
        int_card_glow.setColor(QColor(0, 255, 136, 35))
        int_card_glow.setOffset(0, 0)
        int_card.setGraphicsEffect(int_card_glow)

        int_layout = QVBoxLayout(int_card)
        int_layout.setContentsMargins(15, 12, 15, 12)
        int_layout.setSpacing(8)

        int_header = QHBoxLayout()
        int_header.setSpacing(8)
        int_icon_lbl = QLabel("▶")
        int_icon_lbl.setFont(QFont("Consolas", 14, QFont.Bold))
        int_icon_lbl.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        int_header.addWidget(int_icon_lbl)
        int_title_lbl = QLabel("INTERNAL MODE")
        int_title_lbl.setFont(QFont("Consolas", 12, QFont.Bold))
        int_title_lbl.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent; letter-spacing: 2px;")
        int_header.addWidget(int_title_lbl)
        int_header.addStretch()
        int_layout.addLayout(int_header)

        int_sep = QFrame()
        int_sep.setFixedHeight(2)
        int_sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.3 rgba(0, 255, 136, 0.6),
                stop:0.7 rgba(0, 255, 136, 0.6),
                stop:1 transparent);
        """)
        int_layout.addWidget(int_sep)

        games_data = [
            ("🎓", "AI TRAINER", "Learn gestures interactively", CyberColors.NEON_PURPLE),
            ("🏃", "CYBER RUNNER", "Dodge obstacles with directions", CyberColors.NEON_GREEN),
        ]

        for emoji, name, desc, color in games_data:
            game_row = QHBoxLayout()
            game_row.setSpacing(10)

            g_icon_frame = QFrame()
            g_icon_frame.setFixedSize(38, 38)
            c = QColor(color)
            g_icon_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba({c.red()},{c.green()},{c.blue()}, 0.1);
                    border: 1px solid rgba({c.red()},{c.green()},{c.blue()}, 0.3);
                    border-radius: 8px;
                }}
            """)
            gif_layout = QVBoxLayout(g_icon_frame)
            gif_layout.setContentsMargins(0, 0, 0, 0)
            g_emoji = QLabel(emoji)
            g_emoji.setFont(QFont("Segoe UI Emoji", 18))
            g_emoji.setAlignment(Qt.AlignCenter)
            g_emoji.setStyleSheet("background: transparent;")
            gif_layout.addWidget(g_emoji)
            game_row.addWidget(g_icon_frame)

            g_info = QVBoxLayout()
            g_info.setSpacing(1)
            g_name = QLabel(name)
            g_name.setFont(QFont("Consolas", 10, QFont.Bold))
            g_name.setStyleSheet(f"color: {color}; background: transparent; letter-spacing: 1px;")
            g_info.addWidget(g_name)
            g_desc = QLabel(desc)
            g_desc.setFont(QFont("Consolas", 8))
            g_desc.setStyleSheet(f"color: rgba(180, 200, 220, 0.5); background: transparent;")
            g_info.addWidget(g_desc)
            game_row.addLayout(g_info)
            game_row.addStretch()
            int_layout.addLayout(game_row)

        modes_layout.addWidget(int_card)

        # ── EXTERNAL MODE CARD ──
        ext_card = QFrame()
        ext_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 165, 0, 0.08),
                    stop:0.5 rgba(255, 165, 0, 0.03),
                    stop:1 rgba(255, 165, 0, 0.08));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 165, 0, 0.4),
                    stop:0.5 rgba(255, 165, 0, 0.15),
                    stop:1 rgba(255, 165, 0, 0.4));
                border-radius: 12px;
            }}
        """)
        ext_card_glow = QGraphicsDropShadowEffect()
        ext_card_glow.setBlurRadius(18)
        ext_card_glow.setColor(QColor(255, 165, 0, 35))
        ext_card_glow.setOffset(0, 0)
        ext_card.setGraphicsEffect(ext_card_glow)

        ext_layout_card = QVBoxLayout(ext_card)
        ext_layout_card.setContentsMargins(15, 12, 15, 12)
        ext_layout_card.setSpacing(8)

        ext_header = QHBoxLayout()
        ext_header.setSpacing(8)
        ext_icon_lbl = QLabel("◆")
        ext_icon_lbl.setFont(QFont("Consolas", 14, QFont.Bold))
        ext_icon_lbl.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent;")
        ext_header.addWidget(ext_icon_lbl)
        ext_title_lbl = QLabel("EXTERNAL MODE")
        ext_title_lbl.setFont(QFont("Consolas", 12, QFont.Bold))
        ext_title_lbl.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent; letter-spacing: 2px;")
        ext_header.addWidget(ext_title_lbl)
        ext_header.addStretch()
        ext_layout_card.addLayout(ext_header)

        ext_sep = QFrame()
        ext_sep.setFixedHeight(2)
        ext_sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.3 rgba(255, 165, 0, 0.6),
                stop:0.7 rgba(255, 165, 0, 0.6),
                stop:1 transparent);
        """)
        ext_layout_card.addWidget(ext_sep)

        ext_mappings = [
            ("▲ UP", "→", "W / Jump", CyberColors.NEON_GREEN),
            ("▼ DOWN", "→", "S / Duck", CyberColors.ORANGE),
            ("◄ LEFT", "→", "A / Left", CyberColors.CYAN_PRIMARY),
            ("► RIGHT", "→", "D / Right", CyberColors.MAGENTA),
        ]

        for direction, arrow, key, color in ext_mappings:
            map_row = QHBoxLayout()
            map_row.setSpacing(8)

            m_dir = QLabel(direction)
            m_dir.setFont(QFont("Consolas", 9, QFont.Bold))
            m_dir.setFixedWidth(75)
            m_dir.setStyleSheet(f"color: {color}; background: transparent;")
            map_row.addWidget(m_dir)

            m_arrow = QLabel(arrow)
            m_arrow.setFont(QFont("Consolas", 10))
            m_arrow.setFixedWidth(18)
            m_arrow.setAlignment(Qt.AlignCenter)
            m_arrow.setStyleSheet(f"color: rgba(0, 255, 220, 0.3); background: transparent;")
            map_row.addWidget(m_arrow)

            m_key = QFrame()
            m_key.setFixedHeight(26)
            c = QColor(color)
            m_key.setStyleSheet(f"""
                QFrame {{
                    background: rgba({c.red()},{c.green()},{c.blue()}, 0.06);
                    border: 1px solid rgba({c.red()},{c.green()},{c.blue()}, 0.2);
                    border-radius: 5px;
                }}
            """)
            mk_layout = QHBoxLayout(m_key)
            mk_layout.setContentsMargins(10, 0, 10, 0)
            mk_label = QLabel(key)
            mk_label.setFont(QFont("Consolas", 9))
            mk_label.setStyleSheet(f"color: rgba(200, 220, 240, 0.7); background: transparent;")
            mk_layout.addWidget(mk_label)
            map_row.addWidget(m_key)
            map_row.addStretch()

            ext_layout_card.addLayout(map_row)

        modes_layout.addWidget(ext_card)
        modes_layout.addStretch()

        mid_layout.addWidget(modes_frame, stretch=1)

        ng_layout.addLayout(mid_layout)
        ng_layout.addSpacing(15)

        # ═══════════════════════════════════════════════════════════════
        # BOTTOM — ACTION HINT
        # ═══════════════════════════════════════════════════════════════
        bottom_hint = QFrame()
        bottom_hint.setFixedHeight(38)
        bottom_hint.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 200, 255, 0.0),
                    stop:0.3 rgba(0, 200, 255, 0.06),
                    stop:0.5 rgba(0, 255, 220, 0.08),
                    stop:0.7 rgba(0, 200, 255, 0.06),
                    stop:1 rgba(0, 200, 255, 0.0));
                border: 1px solid rgba(0, 255, 220, 0.12);
                border-radius: 8px;
            }}
        """)
        bh_layout = QHBoxLayout(bottom_hint)
        bh_layout.setContentsMargins(20, 0, 20, 0)
        bh_layout.setSpacing(12)

        bh_icon = QLabel("💡")
        bh_icon.setFont(QFont("Segoe UI Emoji", 12))
        bh_icon.setStyleSheet("background: transparent;")
        bh_layout.addWidget(bh_icon)

        bh_text = QLabel("Select a mode from Control Panel  →  Choose a game  →  Press ENGAGE")
        bh_text.setFont(QFont("Consolas", 9))
        bh_text.setStyleSheet(f"color: rgba(0, 255, 220, 0.35); background: transparent;")
        bh_layout.addWidget(bh_text)
        bh_layout.addStretch()

        ng_layout.addWidget(bottom_hint)
        ng_layout.addStretch(1)

        self.canvas_layout.addWidget(self.no_game_widget)
        main_layout.addWidget(self.canvas_container, 1)

        # ═══════════════════════════════════════════════════════════════
        # FOOTER — ENHANCED (Hidden until game loads) — 50px
        # ═══════════════════════════════════════════════════════════════
        self.footer = QFrame()
        self.footer.setFixedHeight(50)
        self.footer.setVisible(False)
        self.footer.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 8, 20, 0.95),
                    stop:0.15 rgba(0, 40, 70, 0.7),
                    stop:0.3 rgba(0, 60, 100, 0.5),
                    stop:0.5 rgba(0, 100, 140, 0.35),
                    stop:0.7 rgba(0, 60, 100, 0.5),
                    stop:0.85 rgba(0, 40, 70, 0.7),
                    stop:1 rgba(0, 8, 20, 0.95));
                border-top: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 255, 255, 0.05),
                    stop:0.3 rgba(0, 255, 200, 0.6),
                    stop:0.5 rgba(0, 255, 255, 1.0),
                    stop:0.7 rgba(0, 255, 200, 0.6),
                    stop:1 rgba(0, 255, 255, 0.05));
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)

        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(18, 0, 18, 0)
        f_layout.setSpacing(12)

        f_icon = QLabel("🎮")
        f_icon.setFont(QFont("Segoe UI Emoji", 17))
        f_icon.setStyleSheet("background: transparent;")
        f_layout.addWidget(f_icon)

        self.game_label = QLabel("NO GAME LOADED")
        self.game_label.setFont(QFont("Consolas", 13, QFont.Bold))
        self.game_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent; letter-spacing: 2px;")
        f_layout.addWidget(self.game_label)

        f_layout.addStretch()

        score_container = QFrame()
        score_container.setFixedSize(140, 38)
        score_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 215, 0, 0.03),
                    stop:0.5 rgba(255, 215, 0, 0.12),
                    stop:1 rgba(255, 215, 0, 0.03));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 215, 0, 0.3),
                    stop:0.5 rgba(255, 215, 0, 0.8),
                    stop:1 rgba(255, 215, 0, 0.3));
                border-radius: 10px;
            }}
        """)
        score_glow = QGraphicsDropShadowEffect()
        score_glow.setBlurRadius(15)
        score_glow.setColor(QColor(255, 215, 0, 50))
        score_glow.setOffset(0, 0)
        score_container.setGraphicsEffect(score_glow)

        sc_layout = QHBoxLayout(score_container)
        sc_layout.setContentsMargins(12, 0, 12, 0)
        sc_layout.setSpacing(8)

        star_icon = QLabel("⭐")
        star_icon.setFont(QFont("Segoe UI Emoji", 14))
        star_icon.setStyleSheet("background: transparent;")
        sc_layout.addWidget(star_icon)

        self.score_label = QLabel("0000")
        self.score_label.setFont(QFont("Consolas", 15, QFont.Bold))
        self.score_label.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
        sc_layout.addWidget(self.score_label)

        f_layout.addWidget(score_container)

        main_layout.addWidget(self.footer)

        return self.hologram_panel

    # ═══════════════════════════════════════════════════════════════════════════
    # ALL METHODS BELOW ARE UNCHANGED FROM ORIGINAL
    # ═══════════════════════════════════════════════════════════════════════════

    def set_control_mode(self, mode):
        """self.current_mode = mode
        try:
            self.gesture_hud.set_mode(mode)
        except Exception:
            pass"""
        if GAME_CONTROLLER_AVAILABLE and game_controller:
            try:
                game_controller.set_control_mode(mode)
            except Exception:
                pass
        self.gesture_status.setText(f"◈ {mode} ◈")

    def _on_preset_changed(self, preset_text):
        preset_map = {
            "🎯 Default": "default", "🔫 FPS Games": "fps",
            "🎯 Valorant": "valorant", "🏎️ Racing": "racing",
            "⛏️ Minecraft": "minecraft", "🕹️ Platformer": "platformer"
        }
        preset = preset_map.get(preset_text, "default")
        if GAME_CONTROLLER_AVAILABLE and game_controller:
            try:
                game_controller.set_preset(preset)
            except Exception:
                pass

    def toggle_floating_camera(self):
        try:
            if self.floating_camera is None:
                self.floating_camera = FloatingCameraWindow()
            if self.floating_camera.isVisible():
                self.floating_camera.hide()
                self.camera_btn.setText("◎ CAMERA FEED 📌")
                self.camera_btn.setChecked(False)
            else:
                self.floating_camera.show()
                self.camera_btn.setText("✨ FEED ACTIVE 📌")
                self.camera_btn.setChecked(True)
                if self.is_gaming_active:
                    self.floating_camera.start_preview()
        except Exception as e:
            print(f"⚠️ Camera toggle error: {e}")

    def toggle_gaming_mode(self):
        if self.is_gaming_active:
            self.stop_gaming_mode()
        else:
            self.start_gaming_mode()

    def start_gaming_mode(self):
        if self.is_gaming_active or self.is_closing:
            return
       
        self.is_gaming_active = True
        self.last_frame_time = time.time()
        self.frame_count = 0
        self._last_gesture_time = 0
        self._last_direction_time = 0
        self.last_processed_frame_id = None
        self.last_gesture = None

         # ═══════════════════════════════════════════════════════════════
    # ✅ ADD THIS: Set mode to GAMING (disables cursor control)
    # ═══════════════════════════════════════════════════════════════
        mode_manager.set_mode("GAMING")
        print("🎮 Mode set to GAMING - Cursor control DISABLED")



        # ═══════════════════════════════════════════════════════════════
    # ✅ ADD THIS: Show notification
    # ═══════════════════════════════════════════════════════════════
        try:
            from notification_popup import get_toast_manager
            toast = get_toast_manager()
            toast.show_toast(
                "🎮 Gaming Mode Engaged",
                "Cursor control DISABLED - Use gestures for game!",
                duration=3000
            )
        except Exception as e:
            print(f"Toast error: {e}")
       
        self.toggle_btn.setText("◼ DISENGAGE")
        self.toggle_btn.base_color = CyberColors.ORANGE
        self.toggle_btn._apply_style()
        self.toggle_btn.add_glow(20, 120)
       
        self.gesture_status.setText("◉ ACTIVE ◉")
        self.gesture_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN};")
       
        self.top_status.setText("◉ TRACKING ACTIVE ◉")
        self.top_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
       
        self.viewport_status.setText("ACTIVE")
        self.viewport_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        self._status_dot.setStyleSheet(f"background: {CyberColors.NEON_GREEN}; border-radius: 4px;")
       
        """try:
            self.gesture_hud.set_active(True)
        except Exception:
            pass"""
       
        # Start hologram animations
        self.hologram_panel.start_animations()
       
        try:
            camera_is_active = hand_tracker.get_camera_state() if hasattr(hand_tracker, 'get_camera_state') else False
            if not camera_is_active:
                self.camera_started_by_gaming = True
                if hasattr(hand_tracker, 'set_camera_state'):
                    hand_tracker.set_camera_state(True)
                if hasattr(hand_tracker, 'set_gesture_state'):
                    hand_tracker.set_gesture_state(True)
            else:
                self.camera_started_by_gaming = False
        except Exception as e:
            print(f"  ⚠️ Camera Error: {e}")
       
        try:
            mode_manager.set_mode("GAMING")
            if hasattr(mode_manager, 'set_gaming_page'):
                mode_manager.set_gaming_page(self)
        except Exception:
            pass
       
        if GAME_CONTROLLER_AVAILABLE and game_controller:
            try:
                game_controller.start()
                if self.gaming_canvas:
                    game_controller.set_game_callback(self.gaming_canvas.handle_gesture)
            except Exception:
                pass
       
        self.camera_timer.start(CAMERA_TIMER_INTERVAL)
        self.anim_timer.start(ANIMATION_TIMER_INTERVAL)
        self.health_timer.start(HEALTH_CHECK_INTERVAL)
       
        try:
            if self.floating_camera is None:
                self.floating_camera = FloatingCameraWindow()
            self.floating_camera.start_preview()
            self.floating_camera.show()
            self.camera_btn.setText("✨ FEED ACTIVE 📌")
            self.camera_btn.setChecked(True)
        except Exception:
            pass

    def stop_gaming_mode(self):
        if not self.is_gaming_active or self.is_closing:
            return
       
        self.is_gaming_active = False
       
        try:
            self.health_timer.stop()
        except Exception:
            pass
        try:
            self.camera_timer.stop()
        except Exception:
            pass
        try:
            self.anim_timer.stop()
        except Exception:
            pass
       
        self.hologram_panel.stop_animations()

         # ═══════════════════════════════════════════════════════════════
    # ✅ ADD THIS: Switch back to DESKTOP mode (enables cursor control)
    # ═══════════════════════════════════════════════════════════════
        mode_manager.set_mode("DESKTOP")
        print("🖱️ Mode set to DESKTOP - Cursor control ENABLED")

        # ═══════════════════════════════════════════════════════════════
    # ✅ ADD THIS: Show notification
    # ═══════════════════════════════════════════════════════════════
        try:
            from notification_popup import get_toast_manager
            toast = get_toast_manager()
            toast.show_toast(
                "🖱️ Gaming Mode Disengaged",
                "Cursor control ENABLED - Hand gestures control cursor!",
                duration=3000
            )
        except Exception as e:
            print(f"Toast error: {e}")
   
        # ═══════════════════════════════════════════════════════════════
        # ✅ ADD THIS: Unregister gaming page from mode_manager
        # ═══════════════════════════════════════════════════════════════
        try:
            if hasattr(mode_manager, 'set_gaming_page'):
                mode_manager.set_gaming_page(None)
        except Exception:
            pass
       
        try:
            QApplication.processEvents()
            time.sleep(0.05)
        except Exception:
            pass
       
        try:
            if hasattr(mode_manager, 'set_gaming_page'):
                mode_manager.set_gaming_page(None)
        except Exception:
            pass
       
        self.toggle_btn.setText("◉ ENGAGE SYSTEM")
        self.toggle_btn.base_color = CyberColors.NEON_GREEN
        self.toggle_btn._apply_style()
        self.toggle_btn.add_glow(20, 120)
       
        self.gesture_status.setText("◈ READY ◈")
        self.gesture_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY};")
       
        self.top_status.setText("◈ SYSTEM READY ◈")
        self.top_status.setStyleSheet(f"color: {CyberColors.CYAN_PRIMARY}; background: transparent;")
       
        self.viewport_status.setText("STANDBY")
        self.viewport_status.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        self._status_dot.setStyleSheet(f"background: {CyberColors.TEXT_DIM}; border-radius: 4px;")
       
        """try:
            self.gesture_hud.set_active(False)
            self.gesture_hud.set_gesture(None)
        except Exception:
            pass"""
       
        if GAME_CONTROLLER_AVAILABLE and game_controller:
            try:
                game_controller.set_game_callback(None)
                game_controller.stop()
            except Exception:
                pass
       
        if self.camera_started_by_gaming:
            try:
                if hasattr(hand_tracker, 'set_camera_state'):
                    hand_tracker.set_camera_state(False)
                if hasattr(hand_tracker, 'set_gesture_state'):
                    hand_tracker.set_gesture_state(False)
                time.sleep(0.1)
            except Exception:
                pass
            self.camera_started_by_gaming = False
       
        if self.gaming_canvas:
            try:
                self.gaming_canvas.stop_game()
                self.gaming_canvas.setVisible(False)
            except Exception:
                pass
       
        if self.ai_trainer_canvas:
            try:
                self.ai_trainer_canvas.stop_game()
                self.ai_trainer_canvas.setVisible(False)
            except Exception:
                pass
       
        if hasattr(self, 'no_game_widget'):
            self.no_game_widget.setVisible(True)
        if hasattr(self, 'footer'):
            self.footer.setVisible(False)
        if hasattr(self, 'fps_label'):
            self.fps_label.setText("0")
            self.fps_label.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
       
        """try:
            self.gesture_hud.set_game(None)
        except Exception:
            pass"""
       
        for btn in self.game_buttons.values():
            try:
                btn.setChecked(False)
            except Exception:
                pass
       
        if self.floating_camera:
            try:
                self.floating_camera.stop_preview()
                self.floating_camera.close()
                self.floating_camera = None
            except Exception:
                pass
       
        self.camera_btn.setText("◎ CAMERA FEED 📌")
        self.camera_btn.setChecked(False)
       
        try:
            self.direction_hud.set_direction(Direction.NONE)
        except Exception:
            pass
        self.current_direction = Direction.NONE
        self.current_game = None
        self.game_label.setText("NO GAME LOADED")
        self.game_label.setStyleSheet(f"color: {CyberColors.TEXT_DIM}; background: transparent;")
        self.last_processed_frame_id = None
       
        try:
            gc.collect()
        except Exception:
            pass

    def launch_mini_game(self, game_id):
        if self.is_closing:
            return

        self.current_game = game_id
        self.no_game_widget.setVisible(False)
        self.footer.setVisible(True)

        if self.gaming_canvas:
            self.gaming_canvas.setVisible(False)
        if self.ai_trainer_canvas:
            self.ai_trainer_canvas.setVisible(False)

        if game_id == "ai_trainer":
            if self.ai_trainer_canvas:
                self.ai_trainer_canvas.setVisible(True)
                self.ai_trainer_canvas.load_game()
                self.game_label.setText("◉ AI TRAINER ◉")
                self.game_label.setStyleSheet(f"color: {CyberColors.NEON_PURPLE}; background: transparent;")

        elif game_id == "runner":
            if self.gaming_canvas:
                self.gaming_canvas.setVisible(True)
                self.gaming_canvas.load_game("runner")
                self.game_label.setText("◉ CYBER RUNNER ◉")
                self.game_label.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")

        self.viewport_status.setText("ACTIVE")
        self.viewport_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
        self._status_dot.setStyleSheet(f"background: {CyberColors.NEON_GREEN}; border-radius: 4px;")

        for gid, btn in self.game_buttons.items():
            btn.setChecked(gid == game_id)

        if not self.is_gaming_active:
            self.start_gaming_mode()

    def showEvent(self, event):
        super().showEvent(event)
        if self.is_closing:
            return
        try:
            self.camera_was_active_before_entry = hand_tracker.get_camera_state() if hasattr(hand_tracker, 'get_camera_state') else False
        except Exception:
            self.camera_was_active_before_entry = False

    @safe_execute
    def _calculate_direction_from_position(self, hand_x, hand_y):
        try:
            if hand_x is None or hand_y is None:
                return Direction.NONE
            hand_x = max(0.0, min(1.0, float(hand_x)))
            hand_y = max(0.0, min(1.0, float(hand_y)))
            dx = hand_x - 0.5
            dy = hand_y - 0.5
            if abs(dx) < self.direction_threshold and abs(dy) < self.direction_threshold:
                return Direction.NONE
            if abs(dx) > abs(dy):
                return Direction.RIGHT if dx > self.direction_threshold else Direction.LEFT
            else:
                return Direction.DOWN if dy > self.direction_threshold else Direction.UP
        except Exception:
            return Direction.NONE

    def _safe_update_camera(self):
        if self.is_closing:
            return
        try:
            self.update_camera_feed()
        except Exception:
            pass

    @safe_execute
    def update_camera_feed(self):
        if self.is_closing or not self.is_gaming_active:
            return
        if not self.floating_camera or not self.floating_camera.isVisible():
            return
       
        current_time = time.time()
       
        frame = None
        try:
            frame = getattr(mode_manager, 'shared_frame', None)
        except Exception:
            return
       
        if frame is None:
            return
       
        frame_id = id(frame)
        if frame_id == self.last_processed_frame_id:
            return
       
        self.last_processed_frame_id = frame_id
        self.last_frame_time = current_time
        self.frame_count += 1
       
        try:
            if self.floating_camera.is_active:
                self.floating_camera.update_frame(frame)
        except Exception:
            pass
       
        if current_time - self._last_direction_time >= DIRECTION_THROTTLE:
            try:
                hand_pos = getattr(mode_manager, 'hand_position', None)
                if hand_pos and len(hand_pos) >= 2:
                    norm_x = hand_pos[0] / 640.0 if hand_pos[0] else 0.5
                    norm_y = hand_pos[1] / 480.0 if hand_pos[1] else 0.5
                    new_direction = self._calculate_direction_from_position(norm_x, norm_y)
                    if new_direction != self.current_direction or new_direction != Direction.NONE:
                        self.current_direction = new_direction
                        self._last_direction_time = current_time
                        if self.floating_camera:
                            self.floating_camera.update_direction(new_direction)
                        self.handle_direction(new_direction)
            except Exception:
                pass
       
        try:
            if self.floating_camera:
                action = f"{self.current_game or 'NONE'}".upper() if self.current_mode == "INTERNAL" else "KEYBOARD"
                self.floating_camera.update_action(action)
        except Exception:
            pass

    def check_camera_health(self):
        if self.is_closing or not self.is_gaming_active:
            return
        try:
            if time.time() - self.last_frame_time > 5:
                try:
                    if hasattr(hand_tracker, 'set_camera_state'):
                        hand_tracker.set_camera_state(False)
                        time.sleep(0.2)
                        hand_tracker.set_camera_state(True)
                except Exception:
                    pass
                self.last_frame_time = time.time()
                self.last_processed_frame_id = None
        except Exception:
            pass

    def calculate_fps(self):
        if self.is_closing:
            return
        self.current_fps = self.frame_count
        self.frame_count = 0
        try:
            if hasattr(self, 'fps_label'):
                self.fps_label.setText(f"{self.current_fps}")
                if self.current_fps >= 25:
                    self.fps_label.setStyleSheet(f"color: {CyberColors.NEON_GREEN}; background: transparent;")
                elif self.current_fps >= 15:
                    self.fps_label.setStyleSheet(f"color: {CyberColors.GOLD}; background: transparent;")
                else:
                    self.fps_label.setStyleSheet(f"color: {CyberColors.ORANGE}; background: transparent;")
            if self.floating_camera and self.is_gaming_active:
                self.floating_camera.update_fps(self.current_fps)
        except Exception:
            pass

    def hide_all_panels(self):
        self.mode_selection_frame.setVisible(False)
        self.internal_games_frame.setVisible(False)
        self.ai_trainer_details_frame.setVisible(False)
        self.cyber_runner_details_frame.setVisible(False)
        self.external_frame.setVisible(False)

    def show_mode_selection(self):
        self.hide_all_panels()
        self.mode_selection_frame.setVisible(True)
        self.current_mode = None
        """try:
            self.gesture_hud.set_mode("INTERNAL")
        except Exception:
            pass"""

    def show_internal_games(self):
        self.hide_all_panels()
        self.internal_games_frame.setVisible(True)
        self.current_mode = "INTERNAL"
        """try:
            self.gesture_hud.set_mode("INTERNAL")
        except Exception:
            pass"""

    def show_external_options(self):
        self.hide_all_panels()
        self.external_frame.setVisible(True)
        self.current_mode = "EXTERNAL"
        if GAME_CONTROLLER_AVAILABLE and game_controller:
            try:
                game_controller.set_control_mode("EXTERNAL")
            except Exception:
                pass

    def show_ai_trainer_details(self):
        self.hide_all_panels()
        self.ai_trainer_details_frame.setVisible(True)

    def show_cyber_runner_details(self):
        self.hide_all_panels()
        self.cyber_runner_details_frame.setVisible(True)

    @safe_execute
    def handle_gesture(self, gesture_name):
        if self.is_closing or not self.is_gaming_active:
            return
        if not gesture_name or gesture_name == "NONE":
            return
        try:
            if self.current_mode == "INTERNAL":
                if self.current_game == "ai_trainer" and self.ai_trainer_canvas:
                    self.ai_trainer_canvas.handle_gesture(gesture_name)
                elif self.current_game == "runner" and self.gaming_canvas:
                    self.gaming_canvas.handle_gesture(gesture_name)
            else:
                if GAME_CONTROLLER_AVAILABLE and game_controller:
                    game_controller.execute_game_action(gesture_name)
        except Exception:
            pass

    @safe_execute
    def handle_direction(self, direction):
        if self.is_closing or not self.is_gaming_active:
            return
        try:
            if hasattr(self, 'direction_hud') and self.direction_hud:
                self.direction_hud.set_direction(direction)
        except Exception:
            pass
        try:
            if self.current_mode == "INTERNAL":
                if self.current_game == "ai_trainer" and self.ai_trainer_canvas:
                    self.ai_trainer_canvas.handle_direction(direction)
                elif self.current_game == "runner" and self.gaming_canvas:
                    self.gaming_canvas.handle_direction(direction)
            else:
                if GAME_CONTROLLER_AVAILABLE and game_controller:
                    game_controller.handle_direction(direction)
        except Exception:
            pass

    def _on_game_over(self, game_name, score):
        if self.is_closing:
            return
        for btn in self.game_buttons.values():
            try:
                btn.setChecked(False)
            except Exception:
                pass
        self.score_label.setText(f"{score:,}")
        self.gesture_status.setText(f"💀 GAME OVER!")
        self.gesture_status.setStyleSheet(f"color: {CyberColors.ORANGE};")

    def _on_game_started(self, game_name):
        if self.is_closing:
            return
        self.gesture_status.setText(f"🎓 TRAINING")
        self.gesture_status.setStyleSheet(f"color: {CyberColors.NEON_GREEN};")

    def exit_to_desktop(self):
        if self.is_closing:
            return
       
        if self.is_gaming_active:
            self.is_gaming_active = False
            for timer in [self.health_timer, self.camera_timer, self.anim_timer, self.fps_timer]:
                try:
                    timer.stop()
                except Exception:
                    pass
           
            self.hologram_panel.stop_animations()
           
            if GAME_CONTROLLER_AVAILABLE and game_controller:
                try:
                    game_controller.set_game_callback(None)
                    game_controller.stop()
                except Exception:
                    pass
           
            if self.gaming_canvas:
                try:
                    self.gaming_canvas.stop_game()
                except Exception:
                    pass
           
            if self.floating_camera:
                try:
                    self.floating_camera.stop_preview()
                    self.floating_camera.close()
                    self.floating_camera = None
                except Exception:
                    pass
       
        try:
            mode_manager.set_mode("DESKTOP")
            if hasattr(mode_manager, 'set_gaming_page'):
                mode_manager.set_gaming_page(None)
        except Exception:
            pass
       
        try:
            gc.collect()
        except Exception:
            pass
       
        self.switch_to_desktop.emit(self.camera_was_active_before_entry)

    def cleanup(self):
        if self.is_closing:
            return
        self.is_closing = True
        self.is_gaming_active = False
       
        for timer in [self.camera_timer, self.fps_timer, self.health_timer, self.anim_timer]:
            try:
                if timer and timer.isActive():
                    timer.stop()
            except Exception:
                pass
       
        try:
            self.hologram_panel.cleanup()
        except Exception:
            pass
       
        try:
            QApplication.processEvents()
            time.sleep(0.05)
        except Exception:
            pass
       
        try:
            if hasattr(self, 'direction_hud') and self.direction_hud:
                self.direction_hud.cleanup()
        except Exception:
            pass
       
        try:
            if self.floating_camera:
                self.floating_camera.stop_preview()
                self.floating_camera.close()
                self.floating_camera.deleteLater()
                self.floating_camera = None
        except Exception:
            pass
       
        try:
            if self.gaming_canvas:
                self.gaming_canvas.cleanup()
                self.gaming_canvas = None
        except Exception:
            pass
       
        try:
            if self.ai_trainer_canvas:
                self.ai_trainer_canvas.stop_game()
                self.ai_trainer_canvas = None
        except Exception:
            pass
       
        try:
            if GAME_CONTROLLER_AVAILABLE and game_controller:
                game_controller.set_game_callback(None)
                game_controller.stop()
        except Exception:
            pass
       
        try:
            if self.camera_started_by_gaming:
                if hasattr(hand_tracker, 'set_camera_state'):
                    hand_tracker.set_camera_state(False)
                if hasattr(hand_tracker, 'set_gesture_state'):
                    hand_tracker.set_gesture_state(False)
        except Exception:
            pass
       
        self.last_processed_frame_id = None
        try:
            gc.collect()
        except Exception:
            pass

    def closeEvent(self, event):
        self.cleanup()
        event.accept()

    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {CyberColors.NAVY_DARKEST},
                    stop:0.5 {CyberColors.NAVY_DARK},
                    stop:1 {CyberColors.NAVY_DARKEST});
                color: {CyberColors.TEXT_WHITE};
                font-family: Consolas;
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═" * 70)
    print("     🎮 AUREVIX GAMING SYSTEM v3.5 — CONTROLLER HUD 🎮")
    print("═" * 70)
    print(f" Canvas: {'✅' if GAMING_CANVAS_AVAILABLE else '❌'}")
    print(f" Controller: {'✅' if GAME_CONTROLLER_AVAILABLE else '❌'}")
    print("\n 🎨 CHANGES:")
    print(" • ✅ CHANGE 1: HologramCenterPanel — grid, hex corners, radar sweep")
    print(" • ✅ CHANGE 2: Header — gaming HUD with LED dots, status pill, FPS badge")
    print(" • ✅ CHANGE 3: Placeholder — controller D-pad, ABXY buttons, shoulder btns")
    print("═" * 70 + "\n")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GamingModePage()
    window.show()
    window.raise_()
    window.activateWindow()
    
    sys.exit(app.exec())