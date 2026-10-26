"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GAMING MODE - CAMERA WIDGET                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains:
- UltraHolographicCameraWidget
- Camera display with holographic effects
- Data overlay and glitch effects
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QColor, QPainter, QPen,
    QLinearGradient, QRadialGradient
)
import cv2
import random
import math
from datetime import datetime

from gaming_mode.constants import CyberColors


# ═══════════════════════════════════════════════════════════════════════════════
# ✨ ULTRA HOLOGRAPHIC CAMERA WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
class UltraHolographicCameraWidget(QWidget):
    """Ultra Holographic Camera Display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame = None
        self.is_active = False
        self.animation_frame = 0
        self.scanline_offset = 0
        self.glitch_active = False
        self.glitch_lines = []
        self.noise_alpha = 0
        
        self.signal_strength = 100
        self.frame_count = 0
        
        self.setStyleSheet(f"background: {CyberColors.NAVY_DARKEST};")
        
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate)
        
        self.glitch_timer = QTimer()
        self.glitch_timer.timeout.connect(self._trigger_glitch)
    
    def set_active(self, active):
        self.is_active = active
        if active:
            self.anim_timer.start(100)  # ✅ CHANGED: 10 FPS instead of 30
            self.glitch_timer.start(3000)
        else:
            self.anim_timer.stop()
            self.glitch_timer.stop()
    
    def _animate(self):
        self.animation_frame = (self.animation_frame + 1) % 360
        self.scanline_offset = (self.scanline_offset + 2) % self.height()
        self.frame_count += 1
        
        self.noise_alpha = random.randint(0, 20) if random.random() < 0.1 else 0
        self.signal_strength = max(85, min(100, self.signal_strength + random.randint(-2, 2)))
        
        self.update()
    
    def _trigger_glitch(self):
        if random.random() < 0.4:
            self.glitch_active = True
            self.glitch_lines = []
            for _ in range(random.randint(3, 8)):
                self.glitch_lines.append({
                    'y': random.randint(0, self.height()),
                    'height': random.randint(2, 15),
                    'offset': random.randint(-20, 20),
                    'type': random.choice(['rgb', 'shift', 'noise'])
                })
            QTimer.singleShot(random.randint(50, 150), lambda: setattr(self, 'glitch_active', False))
    
    def update_frame(self, frame, glitch=False, glitch_offset=0, chroma=0):
        """Update frame - CRASH-SAFE VERSION"""
        if frame is None:
            return
        
        try:
            w = self.width() - 8
            h = self.height() - 8
            
            # Safety checks
            if w < 10 or h < 10:
                return
            if not hasattr(frame, 'shape'):
                return
            if len(frame.shape) < 2:
                return
            if frame.shape[0] < 10 or frame.shape[1] < 10:
                return
            
            # Resize with error handling - use INTER_NEAREST for speed
            try:
                resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_NEAREST)
            except cv2.error:
                return
            except Exception:
                return
            
            # Convert color safely
            try:
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            except cv2.error:
                return
            except Exception:
                return
            
            # Create QImage safely
            try:
                h_img, w_img = rgb.shape[:2]
                bytes_per_line = 3 * w_img
                qimg = QImage(rgb.data, w_img, h_img, bytes_per_line, QImage.Format_RGB888)
                self.current_frame = QPixmap.fromImage(qimg.copy())  # .copy() prevents memory issues
            except Exception:
                return
            
            # Update display
            self.update()
            
        except Exception as e:
            # Silent fail - don't crash
            pass
    
    def clear_frame(self):
        self.current_frame = None
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        bg_gradient = QLinearGradient(0, 0, 0, h)
        bg_gradient.setColorAt(0, QColor(5, 15, 25))
        bg_gradient.setColorAt(0.5, QColor(8, 20, 35))
        bg_gradient.setColorAt(1, QColor(5, 15, 25))
        painter.fillRect(0, 0, w, h, bg_gradient)
        
        if self.current_frame and not self.current_frame.isNull():
            painter.drawPixmap(4, 4, self.current_frame)
            
            if self.is_active:
                # ✅ SIMPLIFIED: Only essential overlays for performance
                # Removed: scanlines, grid, targeting brackets, crosshair
                
                # Just show data overlay
                self._draw_data_overlay(painter, w, h)
                
                # Glitch
                if self.glitch_active:
                    self._draw_glitch_effect(painter, w, h)
                
                # Noise
                if self.noise_alpha > 0:
                    for _ in range(50):
                        nx = random.randint(0, w)
                        ny = random.randint(0, h)
                        painter.fillRect(nx, ny, 2, 2, QColor(255, 255, 255, self.noise_alpha))
        else:
            self._draw_no_signal(painter, w, h)
        
        # Border
        border_color = QColor(0, 255, 255, 150) if self.is_active else QColor(0, 100, 130, 100)
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(1, 1, w - 2, h - 2)
        
        painter.end()
    
    def _draw_targeting_brackets(self, painter, w, h):
        bracket_size = 35
        bracket_thickness = 3
        margin = 15
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.1)
        color = QColor(0, 255, 200, int(150 + 100 * pulse))
        painter.setPen(QPen(color, bracket_thickness))
        
        painter.drawLine(margin, margin, margin + bracket_size, margin)
        painter.drawLine(margin, margin, margin, margin + bracket_size)
        
        painter.drawLine(w - margin, margin, w - margin - bracket_size, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + bracket_size)
        
        painter.drawLine(margin, h - margin, margin + bracket_size, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - bracket_size)
        
        painter.drawLine(w - margin, h - margin, w - margin - bracket_size, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - bracket_size)
        
        painter.setBrush(color)
        for cx, cy in [(margin, margin), (w - margin, margin),
                       (margin, h - margin), (w - margin, h - margin)]:
            painter.drawEllipse(QPoint(cx, cy), 4, 4)
    
    def _draw_data_overlay(self, painter, w, h):
        panel_bg = QColor(0, 20, 40, 180)
        painter.fillRect(8, 8, 120, 50, panel_bg)
        painter.setPen(QPen(QColor(0, 255, 255, 100), 1))
        painter.drawRect(8, 8, 120, 50)
        
        painter.setPen(QColor(0, 255, 200))
        painter.setFont(QFont("Consolas", 8))
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-4]
        painter.drawText(12, 22, f"TIME: {timestamp}")
        painter.drawText(12, 34, f"FRM: {self.frame_count:06d}")
        painter.drawText(12, 46, f"SIG: {self.signal_strength}%")
        
        bar_width = int(80 * self.signal_strength / 100)
        painter.fillRect(12, 50, bar_width, 4, QColor(0, 255, 136, 200))
        
        status_text = "● TRACKING ACTIVE" if self.is_active else "○ STANDBY"
        painter.setPen(QColor(CyberColors.NEON_GREEN) if self.is_active else QColor(CyberColors.TEXT_DIM))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(w - 130, 22, status_text)
        
        painter.fillRect(8, h - 35, 100, 27, panel_bg)
        painter.setPen(QPen(QColor(0, 255, 255, 100), 1))
        painter.drawRect(8, h - 35, 100, 27)
        
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(12, h - 22, f"X: {w // 2:04d}")
        painter.drawText(60, h - 22, f"Y: {h // 2:04d}")
        painter.drawText(12, h - 12, f"RES: {w}x{h}")
    
    def _draw_center_crosshair(self, painter, w, h):
        cx, cy = w // 2, h // 2
        size = 25
        gap = 8
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.15)
        color = QColor(0, 255, 200, int(100 + 100 * pulse))
        painter.setPen(QPen(color, 2))
        
        painter.drawLine(cx - size, cy, cx - gap, cy)
        painter.drawLine(cx + gap, cy, cx + size, cy)
        painter.drawLine(cx, cy - size, cx, cy - gap)
        painter.drawLine(cx, cy + gap, cx, cy + size)
        
        painter.setBrush(color)
        painter.drawEllipse(QPoint(cx, cy), 3, 3)
        
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.animation_frame)
        painter.setPen(QPen(QColor(0, 255, 255, 60), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(0, 0), 40, 40)
        
        for i in range(0, 360, 30):
            painter.drawLine(38, 0, 42, 0)
            painter.rotate(30)
        
        painter.restore()
    
    def _draw_glitch_effect(self, painter, w, h):
        for line in self.glitch_lines:
            y = line['y']
            height = line['height']
            offset = line['offset']
            glitch_type = line['type']
            
            if glitch_type == 'rgb':
                painter.fillRect(offset, y, w, height, QColor(255, 0, 0, 60))
                painter.fillRect(-offset, y + 1, w, height, QColor(0, 255, 255, 60))
            elif glitch_type == 'shift':
                painter.fillRect(0, y, w, height, QColor(255, 255, 255, 40))
            else:
                for x in range(0, w, 3):
                    if random.random() > 0.5:
                        painter.fillRect(x, y, 3, height, QColor(255, 255, 255, 80))
    
    def _draw_no_signal(self, painter, w, h):
        for _ in range(500):
            x = random.randint(0, w)
            y = random.randint(0, h)
            size = random.randint(1, 3)
            alpha = random.randint(20, 60)
            painter.fillRect(x, y, size, size, QColor(100, 150, 180, alpha))
        
        for y in range(0, h, 4):
            painter.fillRect(0, y, w, 2, QColor(0, 50, 70, 30))
        
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 14, QFont.Bold))
        painter.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "◎ INITIALIZING OPTICAL FEED...")
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.1)
        painter.setPen(QPen(QColor(0, 150, 200, int(80 + 50 * pulse)), 2))
        painter.drawRect(10, 10, w - 20, h - 20)