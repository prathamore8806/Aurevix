# calibration_page.py - Complete Enhanced Calibration Page with HOLOGRAM MODE
# PART 1 OF 3 - Imports, Config, and Basic Components
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ CALIBRATION PAGE V3.0 — HOLOGRAM EDITION ⬡                              ║
║  Futuristic Cyberpunk HUD • Neon Glow Effects • Smart Tracking              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import cv2
import config
import time
import math
import json
import os
import threading
import numpy as np
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Callable, Tuple
from collections import deque
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QProgressBar, QFrame, QGridLayout, QSlider, QCheckBox,
    QGroupBox, QPushButton, QDialog, QLineEdit, QSpinBox,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QScrollArea, QInputDialog, QGraphicsDropShadowEffect,
    QSizePolicy, QStackedWidget, QTabWidget, QSpacerItem,
    QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, Property, QPoint, QSize, QRect
from PySide6.QtGui import QImage, QPixmap, QFont, QPainter, QColor, QPen, QLinearGradient, QBrush, QRadialGradient

from glass_card import GlassCard
from notification_manager import get_notification_manager, NotificationType, Notification
from notification_popup import get_toast_manager

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️ MediaPipe not available")

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    AUDIO_AVAILABLE = True
except:
    AUDIO_AVAILABLE = False
    print("⚠️ Audio not available")


# ============================================================
#                    CONFIGURATION
# ============================================================

CAMERA_WIDTH = 800
CAMERA_HEIGHT = 600
CAPTURE_WIDTH = 800
CAPTURE_HEIGHT = 600
TARGET_MARGIN_TOP = 80
TARGET_MARGIN_BOTTOM = 80
TARGET_MARGIN_LEFT = 80
TARGET_MARGIN_RIGHT = 80


# ============================================================
#                    ⬡ HOLOGRAM CONFIGURATION ⬡
# ============================================================

@dataclass
class HologramConfig:
    """⬡ Hologram visual configuration"""
    enabled: bool = False
    theme: str = "cyan"
    glow_intensity: float = 1.0
    scan_line_speed: float = 1.0
    scan_line_opacity: float = 0.3
    grid_enabled: bool = True
    grid_spacing: int = 40
    particle_enabled: bool = True
    particle_count: int = 50
    glitch_enabled: bool = True
    glitch_intensity: float = 0.3
    corner_brackets: bool = True
    hud_elements: bool = True
    chromatic_aberration: bool = True
    
    THEMES = {
        "cyan": {"primary": (255, 255, 0), "secondary": (255, 200, 0), "accent": (255, 255, 100), "glow": (0, 255, 255)},
        "purple": {"primary": (255, 0, 255), "secondary": (200, 0, 200), "accent": (255, 100, 255), "glow": (255, 0, 255)},
        "green": {"primary": (0, 255, 0), "secondary": (0, 200, 0), "accent": (100, 255, 100), "glow": (0, 255, 0)},
        "red": {"primary": (50, 50, 255), "secondary": (30, 30, 200), "accent": (100, 100, 255), "glow": (0, 0, 255)},
        "orange": {"primary": (0, 165, 255), "secondary": (0, 130, 200), "accent": (50, 190, 255), "glow": (0, 165, 255)},
        "pink": {"primary": (180, 105, 255), "secondary": (140, 80, 200), "accent": (200, 130, 255), "glow": (180, 105, 255)},
    }
    
    def get_colors(self) -> dict:
        return self.THEMES.get(self.theme, self.THEMES["cyan"])


class HologramRenderer:
    """⬡ Renders hologram effects on camera frame"""
    
    def __init__(self, config: HologramConfig = None):
        self.config = config or HologramConfig()
        self.scan_line_y = 0
        self.particles = []
        self.glitch_timer = 0
        self.frame_count = 0
        self.last_glitch_time = 0
        self._init_particles()
        
    def _init_particles(self):
        self.particles = []
        for _ in range(self.config.particle_count):
            self.particles.append({
                'x': np.random.randint(0, CAMERA_WIDTH),
                'y': np.random.randint(0, CAMERA_HEIGHT),
                'vx': np.random.uniform(-0.5, 0.5),
                'vy': np.random.uniform(-0.3, 0.3),
                'size': np.random.randint(1, 4),
                'alpha': np.random.uniform(0.3, 0.8),
                'pulse_offset': np.random.uniform(0, 2 * math.pi)
            })
    
    def update_config(self, config: HologramConfig):
        self.config = config
        if len(self.particles) != config.particle_count:
            self._init_particles()
    
    def render(self, frame: np.ndarray) -> np.ndarray:
        if not self.config.enabled:
            return frame
        
        self.frame_count += 1
        h, w = frame.shape[:2]
        colors = self.config.get_colors()
        
        if self.config.chromatic_aberration:
            frame = self._apply_chromatic_aberration(frame)
        
        if self.config.grid_enabled:
            frame = self._draw_hologram_grid(frame, w, h, colors)
        
        frame = self._draw_scan_lines(frame, w, h, colors)
        
        if self.config.particle_enabled:
            frame = self._draw_particles(frame, w, h, colors)
        
        if self.config.corner_brackets:
            frame = self._draw_corner_brackets(frame, w, h, colors)
        
        if self.config.hud_elements:
            frame = self._draw_hud_elements(frame, w, h, colors)
        
        if self.config.glitch_enabled:
            frame = self._apply_glitch_effect(frame, w, h)
        
        frame = self._apply_hologram_tint(frame, colors)
        
        return frame
    
    def _apply_chromatic_aberration(self, frame: np.ndarray) -> np.ndarray:
        b, g, r = cv2.split(frame)
        rows, cols = frame.shape[:2]
        M_left = np.float32([[1, 0, -2], [0, 1, 0]])
        M_right = np.float32([[1, 0, 2], [0, 1, 0]])
        r = cv2.warpAffine(r, M_right, (cols, rows))
        b = cv2.warpAffine(b, M_left, (cols, rows))
        return cv2.merge([b, g, r])
    
    def _draw_hologram_grid(self, frame: np.ndarray, w: int, h: int, colors: dict) -> np.ndarray:
        overlay = frame.copy()
        spacing = self.config.grid_spacing
        primary = colors['primary']
        
        for x in range(0, w, spacing):
            alpha = 0.1 + 0.05 * math.sin(x / 50 + self.frame_count * 0.02)
            color = tuple(int(c * alpha) for c in primary)
            cv2.line(overlay, (x, 0), (x, h), color, 1, cv2.LINE_AA)
        
        for y in range(0, h, spacing):
            alpha = 0.1 + 0.05 * math.sin(y / 50 + self.frame_count * 0.02)
            color = tuple(int(c * alpha) for c in primary)
            cv2.line(overlay, (0, y), (w, y), color, 1, cv2.LINE_AA)
        
        for x in range(0, w, spacing):
            for y in range(0, h, spacing):
                cv2.circle(overlay, (x, y), 2, primary, -1, cv2.LINE_AA)
        
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        return frame
    
    def _draw_scan_lines(self, frame: np.ndarray, w: int, h: int, colors: dict) -> np.ndarray:
        self.scan_line_y = (self.scan_line_y + int(3 * self.config.scan_line_speed)) % (h + 100)
        overlay = frame.copy()
        primary = colors['primary']
        
        line_y = self.scan_line_y - 50
        if 0 <= line_y < h:
            for i in range(30):
                alpha = (30 - i) / 30 * self.config.scan_line_opacity
                color = tuple(int(c * alpha) for c in primary)
                y = line_y + i
                if 0 <= y < h:
                    cv2.line(overlay, (0, y), (w, y), color, 1)
        
        for y in range(0, h, 3):
            alpha = 0.03 + 0.02 * math.sin(y * 0.5 + self.frame_count * 0.1)
            overlay[y:y+1, :] = (overlay[y:y+1, :] * (1 - alpha)).astype(np.uint8)
        
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        return frame
    
    def _draw_particles(self, frame: np.ndarray, w: int, h: int, colors: dict) -> np.ndarray:
        accent = colors['accent']
        
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            if p['x'] < 0: p['x'] = w
            if p['x'] > w: p['x'] = 0
            if p['y'] < 0: p['y'] = h
            if p['y'] > h: p['y'] = 0
            
            pulse = 0.5 + 0.5 * math.sin(self.frame_count * 0.05 + p['pulse_offset'])
            alpha = p['alpha'] * pulse
            
            pos = (int(p['x']), int(p['y']))
            color = tuple(int(c * alpha) for c in accent)
            cv2.circle(frame, pos, p['size'] + 2, color, -1, cv2.LINE_AA)
            cv2.circle(frame, pos, p['size'], (255, 255, 255), -1, cv2.LINE_AA)
        
        return frame
    
    def _draw_corner_brackets(self, frame: np.ndarray, w: int, h: int, colors: dict) -> np.ndarray:
        primary = colors['primary']
        bracket_size = 60
        thickness = 2
        margin = 20
        
        pulse = 0.7 + 0.3 * math.sin(self.frame_count * 0.03)
        color = tuple(int(c * pulse) for c in primary)
        
        cv2.line(frame, (margin, margin), (margin + bracket_size, margin), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (margin, margin), (margin, margin + bracket_size), color, thickness, cv2.LINE_AA)
        
        cv2.line(frame, (w - margin, margin), (w - margin - bracket_size, margin), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (w - margin, margin), (w - margin, margin + bracket_size), color, thickness, cv2.LINE_AA)
        
        cv2.line(frame, (margin, h - margin), (margin + bracket_size, h - margin), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (margin, h - margin), (margin, h - margin - bracket_size), color, thickness, cv2.LINE_AA)
        
        cv2.line(frame, (w - margin, h - margin), (w - margin - bracket_size, h - margin), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (w - margin, h - margin), (w - margin, h - margin - bracket_size), color, thickness, cv2.LINE_AA)
        
        for corner in [(margin, margin), (w - margin, margin), (margin, h - margin), (w - margin, h - margin)]:
            cv2.circle(frame, corner, 4, color, -1, cv2.LINE_AA)
            cv2.circle(frame, corner, 8, color, 1, cv2.LINE_AA)
        
        return frame
    
    def _draw_hud_elements(self, frame: np.ndarray, w: int, h: int, colors: dict) -> np.ndarray:
        primary = colors['primary']
        secondary = colors['secondary']
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 35), (20, 20, 30), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-4]
        cv2.putText(frame, f"HOLOGRAM MODE", (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, primary, 1, cv2.LINE_AA)
        cv2.putText(frame, f"SYS: ACTIVE", (200, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.4, secondary, 1, cv2.LINE_AA)
        cv2.putText(frame, timestamp, (w - 120, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.4, primary, 1, cv2.LINE_AA)
        
        cv2.rectangle(overlay, (0, h - 30), (w, h), (20, 20, 30), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        cv2.putText(frame, "TRACKING", (15, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, f"RES: {w}x{h}", (150, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, secondary, 1, cv2.LINE_AA)
        cv2.putText(frame, f"FRAME: {self.frame_count:06d}", (w - 150, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, primary, 1, cv2.LINE_AA)
        
        for i in range(5):
            y = 80 + i * 25
            length = 30 + (i % 3) * 10
            alpha = 0.3 + 0.2 * math.sin(self.frame_count * 0.05 + i)
            color = tuple(int(c * alpha) for c in primary)
            cv2.line(frame, (10, y), (10 + length, y), color, 2, cv2.LINE_AA)
            cv2.line(frame, (w - 10 - length, y), (w - 10, y), color, 2, cv2.LINE_AA)
        
        return frame
    
    def _apply_glitch_effect(self, frame: np.ndarray, w: int, h: int) -> np.ndarray:
        now = time.time()
        
        if now - self.last_glitch_time > np.random.uniform(2, 5):
            self.last_glitch_time = now
            self.glitch_timer = np.random.randint(3, 10)
        
        if self.glitch_timer > 0:
            self.glitch_timer -= 1
            
            num_slices = np.random.randint(1, 4)
            for _ in range(num_slices):
                y = np.random.randint(0, h - 20)
                slice_h = np.random.randint(5, 20)
                shift = np.random.randint(-20, 20)
                
                if 0 <= y < h and 0 <= y + slice_h < h:
                    slice_data = frame[y:y+slice_h, :].copy()
                    frame[y:y+slice_h, :] = np.roll(slice_data, shift, axis=1)
            
            if np.random.random() < self.config.glitch_intensity:
                b, g, r = cv2.split(frame)
                shift = np.random.randint(-5, 5)
                r = np.roll(r, shift, axis=1)
                frame = cv2.merge([b, g, r])
        
        return frame
    
    def _apply_hologram_tint(self, frame: np.ndarray, colors: dict) -> np.ndarray:
        glow = colors['glow']
        
        overlay = np.zeros_like(frame)
        overlay[:] = glow
        
        alpha = 0.08 * self.config.glow_intensity
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha * 0.5, 0, frame)
        
        rows, cols = frame.shape[:2]
        X = np.arange(0, cols)
        Y = np.arange(0, rows)
        X, Y = np.meshgrid(X, Y)
        
        center_x, center_y = cols / 2, rows / 2
        vignette = 1 - np.sqrt((X - center_x)**2 + (Y - center_y)**2) / (np.sqrt(center_x**2 + center_y**2) * 1.2)
        vignette = np.clip(vignette, 0.6, 1)
        
        for i in range(3):
            frame[:, :, i] = (frame[:, :, i] * vignette).astype(np.uint8)
        
        return frame


# ============================================================
#                    UI COMPONENTS
# ============================================================

class ModernButton(QPushButton):
    def __init__(self, text: str = "", icon: str = "", style: str = "primary", 
                 size: str = "normal", parent=None):
        super().__init__(parent)
        self.setText(f"{icon} {text}".strip() if icon else text)
        self.style_type = style
        self.size_type = size
        self.setCursor(Qt.PointingHandCursor)
        self._setup_size()
        self._setup_style()
        self._setup_shadow()
        
    def _setup_size(self):
        sizes = {
            "tiny": (28, 10, 16, 11), "small": (32, 8, 14, 11),
            "normal": (36, 10, 18, 12), "medium": (40, 10, 20, 12), "large": (44, 12, 24, 13)
        }
        h, vpad, hpad, font = sizes.get(self.size_type, sizes["normal"])
        self.setMinimumHeight(h)
        self.setMaximumHeight(h + 4)
        self._vpad, self._hpad, self._font_size = vpad, hpad, font
        
    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 3)
        colors = {
            "primary": QColor(0, 212, 255, 60), "success": QColor(0, 255, 136, 60),
            "warning": QColor(255, 170, 0, 60), "danger": QColor(255, 85, 85, 60),
            "hologram": QColor(0, 255, 255, 80),
        }
        shadow.setColor(colors.get(self.style_type, QColor(0, 0, 0, 30)))
        self.setGraphicsEffect(shadow)
        
    def _setup_style(self):
        base_styles = {
            "primary": ("0, 212, 255", "0, 150, 200", "0, 230, 255", "0, 180, 220"),
            "success": ("0, 255, 136", "0, 200, 100", "50, 255, 160", "30, 220, 120"),
            "warning": ("255, 170, 0", "220, 130, 0", "255, 190, 50", "240, 150, 30"),
            "danger": ("255, 85, 85", "200, 50, 50", "255, 110, 110", "220, 70, 70"),
            "hologram": ("0, 255, 255", "0, 200, 200", "50, 255, 255", "0, 230, 230"),
        }
        
        if self.style_type in base_styles:
            c1, c2, h1, h2 = base_styles[self.style_type]
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({c1}, 0.85), stop:1 rgba({c2}, 0.85));
                    color: white; border: none; border-radius: 8px;
                    padding: {self._vpad}px {self._hpad}px;
                    font-size: {self._font_size}px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({h1}, 1), stop:1 rgba({h2}, 1));
                }}
                QPushButton:pressed {{ padding-top: {self._vpad + 2}px; }}
                QPushButton:disabled {{ background: rgba(100, 100, 100, 0.4); color: rgba(255, 255, 255, 0.4); }}
            """)
        elif self.style_type == "ghost":
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.03); color: rgba(255, 255, 255, 0.75);
                    border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px;
                    padding: {self._vpad}px {self._hpad}px; font-size: {self._font_size}px;
                }}
                QPushButton:hover {{ background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.3); color: white; }}
            """)
        elif self.style_type == "glass":
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.1), stop:1 rgba(255, 255, 255, 0.03));
                    color: rgba(255, 255, 255, 0.85); border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 8px; padding: {self._vpad}px {self._hpad}px; font-size: {self._font_size}px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 212, 255, 0.15), stop:1 rgba(0, 212, 255, 0.05));
                    border-color: rgba(0, 212, 255, 0.4); color: #00d4ff;
                }}
            """)


class ModernToggle(QWidget):
    toggled = Signal(bool)
    
    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._handle_position = 22 if checked else 2
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        
        self._animation = QPropertyAnimation(self, b"handle_position")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def get_handle_position(self): return self._handle_position
    def set_handle_position(self, pos): self._handle_position = pos; self.update()
    handle_position = Property(float, get_handle_position, set_handle_position)
    
    def isChecked(self): return self._checked
    
    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animation.setStartValue(self._handle_position)
            self._animation.setEndValue(22 if checked else 2)
            self._animation.start()
            self.toggled.emit(checked)
    
    def mousePressEvent(self, event): self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track_color = QColor(0, 212, 255) if self._checked else QColor(80, 80, 100)
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 46, 26, 13, 13)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(self._handle_position), 2, 22, 22)


class HologramToggle(QWidget):
    """⬡ Special hologram-themed toggle switch"""
    toggled = Signal(bool)
    
    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._handle_position = 26 if checked else 2
        self._glow_phase = 0
        self.setFixedSize(54, 28)
        self.setCursor(Qt.PointingHandCursor)
        
        self._animation = QPropertyAnimation(self, b"handle_position")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._update_glow)
        self._glow_timer.start(50)
        
    def get_handle_position(self): return self._handle_position
    def set_handle_position(self, pos): self._handle_position = pos; self.update()
    handle_position = Property(float, get_handle_position, set_handle_position)
    
    def _update_glow(self):
        if self._checked:
            self._glow_phase = (self._glow_phase + 0.1) % (2 * math.pi)
            self.update()
    
    def isChecked(self): return self._checked
    
    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animation.setStartValue(self._handle_position)
            self._animation.setEndValue(26 if checked else 2)
            self._animation.start()
            self.toggled.emit(checked)
    
    def mousePressEvent(self, event): self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._checked:
            glow_alpha = int(40 + 20 * math.sin(self._glow_phase))
            painter.setBrush(QColor(0, 255, 255, glow_alpha))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(-3, -3, 60, 34, 17, 17)
        
        if self._checked:
            gradient = QLinearGradient(0, 0, 54, 0)
            gradient.setColorAt(0, QColor(0, 200, 200))
            gradient.setColorAt(0.5, QColor(0, 255, 255))
            gradient.setColorAt(1, QColor(0, 200, 200))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor(0, 255, 255), 1))
        else:
            painter.setBrush(QColor(50, 50, 70))
            painter.setPen(QPen(QColor(70, 70, 90), 1))
        
        painter.drawRoundedRect(0, 0, 54, 28, 14, 14)
        
        handle_x = int(self._handle_position)
        if self._checked:
            glow_size = int(24 + 2 * math.sin(self._glow_phase))
            painter.setBrush(QColor(0, 255, 255, 50))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(handle_x - 1, 1, glow_size + 2, glow_size + 2)
        
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawEllipse(handle_x, 2, 24, 24)
        
        painter.setFont(QFont("Segoe UI", 10))
        if self._checked:
            painter.setPen(QColor(0, 200, 200))
            painter.drawText(QRect(handle_x, 2, 24, 24), Qt.AlignCenter, "⬡")
        else:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(QRect(handle_x, 2, 24, 24), Qt.AlignCenter, "○")


class PointCountSelector(QFrame):
    pointCountChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pointSelector")
        self._current = config.calibration_point_count
        self._build_ui()
        
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        
        label = QLabel("📍 Calibration Points:")
        label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(label)
        
        self.buttons = {}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        for count in [4, 9, 16]:
            btn = QPushButton(str(count))
            btn.setCheckable(True)
            btn.setChecked(count == self._current)
            btn.setFixedSize(50, 34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: rgba(255, 255, 255, 0.06); color: rgba(255, 255, 255, 0.7);
                    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; font-size: 13px; font-weight: 600; }
                QPushButton:hover { background: rgba(0, 212, 255, 0.12); border-color: rgba(0, 212, 255, 0.4); color: #00d4ff; }
                QPushButton:checked { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 212, 255, 0.3), stop:1 rgba(0, 180, 220, 0.2)); border-color: rgba(0, 212, 255, 0.8); color: #00d4ff; }
                QPushButton:disabled { background: rgba(255, 255, 255, 0.02); color: rgba(255, 255, 255, 0.3); }
            """)
            btn.clicked.connect(lambda checked, c=count: self._select(c))
            self.buttons[count] = btn
            self.button_group.addButton(btn)
            layout.addWidget(btn)
        
        grid_names = {4: "(2×2 Grid)", 9: "(3×3 Grid)", 16: "(4×4 Grid)"}
        self.grid_label = QLabel(grid_names.get(self._current, "(2×2 Grid)"))
        self.grid_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px; margin-left: 8px; background: transparent;")
        layout.addWidget(self.grid_label)
        layout.addStretch()
        
        self.setStyleSheet("""
            #pointSelector {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06));
                border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px;
            }
        """)
        
    def _select(self, count: int):
        self._current = count
        for c, btn in self.buttons.items(): btn.setChecked(c == count)
        grid_names = {4: "(2×2 Grid)", 9: "(3×3 Grid)", 16: "(4×4 Grid)"}
        self.grid_label.setText(grid_names.get(count, ""))
        config.calibration_point_count = count
        config.save_config()
        self.pointCountChanged.emit(count)
        
    def get_count(self) -> int: return self._current
    def set_count(self, count: int):
        if count in self.buttons:
            self._current = count
            for c, btn in self.buttons.items():
                btn.blockSignals(True); btn.setChecked(c == count); btn.blockSignals(False)
            grid_names = {4: "(2×2 Grid)", 9: "(3×3 Grid)", 16: "(4×4 Grid)"}
            self.grid_label.setText(grid_names.get(count, ""))
    def set_enabled(self, enabled: bool):
        for btn in self.buttons.values(): btn.setEnabled(enabled)


# ============================================================
#                    PROFILE SYSTEM
# ============================================================

@dataclass
class CalibrationData:
    margin_x_min: float = 100
    margin_x_max: float = 540
    margin_y_min: float = 100
    margin_y_max: float = 380
    captured_points: List[tuple] = field(default_factory=list)
    accuracy_score: float = 0.0
    camera_index: int = 0
    point_count: int = 4
    hologram_mode: bool = False
    hologram_theme: str = "cyan"


@dataclass
class CalibrationProfile:
    name: str
    description: str = ""
    calibration: CalibrationData = field(default_factory=CalibrationData)
    created_at: str = ""
    updated_at: str = ""
    use_count: int = 0
    is_favorite: bool = False
    icon: str = "👤"
    
    def __post_init__(self):
        if not self.created_at: self.created_at = datetime.now().isoformat()
        if not self.updated_at: self.updated_at = self.created_at
    
    @property
    def is_hologram(self) -> bool: return self.calibration.hologram_mode
    @property
    def display_name(self) -> str:
        hologram_badge = " ⬡" if self.is_hologram else ""
        return f"{self.icon} {self.name}{hologram_badge}"


class ProfileManager:
    ICONS = ["👤", "🪑", "🧍", "🤚", "✋", "📱", "🖥️", "🎮", "💼", "🏠", "⬡"]
    
    def __init__(self):
        self.profiles_dir = Path.home() / ".gesture_control" / "calibration_profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, CalibrationProfile] = {}
        self.active_profile: Optional[str] = None
        self._load_profiles()
        
    def _load_profiles(self):
        self.profiles.clear()
        for f in self.profiles_dir.glob("*.json"):
            if f.name.startswith("_"): continue
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    cal_dict = data.get('calibration', {})
                    cal_data = CalibrationData(
                        margin_x_min=cal_dict.get('margin_x_min', 100),
                        margin_x_max=cal_dict.get('margin_x_max', 540),
                        margin_y_min=cal_dict.get('margin_y_min', 100),
                        margin_y_max=cal_dict.get('margin_y_max', 380),
                        captured_points=[tuple(p) for p in cal_dict.get('captured_points', [])],
                        accuracy_score=cal_dict.get('accuracy_score', 0.0),
                        camera_index=cal_dict.get('camera_index', 0),
                        point_count=cal_dict.get('point_count', 4),
                        hologram_mode=cal_dict.get('hologram_mode', False),
                        hologram_theme=cal_dict.get('hologram_theme', 'cyan')
                    )
                    profile = CalibrationProfile(
                        name=data['name'], description=data.get('description', ''),
                        calibration=cal_data, created_at=data.get('created_at', ''),
                        updated_at=data.get('updated_at', ''), use_count=data.get('use_count', 0),
                        is_favorite=data.get('is_favorite', False), icon=data.get('icon', '👤')
                    )
                    self.profiles[profile.name] = profile
            except Exception as e:
                print(f"⚠️ Error loading profile {f}: {e}")
        
        active_file = self.profiles_dir / "_active.txt"
        if active_file.exists():
            name = active_file.read_text().strip()
            if name in self.profiles: self.active_profile = name
        
        hologram_count = sum(1 for p in self.profiles.values() if p.is_hologram)
        print(f"📂 Loaded {len(self.profiles)} profiles ({hologram_count} ⬡ hologram)")
                
    def save_profile(self, profile: CalibrationProfile) -> bool:
        profile.updated_at = datetime.now().isoformat()
        filename = profile.name.lower().replace(' ', '_') + ".json"
        filepath = self.profiles_dir / filename
        try:
            data = {
                'name': profile.name, 'description': profile.description,
                'calibration': asdict(profile.calibration),
                'created_at': profile.created_at, 'updated_at': profile.updated_at,
                'use_count': profile.use_count, 'is_favorite': profile.is_favorite, 'icon': profile.icon
            }
            with open(filepath, 'w') as f: json.dump(data, f, indent=2)
            self.profiles[profile.name] = profile
            return True
        except Exception as e:
            print(f"❌ Error saving profile: {e}")
            return False
            
    def create_profile(self, name: str, calibration: CalibrationData = None, 
                      icon: str = "👤", hologram_mode: bool = False) -> Optional[CalibrationProfile]:
        if not name: return None
        cal_data = calibration or CalibrationData()
        cal_data.hologram_mode = hologram_mode
        if hologram_mode and icon != "⬡": icon = "⬡"
        profile = CalibrationProfile(name=name, calibration=cal_data, icon=icon)
        return profile if self.save_profile(profile) else None
    
    def create_hologram_profile(self, name: str, theme: str = "cyan") -> Optional[CalibrationProfile]:
        cal_data = CalibrationData(hologram_mode=True, hologram_theme=theme)
        return self.create_profile(name, cal_data, "⬡", hologram_mode=True)
    
    def delete_profile(self, name: str) -> bool:
        if name not in self.profiles: return False
        filename = name.lower().replace(' ', '_') + ".json"
        filepath = self.profiles_dir / filename
        try:
            if filepath.exists(): filepath.unlink()
            del self.profiles[name]
            if self.active_profile == name: self.active_profile = None
            return True
        except: return False
    
    def set_active(self, name: str) -> bool:
        if name not in self.profiles: return False
        self.active_profile = name
        self.profiles[name].use_count += 1
        self.save_profile(self.profiles[name])
        (self.profiles_dir / "_active.txt").write_text(name)
        return True
    
    def get_active(self) -> Optional[CalibrationProfile]:
        if self.active_profile and self.active_profile in self.profiles:
            return self.profiles[self.active_profile]
        return None
    
    def get_all_profiles(self) -> List[CalibrationProfile]:
        return sorted(self.profiles.values(), key=lambda p: (-int(p.is_favorite), -p.use_count, p.name))
    
    def get_hologram_profiles(self) -> List[CalibrationProfile]:
        return [p for p in self.get_all_profiles() if p.is_hologram]
    
    def toggle_favorite(self, name: str) -> bool:
        if name in self.profiles:
            self.profiles[name].is_favorite = not self.profiles[name].is_favorite
            return self.save_profile(self.profiles[name])
        return False
    
    def toggle_hologram_mode(self, name: str) -> bool:
        if name in self.profiles:
            profile = self.profiles[name]
            profile.calibration.hologram_mode = not profile.calibration.hologram_mode
            profile.icon = "⬡" if profile.calibration.hologram_mode else "👤"
            return self.save_profile(profile)
        return False
    
    def export_profile(self, name: str, filepath: str) -> bool:
        if name not in self.profiles: return False
        try:
            profile = self.profiles[name]
            data = {'name': profile.name, 'calibration': asdict(profile.calibration),
                    'icon': profile.icon, 'exported_at': datetime.now().isoformat()}
            with open(filepath, 'w') as f: json.dump(data, f, indent=2)
            return True
        except: return False
    
    def import_profile(self, filepath: str) -> Optional[CalibrationProfile]:
        try:
            with open(filepath, 'r') as f: data = json.load(f)
            name = data.get('name', 'Imported')
            counter = 1
            while name in self.profiles:
                name = f"{data.get('name', 'Imported')} ({counter})"; counter += 1
            cal_dict = data.get('calibration', {})
            cal_data = CalibrationData(
                margin_x_min=cal_dict.get('margin_x_min', 100),
                margin_x_max=cal_dict.get('margin_x_max', 540),
                hologram_mode=cal_dict.get('hologram_mode', False),
                hologram_theme=cal_dict.get('hologram_theme', 'cyan')
            )
            return self.create_profile(name, cal_data, data.get('icon', '👤'))
        except: return None


class QuickProfileBar(QFrame):
    profileSelected = Signal(str)
    
    def __init__(self, profile_manager: ProfileManager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setFixedHeight(54)
        self.setObjectName("quickProfiles")
        self._build_ui()
        
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        
        label = QLabel("⚡ Quick Profiles:")
        label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(label)
        
        self.button_container = QHBoxLayout()
        self.button_container.setSpacing(8)
        layout.addLayout(self.button_container)
        layout.addStretch()
        self.refresh()
        
        self.setStyleSheet("""
            #quickProfiles {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06));
                border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px;
            }
        """)
        
    def refresh(self):
        while self.button_container.count():
            item = self.button_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        profiles = self.profile_manager.get_all_profiles()[:5]
        
        if not profiles:
            no_profiles = QLabel("No profiles saved")
            no_profiles.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px; background: transparent;")
            self.button_container.addWidget(no_profiles)
            return
        
        for profile in profiles:
            btn = QPushButton(profile.icon)
            tooltip = f"{profile.name} (Used {profile.use_count}x)"
            if profile.is_hologram: tooltip += " ⬡ HOLOGRAM"
            btn.setToolTip(tooltip)
            btn.setFixedSize(38, 38)
            btn.setCursor(Qt.PointingHandCursor)
            
            if profile.is_hologram:
                btn.setStyleSheet("""
                    QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 255, 255, 0.2), stop:1 rgba(0, 255, 255, 0.1));
                        border: 2px solid rgba(0, 255, 255, 0.5); border-radius: 19px; font-size: 16px; }
                    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 255, 255, 0.4), stop:1 rgba(0, 255, 255, 0.2)); border-color: rgba(0, 255, 255, 0.9); }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.1), stop:1 rgba(255, 255, 255, 0.05));
                        border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 19px; font-size: 16px; }
                    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 212, 255, 0.25), stop:1 rgba(0, 212, 255, 0.15)); border-color: rgba(0, 212, 255, 0.6); }
                """)
            btn.clicked.connect(lambda _, n=profile.name: self.profileSelected.emit(n))
            self.button_container.addWidget(btn)


class ModernProfileDialog(QDialog):
    profileSelected = Signal(str)
    
    def __init__(self, profile_manager: ProfileManager, parent=None):
        super().__init__(parent)
        self.pm = profile_manager
        self.setWindowTitle("⬡ Calibration Profiles")
        self.setFixedSize(450, 580)
        self.setModal(True)
        self._build_ui()
        self._load_profiles()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        title = QLabel("📁 Profiles")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        header.addWidget(title)
        header.addStretch()
        
        self.hologram_filter = QCheckBox("⬡ Only")
        self.hologram_filter.setStyleSheet("QCheckBox { color: #00ffff; font-size: 11px; }")
        self.hologram_filter.toggled.connect(self._load_profiles)
        header.addWidget(self.hologram_filter)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { background: rgba(255,255,255,0.08); border: none; border-radius: 14px; color: white; } QPushButton:hover { background: rgba(255, 85, 85, 0.5); }")
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search profiles...")
        self.search.textChanged.connect(self._filter)
        self.search.setStyleSheet("QLineEdit { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; padding: 10px 14px; font-size: 12px; } QLineEdit:focus { border-color: rgba(0, 212, 255, 0.4); }")
        layout.addWidget(self.search)
        
        self.profile_list = QListWidget()
        self.profile_list.itemDoubleClicked.connect(self._select)
        self.profile_list.setStyleSheet("QListWidget { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 6px; outline: none; } QListWidget::item { background: rgba(255,255,255,0.02); border: 1px solid transparent; border-radius: 6px; padding: 10px; margin: 2px 0; color: white; } QListWidget::item:hover { background: rgba(0,212,255,0.08); border-color: rgba(0,212,255,0.2); } QListWidget::item:selected { background: rgba(0,212,255,0.15); border-color: rgba(0,212,255,0.4); }")
        layout.addWidget(self.profile_list)
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        layout.addWidget(self.stats_label)
        
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(8)
        
        new_btn = ModernButton("New", "➕", "glass", "small")
        new_btn.clicked.connect(self._create)
        btn_row1.addWidget(new_btn)
        
        new_holo_btn = ModernButton("New ⬡", "➕", "hologram", "small")
        new_holo_btn.clicked.connect(self._create_hologram)
        btn_row1.addWidget(new_holo_btn)
        
        del_btn = ModernButton("Delete", "🗑️", "ghost", "small")
        del_btn.clicked.connect(self._delete)
        btn_row1.addWidget(del_btn)
        
        fav_btn = ModernButton("Favorite", "⭐", "ghost", "small")
        fav_btn.clicked.connect(self._toggle_favorite)
        btn_row1.addWidget(fav_btn)
        layout.addLayout(btn_row1)
        
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(8)
        
        toggle_holo_btn = ModernButton("Toggle ⬡", "⬡", "ghost", "small")
        toggle_holo_btn.clicked.connect(self._toggle_hologram)
        btn_row2.addWidget(toggle_holo_btn)
        
        exp_btn = ModernButton("Export", "📤", "ghost", "small")
        exp_btn.clicked.connect(self._export)
        btn_row2.addWidget(exp_btn)
        
        imp_btn = ModernButton("Import", "📥", "ghost", "small")
        imp_btn.clicked.connect(self._import)
        btn_row2.addWidget(imp_btn)
        
        btn_row2.addStretch()
        
        select_btn = ModernButton("Select", "✓", "primary", "normal")
        select_btn.setMinimumWidth(100)
        select_btn.clicked.connect(self._select_current)
        btn_row2.addWidget(select_btn)
        layout.addLayout(btn_row2)
        
        self.setStyleSheet("QDialog { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f0f23); }")
        
    def _load_profiles(self):
        self.profile_list.clear()
        active = self.pm.active_profile
        profiles = self.pm.get_hologram_profiles() if self.hologram_filter.isChecked() else self.pm.get_all_profiles()
        
        hologram_count = len(self.pm.get_hologram_profiles())
        total = len(self.pm.profiles)
        self.stats_label.setText(f"Total: {total} | ⬡ Hologram: {hologram_count}")
        
        for p in profiles:
            fav_star = " ⭐" if p.is_favorite else ""
            active_badge = " ✓" if p.name == active else ""
            hologram_badge = " ⬡" if p.is_hologram else ""
            text = f"{p.icon}  {p.name}{hologram_badge}{fav_star}{active_badge}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, p.name)
            tooltip = f"Used: {p.use_count} times"
            if p.is_hologram: tooltip += f" | Theme: {p.calibration.hologram_theme}"
            item.setToolTip(tooltip)
            self.profile_list.addItem(item)
            
    def _filter(self, text):
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def _select(self, item):
        name = item.data(Qt.UserRole)
        self.profileSelected.emit(name)
        self.accept()
        
    def _select_current(self):
        item = self.profile_list.currentItem()
        if item: self._select(item)
            
    def _create(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Enter profile name:")
        if ok and name.strip():
            if self.pm.create_profile(name.strip()): self._load_profiles()
    
    def _create_hologram(self):
        name, ok = QInputDialog.getText(self, "New ⬡ Hologram Profile", "Enter profile name:")
        if ok and name.strip():
            themes = ["cyan", "purple", "green", "red", "orange", "pink"]
            theme, ok2 = QInputDialog.getItem(self, "Select Theme", "Hologram color theme:", themes, 0, False)
            if ok2:
                if self.pm.create_hologram_profile(name.strip(), theme): self._load_profiles()
                
    def _delete(self):
        item = self.profile_list.currentItem()
        if not item: return
        name = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete", f"Delete '{name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.pm.delete_profile(name): self._load_profiles()
                
    def _toggle_favorite(self):
        item = self.profile_list.currentItem()
        if item:
            self.pm.toggle_favorite(item.data(Qt.UserRole))
            self._load_profiles()
    
    def _toggle_hologram(self):
        item = self.profile_list.currentItem()
        if item:
            self.pm.toggle_hologram_mode(item.data(Qt.UserRole))
            self._load_profiles()
            
    def _export(self):
        item = self.profile_list.currentItem()
        if not item: return
        name = item.data(Qt.UserRole)
        path, _ = QFileDialog.getSaveFileName(self, "Export", f"{name}.json", "JSON (*.json)")
        if path and self.pm.export_profile(name, path):
            QMessageBox.information(self, "Success", "Profile exported!")
                
    def _import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json)")
        if path:
            profile = self.pm.import_profile(path)
            if profile: self._load_profiles()


# ============================================================
#                    HAND STATE & VISUALIZER
# ============================================================

class HandState(Enum):
    NOT_DETECTED = 0
    DETECTED = 1
    STABLE = 2
    CAPTURING = 3
    CAPTURED = 4


class ModernHandVisualizer:
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20), (5, 9), (9, 13), (13, 17)
    ]
    FINGERTIPS = [4, 8, 12, 16, 20]
    
    THEMES = {
        HandState.NOT_DETECTED: {'primary': (90, 90, 90), 'secondary': (60, 60, 60), 'accent': (120, 120, 120)},
        HandState.DETECTED: {'primary': (255, 180, 50), 'secondary': (200, 140, 30), 'accent': (255, 220, 100)},
        HandState.STABLE: {'primary': (0, 255, 170), 'secondary': (0, 200, 130), 'accent': (100, 255, 200)},
        HandState.CAPTURING: {'primary': (0, 200, 255), 'secondary': (0, 150, 200), 'accent': (100, 220, 255)},
        HandState.CAPTURED: {'primary': (0, 255, 100), 'secondary': (0, 200, 80), 'accent': (150, 255, 180)}
    }
    
    HOLOGRAM_THEMES = {
        HandState.NOT_DETECTED: {'primary': (128, 128, 128), 'secondary': (80, 80, 80), 'accent': (160, 160, 160)},
        HandState.DETECTED: {'primary': (255, 255, 0), 'secondary': (200, 200, 0), 'accent': (255, 255, 100)},
        HandState.STABLE: {'primary': (255, 255, 0), 'secondary': (200, 200, 0), 'accent': (255, 255, 150)},
        HandState.CAPTURING: {'primary': (255, 255, 0), 'secondary': (200, 200, 0), 'accent': (255, 255, 200)},
        HandState.CAPTURED: {'primary': (255, 255, 0), 'secondary': (200, 200, 0), 'accent': (255, 255, 255)}
    }
    
    def __init__(self):
        self.state = HandState.NOT_DETECTED
        self.stability_history = deque(maxlen=30)
        self.stability_threshold = 10
        self.last_position = None
        self.capture_flash = 0
        self.pulse_phase = 0
        self.trail_points = deque(maxlen=8)
        self.hologram_mode = False
        
    def set_hologram_mode(self, enabled: bool): self.hologram_mode = enabled
        
    def update_state(self, hand_detected: bool, finger_pos: tuple, 
                     is_capturing: bool = False, just_captured: bool = False):
        if not hand_detected:
            self.state = HandState.NOT_DETECTED
            self.stability_history.clear()
            self.last_position = None
            self.trail_points.clear()
            return
        
        if finger_pos: self.trail_points.append(finger_pos)
        
        if just_captured:
            self.state = HandState.CAPTURED
            self.capture_flash = 12
            return
            
        if is_capturing:
            self.state = HandState.CAPTURING
            return
        
        if finger_pos and self.last_position:
            dx = finger_pos[0] - self.last_position[0]
            dy = finger_pos[1] - self.last_position[1]
            movement = math.sqrt(dx*dx + dy*dy)
            self.stability_history.append(movement < self.stability_threshold)
            
            stable_count = sum(self.stability_history)
            if len(self.stability_history) >= 20 and stable_count >= 17:
                self.state = HandState.STABLE
            else:
                self.state = HandState.DETECTED
        else:
            self.state = HandState.DETECTED
            
        self.last_position = finger_pos
        if self.capture_flash > 0: self.capture_flash -= 1
    
    def get_stability_percentage(self) -> float:
        if not self.stability_history: return 0
        return (sum(self.stability_history) / len(self.stability_history)) * 100
    
    def get_state_name(self) -> str:
        names = {
            HandState.NOT_DETECTED: "No Hand", HandState.DETECTED: "Tracking",
            HandState.STABLE: "Stable ✓", HandState.CAPTURING: "Capturing...", HandState.CAPTURED: "Captured!"
        }
        return names.get(self.state, "Unknown")
    
    def draw_skeleton(self, frame, landmarks, cam_w: int, cam_h: int):
        if landmarks is None or len(landmarks) < 21: return frame
        
        theme = self.HOLOGRAM_THEMES[self.state] if self.hologram_mode else self.THEMES[self.state]
        
        if self.capture_flash > 0:
            overlay = frame.copy()
            alpha = self.capture_flash / 25
            cv2.rectangle(overlay, (0, 0), (cam_w, cam_h), theme['primary'], -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        points = [(int(lm.x * cam_w), int(lm.y * cam_h)) for lm in landmarks]
        
        if self.hologram_mode:
            overlay = frame.copy()
            for conn in self.HAND_CONNECTIONS:
                if conn[0] < len(points) and conn[1] < len(points):
                    cv2.line(overlay, points[conn[0]], points[conn[1]], theme['primary'], 12, cv2.LINE_AA)
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        
        overlay = frame.copy()
        for conn in self.HAND_CONNECTIONS:
            if conn[0] < len(points) and conn[1] < len(points):
                cv2.line(overlay, points[conn[0]], points[conn[1]], theme['primary'], 6, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
        
        for conn in self.HAND_CONNECTIONS:
            if conn[0] < len(points) and conn[1] < len(points):
                cv2.line(frame, points[conn[0]], points[conn[1]], theme['secondary'], 2, cv2.LINE_AA)
                cv2.line(frame, points[conn[0]], points[conn[1]], theme['primary'], 1, cv2.LINE_AA)
        
        for i, point in enumerate(points):
            if i == 8:
                self._draw_index_tip(frame, point, theme)
            elif i in self.FINGERTIPS:
                cv2.circle(frame, point, 6, theme['secondary'], -1, cv2.LINE_AA)
                cv2.circle(frame, point, 4, theme['primary'], -1, cv2.LINE_AA)
            elif i == 0:
                cv2.circle(frame, point, 8, theme['secondary'], -1, cv2.LINE_AA)
                cv2.circle(frame, point, 5, theme['primary'], -1, cv2.LINE_AA)
            else:
                cv2.circle(frame, point, 3, theme['primary'], -1, cv2.LINE_AA)
        
        return frame
    
    def _draw_index_tip(self, frame, pos: tuple, theme: dict):
        self.pulse_phase = (self.pulse_phase + 0.12) % (2 * math.pi)
        pulse = 2 + 2 * math.sin(self.pulse_phase)
        
        for i in range(3):
            size = int(14 + (i * 4) + pulse)
            overlay = frame.copy()
            cv2.circle(overlay, pos, size, theme['primary'], -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
        
        cv2.circle(frame, pos, 10, theme['secondary'], -1, cv2.LINE_AA)
        cv2.circle(frame, pos, 8, theme['primary'], -1, cv2.LINE_AA)
        cv2.circle(frame, pos, 5, theme['accent'], -1, cv2.LINE_AA)
        cv2.circle(frame, pos, 2, (255, 255, 255), -1, cv2.LINE_AA)
    
    def draw_status_bar(self, frame, pos: tuple = (10, 10), width: int = 180):
        stability = self.get_stability_percentage()
        theme = self.HOLOGRAM_THEMES[self.state] if self.hologram_mode else self.THEMES[self.state]
        
        overlay = frame.copy()
        cv2.rectangle(overlay, pos, (pos[0] + width + 16, pos[1] + 42), (10, 10, 20), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        cv2.rectangle(frame, pos, (pos[0] + width + 16, pos[1] + 42), (40, 40, 60), 1, cv2.LINE_AA)
        
        status_text = ("⬡ " if self.hologram_mode else "") + self.get_state_name()
        cv2.putText(frame, status_text, (pos[0] + 8, pos[1] + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, theme['primary'], 1, cv2.LINE_AA)
        
        bar_pos = (pos[0] + 8, pos[1] + 24)
        cv2.rectangle(frame, bar_pos, (bar_pos[0] + width, bar_pos[1] + 5), (30, 30, 40), -1, cv2.LINE_AA)
        
        fill_width = int(width * (stability / 100))
        if fill_width > 0:
            cv2.rectangle(frame, bar_pos, (bar_pos[0] + fill_width, bar_pos[1] + 5), theme['primary'], -1, cv2.LINE_AA)
        
        cv2.putText(frame, f"{int(stability)}%", (pos[0] + width - 20, pos[1] + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (150, 150, 150), 1, cv2.LINE_AA)
        
        return frame
    
    def reset(self):
        self.state = HandState.NOT_DETECTED
        self.stability_history.clear()
        self.last_position = None
        self.capture_flash = 0
        self.trail_points.clear()


# ============================================================
#                    AUTO CAPTURE SYSTEM
# ============================================================

class CaptureMode(Enum):
    MANUAL = "manual"
    STABILITY = "stability"
    COUNTDOWN = "countdown"


@dataclass
class CaptureConfig:
    mode: CaptureMode = CaptureMode.COUNTDOWN
    stability_required: float = 90.0
    countdown_seconds: int = 3
    hold_time: float = 1.5
    target_tolerance: float = 60.0


class AutoCaptureSystem:
    def __init__(self, config: CaptureConfig = None):
        self.config = config or CaptureConfig()
        self.countdown_active = False
        self.countdown_start = 0.0
        self.countdown_value = 0
        self.stable_start_time = None
        self.last_capture_time = 0.0
        self.capture_cooldown = 0.8
        self.on_capture: Optional[Callable] = None
        self.on_countdown_tick: Optional[Callable[[int], None]] = None
        
    def set_mode(self, mode: CaptureMode): self.config.mode = mode; self.reset()
    def reset(self):
        self.countdown_active = False
        self.countdown_start = 0.0
        self.countdown_value = 0
        self.stable_start_time = None
        
    def update(self, stability: float, hand_detected: bool, 
               finger_pos: tuple = None, target_pos: tuple = None) -> dict:
        now = time.time()
        result = {'should_capture': False, 'countdown': None, 'progress': 0.0, 'status': 'waiting', 'in_zone': False}
        
        if now - self.last_capture_time < self.capture_cooldown:
            result['status'] = 'cooldown'; return result
        
        if not hand_detected:
            self.reset(); result['status'] = 'no_hand'; return result
        
        in_zone = False
        if finger_pos and target_pos:
            dist = math.sqrt((finger_pos[0] - target_pos[0])**2 + (finger_pos[1] - target_pos[1])**2)
            in_zone = dist < self.config.target_tolerance
        result['in_zone'] = in_zone
        
        if not in_zone:
            self.reset(); result['status'] = 'move'; return result
        
        if self.config.mode == CaptureMode.MANUAL:
            result['status'] = 'ready'; result['progress'] = stability
            
        elif self.config.mode == CaptureMode.STABILITY:
            if stability >= self.config.stability_required:
                if self.stable_start_time is None: self.stable_start_time = now
                elapsed = now - self.stable_start_time
                result['progress'] = min(100, (elapsed / self.config.hold_time) * 100)
                result['status'] = 'holding'
                if elapsed >= self.config.hold_time: result['should_capture'] = True
            else:
                self.stable_start_time = None
                result['status'] = 'stabilizing'; result['progress'] = stability
                
        elif self.config.mode == CaptureMode.COUNTDOWN:
            if stability >= self.config.stability_required:
                if not self.countdown_active:
                    self.countdown_active = True
                    self.countdown_start = now
                    self.countdown_value = self.config.countdown_seconds
                    if self.on_countdown_tick: self.on_countdown_tick(self.countdown_value)
                
                elapsed = now - self.countdown_start
                remaining = self.config.countdown_seconds - elapsed
                
                if remaining <= 0:
                    result['should_capture'] = True
                    result['countdown'] = 0; result['progress'] = 100
                else:
                    new_val = int(math.ceil(remaining))
                    if new_val != self.countdown_value:
                        self.countdown_value = new_val
                        if self.on_countdown_tick: self.on_countdown_tick(new_val)
                    result['countdown'] = new_val
                    result['progress'] = ((self.config.countdown_seconds - remaining) / self.config.countdown_seconds) * 100
                    result['status'] = 'countdown'
            else:
                self.countdown_active = False
                result['status'] = 'stabilizing'; result['progress'] = stability
        
        if result['should_capture']:
            self.last_capture_time = now; self.reset()
            if self.on_capture: self.on_capture()
                
        return result
    
    def force_capture(self):
        self.last_capture_time = time.time(); self.reset()
        if self.on_capture: self.on_capture()


# ============================================================
#                    AUDIO MANAGER
# ============================================================

class AudioManager:
    def __init__(self):
        self.sounds_dir = Path.home() / ".gesture_control" / "sounds"
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = config.calibration_sound_enabled
        self.volume = config.calibration_volume / 100.0
        self.sounds = {}
        if AUDIO_AVAILABLE: self._generate_sounds()
            
    def _generate_sounds(self):
        import wave
        import struct
        
        sound_defs = {
            'countdown_3': (440, 0.12), 'countdown_2': (523, 0.12), 'countdown_1': (659, 0.12),
            'capture': (880, 0.15), 'success': (1046, 0.25), 'error': (220, 0.2),
            'complete': (1318, 0.35), 'ready': (600, 0.1),
            'hologram_on': (800, 0.2), 'hologram_off': (400, 0.15)
        }
        
        for name, (freq, dur) in sound_defs.items():
            filepath = self.sounds_dir / f"{name}.wav"
            if not filepath.exists():
                try:
                    samples = []
                    num = int(44100 * dur)
                    for i in range(num):
                        fade = min(1.0, min(i, num - i) / 440)
                        val = int(32767 * fade * math.sin(2 * math.pi * freq * i / 44100) * 0.7)
                        samples.append(struct.pack('<h', max(-32767, min(32767, val))))
                    with wave.open(str(filepath), 'w') as wf:
                        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100)
                        wf.writeframes(b''.join(samples))
                except: pass
            
            if filepath.exists():
                try:
                    sound = pygame.mixer.Sound(str(filepath))
                    sound.set_volume(self.volume)
                    self.sounds[name] = sound
                except: pass
                    
    def play(self, name: str):
        if self.enabled and AUDIO_AVAILABLE and name in self.sounds:
            try: threading.Thread(target=lambda: self.sounds[name].play(), daemon=True).start()
            except: pass
                
    def play_countdown(self, num: int):
        if 1 <= num <= 3: self.play(f'countdown_{num}')
            
    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        for sound in self.sounds.values():
            try: sound.set_volume(self.volume)
            except: pass
    
    def reload_from_config(self):
        self.enabled = config.calibration_sound_enabled
        self.set_volume(config.calibration_volume / 100.0)


# ============================================================
#                    OVERLAY WIDGETS
# ============================================================

class SuccessNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        self._visible = False
        self.setFixedSize(480, 180)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hologram_mode = False
        
        self._fade_in = QPropertyAnimation(self, b"opacity")
        self._fade_in.setDuration(500); self._fade_in.setStartValue(0.0); self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        self._fade_out = QPropertyAnimation(self, b"opacity")
        self._fade_out.setDuration(400); self._fade_out.setStartValue(1.0); self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)
        self._fade_out.finished.connect(lambda: self.hide())
        
        self._pulse_value = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._animate_pulse)
        
    def get_opacity(self): return self._opacity
    def set_opacity(self, value): self._opacity = value; self.update()
    opacity = Property(float, get_opacity, set_opacity)
    
    def set_hologram_mode(self, enabled: bool): self.hologram_mode = enabled
    def _animate_pulse(self): self._pulse_value = (self._pulse_value + 0.08) % (2 * math.pi); self.update()
    
    def show_notification(self, duration_ms: int = 3500):
        self._visible = True; self.show(); self.raise_()
        self._pulse_timer.start(50); self._fade_in.start()
        QTimer.singleShot(duration_ms, self._start_fade_out)
    
    def _start_fade_out(self): self._pulse_timer.stop(); self._fade_out.start()
    
    def paintEvent(self, event):
        if self._opacity <= 0: return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)
        
        rect = self.rect().adjusted(10, 10, -10, -10)
        center = rect.center()
        pulse = 6 + 4 * math.sin(self._pulse_value)
        
        main_color = QColor(0, 255, 255) if self.hologram_mode else QColor(0, 255, 136)
        accent_color = QColor(0, 200, 200) if self.hologram_mode else QColor(0, 200, 100)
        
        for i in range(4):
            glow_rect = rect.adjusted(-i*5 - int(pulse), -i*5 - int(pulse), i*5 + int(pulse), i*5 + int(pulse))
            gradient = QRadialGradient(center, 250 + i * 15)
            gradient.setColorAt(0, QColor(main_color.red(), main_color.green(), main_color.blue(), int(25 - i * 5)))
            gradient.setColorAt(1, QColor(main_color.red(), main_color.green(), main_color.blue(), 0))
            painter.setBrush(gradient); painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(glow_rect, 22, 22)
        
        bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg_gradient.setColorAt(0, QColor(main_color.red(), main_color.green(), main_color.blue(), 245))
        bg_gradient.setColorAt(1, QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 245))
        painter.setBrush(bg_gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
        painter.drawRoundedRect(rect, 18, 18)
        
        icon_x, icon_y = rect.center().x(), rect.top() + 55
        painter.setBrush(QColor(255, 255, 255, 40))
        painter.setPen(QPen(QColor(255, 255, 255, 180), 3))
        painter.drawEllipse(QPoint(icon_x, icon_y), 32, 32)
        
        painter.setPen(QPen(QColor(255, 255, 255), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if self.hologram_mode:
            painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
            painter.drawText(QRect(icon_x - 20, icon_y - 15, 40, 30), Qt.AlignCenter, "⬡")
        else:
            painter.drawLine(QPoint(icon_x - 16, icon_y), QPoint(icon_x - 5, icon_y + 12))
            painter.drawLine(QPoint(icon_x - 5, icon_y + 12), QPoint(icon_x + 16, icon_y - 12))
        
        title = "⬡ Calibration Complete!" if self.hologram_mode else "Calibration Complete!"
        painter.setFont(QFont("Segoe UI", 20, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRect(rect.left(), icon_y + 45, rect.width(), 35), Qt.AlignCenter, title)
        
        subtitle = "⬡ Hologram mode calibrated • Ready!" if self.hologram_mode else "✓ Environment calibrated • Good to go!"
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawText(QRect(rect.left(), icon_y + 78, rect.width(), 28), Qt.AlignCenter, subtitle)
        
    def cleanup(self): self._pulse_timer.stop()


class ZoomControlButton(QPushButton):
    zoomChanged = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoomed_out = False
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._toggle_zoom)
        self._update_style()
        self.raise_()
        
    def _toggle_zoom(self):
        self.zoomed_out = not self.zoomed_out
        self._update_style()
        self.zoomChanged.emit(self.zoomed_out)
        
    def _update_style(self):
        if self.zoomed_out:
            icon, bg_color, border_color = "🔍−", "rgba(0, 212, 255, 0.85)", "rgba(0, 212, 255, 1)"
            tooltip = "Zoom In (Normal View)"
        else:
            icon, bg_color, border_color = "🔍+", "rgba(255, 255, 255, 0.12)", "rgba(255, 255, 255, 0.25)"
            tooltip = "Zoom Out (Wider View)"
        
        self.setText(icon); self.setToolTip(tooltip)
        self.setStyleSheet(f"QPushButton {{ background: {bg_color}; border: 2px solid {border_color}; border-radius: 22px; color: white; font-size: 16px; font-weight: bold; }} QPushButton:hover {{ background: rgba(0, 212, 255, 1); border-color: white; }}")
    
    def reset_zoom(self):
        if self.zoomed_out: self.zoomed_out = False; self._update_style(); self.zoomChanged.emit(False)
    
    def set_zoom_out(self):
        if not self.zoomed_out: self.zoomed_out = True; self._update_style(); self.zoomChanged.emit(True)
    
    def update_position(self):
        if self.parent():
            parent_width = self.parent().width()
            self.move(parent_width - self.width() - 10, 10)
            self.raise_()


class ModernCountdownOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.number = 0
        self._visible = False
        self.setFixedSize(140, 140)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.progress = 0.0
        self.hologram_mode = False
        
    def set_hologram_mode(self, enabled: bool): self.hologram_mode = enabled
    def set_number(self, num: int, progress: float = 0):
        self.number = num; self.progress = progress; self._visible = num > 0; self.update()
        
    def update_position(self):
        if self.parent():
            self.move((self.parent().width() - self.width()) // 2, (self.parent().height() - self.height()) // 2)
        
    def paintEvent(self, event):
        if not self._visible: return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        
        main_color = QColor(0, 255, 255) if self.hologram_mode else QColor(0, 212, 255)
        bg_color = QColor(0, 50, 50, 220) if self.hologram_mode else QColor(15, 15, 30, 220)
        
        gradient = QRadialGradient(center, 56)
        gradient.setColorAt(0, bg_color); gradient.setColorAt(1, QColor(8, 8, 20, 220))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(main_color.red(), main_color.green(), main_color.blue(), 40), 2))
        painter.drawEllipse(center, 56, 56)
        
        painter.setPen(QPen(main_color, 4, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        span = int(-self.progress * 3.6 * 16)
        painter.drawArc(center.x() - 52, center.y() - 52, 104, 104, 90 * 16, span)
        
        painter.setFont(QFont("SF Pro Display", 48, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignCenter, str(self.number))


class GlassLiveStatsWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassLiveStats")
        self.hologram_mode = False
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0); layout.setContentsMargins(0, 0, 0, 0)
        
        header = QFrame()
        header.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 212, 255, 0.15), stop:1 rgba(0, 180, 220, 0.08)); border-top-left-radius: 14px; border-top-right-radius: 14px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        self.title_label = QLabel("📊 Live Stats")
        self.title_label.setStyleSheet("color: white; font-size: 13px; font-weight: 600; background: transparent;")
        header_layout.addWidget(self.title_label)
        layout.addWidget(header)
        
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: transparent;")
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setContentsMargins(14, 12, 14, 14); stats_layout.setSpacing(8)
        
        stats = [("🎬", "FPS", "fps"), ("👁️", "Detection", "detection"), ("🎯", "Stability", "stability"),
                 ("⭐", "Quality", "quality"), ("📍", "Points", "points"), ("⏱️", "Time", "time")]
        
        self.values = {}
        for i, (icon, label, key) in enumerate(stats):
            lbl = QLabel(f"{icon} {label}")
            lbl.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px; background: transparent;")
            stats_layout.addWidget(lbl, i, 0)
            val = QLabel("--")
            val.setStyleSheet("color: #00d4ff; font-weight: 600; font-size: 12px; background: transparent;")
            val.setAlignment(Qt.AlignRight)
            stats_layout.addWidget(val, i, 1)
            self.values[key] = val
        layout.addWidget(stats_widget)
        
        self.setStyleSheet("#glassLiveStats { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06)); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; }")
    
    def set_hologram_mode(self, enabled: bool):
        self.hologram_mode = enabled
        color = "#00ffff" if enabled else "#00d4ff"
        self.title_label.setText("⬡ Live Stats" if enabled else "📊 Live Stats")
        for val in self.values.values():
            val.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 12px; background: transparent;")
        
    def update_stats(self, fps, detection, stability, quality, points, total, duration):
        self.values["fps"].setText(f"{fps:.0f}")
        self.values["detection"].setText(f"{detection:.0f}%")
        self.values["stability"].setText(f"{stability:.0f}%")
        self.values["quality"].setText(quality)
        self.values["points"].setText(f"{points}/{total}")
        self.values["time"].setText(f"{int(duration//60)}:{int(duration%60):02d}")


class SettingsInfoCard(QFrame):
    openPreferencesClicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInfoCard")
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14); layout.setSpacing(8)
        
        header = QLabel("⚙️ Active Settings")
        header.setStyleSheet("color: white; font-weight: 600; font-size: 13px; background: transparent;")
        layout.addWidget(header)
        
        divider = QFrame(); divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255,255,255,0.1);")
        layout.addWidget(divider)
        
        self.mode_label = QLabel(f"Mode: {self._get_mode_name()}")
        self.stability_label = QLabel(f"Stability: {config.calibration_stability_threshold}%")
        self.countdown_label = QLabel(f"Countdown: {config.calibration_countdown_seconds}s")
        self.sound_label = QLabel(f"Sound: {'ON' if config.calibration_sound_enabled else 'OFF'}")
        self.volume_label = QLabel(f"Volume: {config.calibration_volume}%")
        self.points_label = QLabel(f"Points: {config.calibration_point_count}")
        self.hologram_label = QLabel("⬡ Hologram: OFF")
        
        for lbl in [self.mode_label, self.stability_label, self.countdown_label, 
                    self.sound_label, self.volume_label, self.points_label, self.hologram_label]:
            lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px; background: transparent;")
            layout.addWidget(lbl)
        
        layout.addSpacing(10)
        prefs_btn = ModernButton("Open Preferences", "⚙️", "primary", "small")
        prefs_btn.clicked.connect(self.openPreferencesClicked.emit)
        layout.addWidget(prefs_btn)
        layout.addStretch()
        
        self.setStyleSheet("#settingsInfoCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06)); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; }")
    
    def _get_mode_name(self) -> str:
        return {0: "Manual", 1: "Hold Stable", 2: "Countdown"}.get(config.calibration_capture_mode, "Unknown")
    
    def refresh(self, hologram_enabled: bool = False):
        self.mode_label.setText(f"Mode: {self._get_mode_name()}")
        self.stability_label.setText(f"Stability: {config.calibration_stability_threshold}%")
        self.countdown_label.setText(f"Countdown: {config.calibration_countdown_seconds}s")
        self.sound_label.setText(f"Sound: {'ON' if config.calibration_sound_enabled else 'OFF'}")
        self.volume_label.setText(f"Volume: {config.calibration_volume}%")
        self.points_label.setText(f"Points: {config.calibration_point_count}")
        
        if hologram_enabled:
            self.hologram_label.setText("⬡ Hologram: ON")
            self.hologram_label.setStyleSheet("color: #00ffff; font-size: 11px; background: transparent; font-weight: 600;")
        else:
            self.hologram_label.setText("⬡ Hologram: OFF")
            self.hologram_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px; background: transparent;")


class QuickSettingsCard(QFrame):
    settingsChanged = Signal()
    hologramModeChanged = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickSettingsCard")
        self.current_theme = "cyan"
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14); layout.setSpacing(10)
        
        header = QLabel("⚡ Quick Settings")
        header.setStyleSheet("color: white; font-weight: 600; font-size: 13px; background: transparent;")
        layout.addWidget(header)
        
        divider = QFrame(); divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255,255,255,0.1);")
        layout.addWidget(divider)
        
        # Hologram toggle
        hologram_container = QFrame()
        hologram_container.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 255, 0.1), stop:1 rgba(0, 200, 200, 0.05)); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 10px; }")
        hologram_layout = QHBoxLayout(hologram_container)
        hologram_layout.setContentsMargins(10, 8, 10, 8)
        hologram_label = QLabel("⬡ Hologram Mode")
        hologram_label.setStyleSheet("color: #00ffff; font-size: 12px; font-weight: 600; background: transparent;")
        hologram_layout.addWidget(hologram_label)
        hologram_layout.addStretch()
        self.hologram_toggle = HologramToggle(False)
        self.hologram_toggle.toggled.connect(self._on_hologram_toggled)
        hologram_layout.addWidget(self.hologram_toggle)
        layout.addWidget(hologram_container)
        
        # Theme selector
        self.theme_container = QWidget(); self.theme_container.setVisible(False)
        theme_layout = QHBoxLayout(self.theme_container)
        theme_layout.setContentsMargins(0, 4, 0, 4); theme_layout.setSpacing(6)
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px; background: transparent;")
        theme_layout.addWidget(theme_label)
        
        self.theme_buttons = {}
        for theme_name, color in [("cyan", "#00FFFF"), ("purple", "#FF00FF"), ("green", "#00FF00"), ("red", "#FF5050"), ("orange", "#FFA500")]:
            btn = QPushButton(); btn.setFixedSize(24, 24); btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(theme_name.title())
            btn.setStyleSheet(f"QPushButton {{ background: {color}; border: 2px solid rgba(255,255,255,0.3); border-radius: 12px; }} QPushButton:hover {{ border-color: white; }}")
            btn.clicked.connect(lambda _, t=theme_name: self._on_theme_selected(t))
            self.theme_buttons[theme_name] = btn
            theme_layout.addWidget(btn)
        theme_layout.addStretch()
        layout.addWidget(self.theme_container)
        
        # Other toggles
        for label_text, toggle_name, config_attr in [("🔊 Sound Effects", "sound_toggle", "calibration_sound_enabled"),
                                                      ("📐 Show Grid", "grid_toggle", "calibration_show_grid"),
                                                      ("🦴 Show Skeleton", "skeleton_toggle", "calibration_show_skeleton")]:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;")
            row.addWidget(lbl); row.addStretch()
            toggle = ModernToggle(getattr(config, config_attr))
            toggle.toggled.connect(lambda checked, attr=config_attr: self._on_toggle_changed(attr, checked))
            setattr(self, toggle_name, toggle)
            row.addWidget(toggle)
            layout.addLayout(row)
        
        # Volume
        layout.addSpacing(6)
        vol_label = QLabel("🔉 Volume")
        vol_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;")
        layout.addWidget(vol_label)
        
        vol_row = QHBoxLayout(); vol_row.setSpacing(10)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100); self.volume_slider.setValue(config.calibration_volume)
        self.volume_slider.setFixedHeight(20)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_slider.setStyleSheet("QSlider::groove:horizontal { background: rgba(255, 255, 255, 0.1); height: 6px; border-radius: 3px; } QSlider::handle:horizontal { background: #00d4ff; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; } QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:1 #00ff88); border-radius: 3px; }")
        vol_row.addWidget(self.volume_slider)
        self.volume_value = QLabel(f"{config.calibration_volume}%")
        self.volume_value.setFixedWidth(40)
        self.volume_value.setStyleSheet("color: #00d4ff; font-size: 11px; font-weight: 600; background: transparent;")
        self.volume_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vol_row.addWidget(self.volume_value)
        layout.addLayout(vol_row)
        
        # Capture mode
        layout.addSpacing(6)
        mode_lbl = QLabel("📸 Capture Mode")
        mode_lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;")
        layout.addWidget(mode_lbl)
        
        mode_row = QHBoxLayout(); mode_row.setSpacing(6)
        self.mode_buttons = {}
        for icon, mode_id, tooltip in [("🖱️", 0, "Manual"), ("⏱️", 1, "Hold"), ("⏰", 2, "Count")]:
            btn = QPushButton(icon); btn.setFixedSize(50, 32)
            btn.setCheckable(True); btn.setChecked(config.calibration_capture_mode == mode_id)
            btn.setToolTip(tooltip); btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=mode_id: self._on_mode_changed(m))
            btn.setStyleSheet("QPushButton { background: rgba(255, 255, 255, 0.06); color: rgba(255, 255, 255, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; font-size: 14px; } QPushButton:hover { background: rgba(0, 212, 255, 0.12); border-color: rgba(0, 212, 255, 0.4); } QPushButton:checked { background: rgba(0, 212, 255, 0.25); border-color: rgba(0, 212, 255, 0.8); color: #00d4ff; }")
            self.mode_buttons[mode_id] = btn
            mode_row.addWidget(btn)
        mode_row.addStretch()
        layout.addLayout(mode_row)
        layout.addStretch()
        
        self.setStyleSheet("#quickSettingsCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06)); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; }")
    
    def _on_hologram_toggled(self, checked: bool):
        self.theme_container.setVisible(checked)
        self.hologramModeChanged.emit(checked)
        self.settingsChanged.emit()
    
    def _on_theme_selected(self, theme: str):
        self.current_theme = theme
        self.settingsChanged.emit()
    
    def _on_toggle_changed(self, attr: str, checked: bool):
        setattr(config, attr, checked); config.save_config()
        self.settingsChanged.emit()
        
    def _on_volume_changed(self, value: int):
        config.calibration_volume = value; config.save_config()
        self.volume_value.setText(f"{value}%")
        self.settingsChanged.emit()
        
    def _on_mode_changed(self, mode: int):
        config.calibration_capture_mode = mode; config.save_config()
        for m, btn in self.mode_buttons.items(): btn.setChecked(m == mode)
        self.settingsChanged.emit()
    
    def is_hologram_enabled(self) -> bool: return self.hologram_toggle.isChecked()
    def get_hologram_theme(self) -> str: return self.current_theme
    def get_hologram_config(self) -> HologramConfig:
        return HologramConfig(enabled=self.hologram_toggle.isChecked(), theme=self.current_theme, grid_enabled=self.grid_toggle.isChecked())
    
    def refresh(self):
        self.sound_toggle.setChecked(config.calibration_sound_enabled)
        self.grid_toggle.setChecked(config.calibration_show_grid)
        self.skeleton_toggle.setChecked(config.calibration_show_skeleton)
        self.volume_slider.setValue(config.calibration_volume)
        self.volume_value.setText(f"{config.calibration_volume}%")
        for m, btn in self.mode_buttons.items(): btn.setChecked(m == config.calibration_capture_mode)


# ============================================================
#                    MAIN CALIBRATION PAGE
# ============================================================

class CalibrationPage(QWidget):
    """
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║  ⬡ CALIBRATION PAGE V3.0 — HOLOGRAM EDITION ⬡                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    
    calibrationComplete = Signal()
    openPreferencesRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.step = 0
        self.captured_points = []
        self.calibration_active = False
        self.camera_running = False
        self.total_points = config.calibration_point_count
        self.targets = []
        self.target_names = []
        
        self.hologram_mode = False
        self.hologram_config = HologramConfig()
        self.hologram_renderer = HologramRenderer(self.hologram_config)
        
        self.display_width = CAMERA_WIDTH
        self.display_height = CAMERA_HEIGHT
        self.capture_width = CAPTURE_WIDTH
        self.capture_height = CAPTURE_HEIGHT
        
        self.zoom_scale = 1.0
        self.target_zoom = 1.0
        self.zoom_transition_speed = 0.15
        
        self.cap = None
        self.hands = None
        if MEDIAPIPE_AVAILABLE: self.mp_hands = mp.solutions.hands
        
        self.visualizer = ModernHandVisualizer()
        self.audio = AudioManager()
        
        self.auto_capture = AutoCaptureSystem(CaptureConfig(
            mode=self._get_capture_mode(),
            countdown_seconds=config.calibration_countdown_seconds,
            stability_required=config.calibration_stability_threshold,
            target_tolerance=70.0
        ))
        self.auto_capture.on_capture = self._on_auto_capture
        self.auto_capture.on_countdown_tick = self._on_countdown_tick
        
        self.profile_manager = ProfileManager()
        self.notification_manager = get_notification_manager()
        self.toast_manager = get_toast_manager()
        
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.session_start = None
        self.detection_samples = deque(maxlen=100)
        self.stability_samples = deque(maxlen=50)
        
        self._build_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
    
    def _get_capture_mode(self) -> CaptureMode:
        return [CaptureMode.MANUAL, CaptureMode.STABILITY, CaptureMode.COUNTDOWN][config.calibration_capture_mode]
    
    def _get_mode_name(self) -> str:
        return {0: "Manual", 1: "Hold Stable", 2: "Countdown"}.get(config.calibration_capture_mode, "Unknown")

    def _generate_targets(self, w: int, h: int, count: int) -> tuple:
        margin_top, margin_bottom = TARGET_MARGIN_TOP, TARGET_MARGIN_BOTTOM
        margin_left, margin_right = TARGET_MARGIN_LEFT, TARGET_MARGIN_RIGHT
        
        targets, names = [], []
        
        if count == 4:
            targets = [(margin_left, margin_top), (w - margin_right, margin_top),
                      (margin_left, h - margin_bottom), (w - margin_right, h - margin_bottom)]
            names = ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-LEFT", "BOTTOM-RIGHT"]
        elif count == 9:
            x_pos = [margin_left, w // 2, w - margin_right]
            y_pos = [margin_top, h // 2, h - margin_bottom]
            grid = [(0, 0, "TOP-LEFT"), (1, 0, "TOP-CENTER"), (2, 0, "TOP-RIGHT"),
                   (0, 1, "MID-LEFT"), (1, 1, "CENTER"), (2, 1, "MID-RIGHT"),
                   (0, 2, "BOT-LEFT"), (1, 2, "BOT-CENTER"), (2, 2, "BOT-RIGHT")]
            for xi, yi, name in grid:
                targets.append((x_pos[xi], y_pos[yi])); names.append(name)
        elif count == 16:
            uw = w - margin_left - margin_right
            uh = h - margin_top - margin_bottom
            for yi in range(4):
                for xi in range(4):
                    x = margin_left + int(xi * uw / 3)
                    y = margin_top + int(yi * uh / 3)
                    targets.append((x, y)); names.append(f"P{yi * 4 + xi + 1}")
        
        return targets, names

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { background: rgba(255, 255, 255, 0.03); width: 10px; border-radius: 5px; } QScrollBar::handle:vertical { background: rgba(0, 212, 255, 0.4); border-radius: 5px; min-height: 30px; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20); scroll_layout.setSpacing(20)
        
        # Left panel
        left_panel = QVBoxLayout(); left_panel.setSpacing(14)
        
        # Header
        header = QHBoxLayout()
        title_block = QVBoxLayout()
        self.page_title = QLabel("🎯 AI Calibration")
        self.page_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        title_block.addWidget(self.page_title)
        self.page_subtitle = QLabel("Point at the markers to calibrate your gesture control")
        self.page_subtitle.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 13px;")
        title_block.addWidget(self.page_subtitle)
        header.addLayout(title_block)
        header.addStretch()
        
        self.mode_label = QLabel(f"⏰ {self._get_mode_name()}")
        self.mode_label.setStyleSheet("color: #00d4ff; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 212, 255, 0.2), stop:1 rgba(0, 212, 255, 0.1)); padding: 8px 18px; border-radius: 18px; font-size: 12px; font-weight: 600; border: 1px solid rgba(0, 212, 255, 0.3);")
        header.addWidget(self.mode_label)
        
        self.cam_select = QComboBox()
        self.cam_select.addItems(["📷 Camera 0", "📷 Camera 1", "📷 Camera 2"])
        self.cam_select.setCurrentIndex(config.camera_index)
        self.cam_select.currentIndexChanged.connect(self._change_camera)
        self.cam_select.setFixedWidth(130)
        self.cam_select.setStyleSheet("QComboBox { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.1), stop:1 rgba(255, 255, 255, 0.05)); color: white; border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; padding: 10px 14px; font-size: 12px; } QComboBox:hover { border-color: rgba(0, 212, 255, 0.5); } QComboBox QAbstractItemView { background: #1a1a2e; color: white; selection-background-color: rgba(0, 212, 255, 0.3); }")
        header.addWidget(self.cam_select)
        left_panel.addLayout(header)
        
        # Camera preview
        self.main_card = GlassCard(self)
        card_layout = QVBoxLayout(self.main_card)
        card_layout.setSpacing(0); card_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_container = QWidget()
        preview_container.setStyleSheet("background: transparent;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        
        self.cam_preview = QLabel("📷 Click 'Start Calibration' to begin")
        self.cam_preview.setFixedSize(self.display_width, self.display_height)
        self.cam_preview.setAlignment(Qt.AlignCenter)
        self.cam_preview.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(8, 8, 26, 0.9), stop:1 rgba(18, 18, 42, 0.9)); border: 2px dashed rgba(0, 212, 255, 0.3); border-radius: 16px; color: rgba(255, 255, 255, 0.5); font-size: 16px;")
        preview_layout.addWidget(self.cam_preview, alignment=Qt.AlignCenter)
        
        # Overlays
        self.zoom_btn = ZoomControlButton(self.cam_preview)
        self.zoom_btn.zoomChanged.connect(self._on_zoom_changed)
        self.zoom_btn.hide()
        
        self.countdown_overlay = ModernCountdownOverlay(self.cam_preview)
        self.countdown_overlay.hide()
        
        self.success_notification = SuccessNotification(self.cam_preview)
        self.success_notification.hide()
        
        card_layout.addWidget(preview_container)
        left_panel.addWidget(self.main_card)
        
        # Controls
        self.point_selector = PointCountSelector()
        self.point_selector.pointCountChanged.connect(self._on_point_count_changed)
        left_panel.addWidget(self.point_selector)
        
        self.quick_profiles = QuickProfileBar(self.profile_manager)
        self.quick_profiles.profileSelected.connect(self._load_profile)
        left_panel.addWidget(self.quick_profiles)
        
        # Progress
        progress_card = QFrame()
        progress_card.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06)); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; }")
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(16, 14, 16, 16); progress_layout.setSpacing(12)
        
        progress_header = QHBoxLayout()
        progress_title = QLabel("📈 Calibration Progress")
        progress_title.setStyleSheet("color: white; font-weight: 600; font-size: 13px; background: transparent;")
        progress_header.addWidget(progress_title)
        self.progress_label = QLabel(f"0/{self.total_points} points captured")
        self.progress_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; background: transparent;")
        progress_header.addStretch()
        progress_header.addWidget(self.progress_label)
        progress_layout.addLayout(progress_header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total_points); self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False); self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; border-radius: 6px; background: rgba(255,255,255,0.1); } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:0.5 #00ff88, stop:1 #00d4ff); border-radius: 6px; }")
        progress_layout.addWidget(self.progress_bar)
        left_panel.addWidget(progress_card)
        
        # Instruction
        self.instruction = QLabel("Select the number of calibration points and click 'Start Calibration'")
        self.instruction.setAlignment(Qt.AlignCenter); self.instruction.setWordWrap(True)
        self.instruction.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; padding: 18px 24px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 212, 255, 0.1), stop:1 rgba(0, 212, 255, 0.05)); border-radius: 14px; border: 1px solid rgba(0, 212, 255, 0.2);")
        left_panel.addWidget(self.instruction)
        
        # Buttons
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12)
        
        self.profile_btn = ModernButton("Profiles", "📁", "glass", "normal")
        self.profile_btn.clicked.connect(self._show_profile_dialog)
        btn_layout.addWidget(self.profile_btn)
        
        self.action_btn = ModernButton("Start Calibration", "🎯", "primary", "large")
        self.action_btn.setMinimumWidth(200)
        self.action_btn.clicked.connect(self._start_calibration)
        btn_layout.addWidget(self.action_btn)
        
        self.capture_btn = ModernButton("Capture Point", "📍", "success", "normal")
        self.capture_btn.clicked.connect(self._manual_capture)
        self.capture_btn.setVisible(False)
        btn_layout.addWidget(self.capture_btn)
        
        self.stop_btn = ModernButton("Stop", "⏹", "danger", "normal")
        self.stop_btn.clicked.connect(self._stop_calibration)
        self.stop_btn.setVisible(False)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        
        self.dashboard_btn = ModernButton("Return to Dashboard", "🏠", "primary", "large")
        self.dashboard_btn.setMinimumWidth(200)
        self.dashboard_btn.clicked.connect(self._return_to_dashboard)
        self.dashboard_btn.setVisible(False)
        btn_layout.addWidget(self.dashboard_btn)
        
        left_panel.addLayout(btn_layout)
        left_panel.addStretch()
        
        scroll_layout.addLayout(left_panel, stretch=4)
        
        # Right panel
        right_panel = QVBoxLayout(); right_panel.setSpacing(16)
        
        self.live_stats = GlassLiveStatsWidget()
        self.live_stats.setFixedWidth(270)
        right_panel.addWidget(self.live_stats)
        
        profile_card = QFrame()
        profile_card.setFixedWidth(270)
        profile_card.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.08), stop:0.5 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.06)); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; }")
        profile_card_layout = QVBoxLayout(profile_card)
        profile_card_layout.setContentsMargins(16, 14, 16, 14)
        
        profile_header = QLabel("👤 Active Profile")
        profile_header.setStyleSheet("color: white; font-weight: 600; font-size: 13px; background: transparent;")
        profile_card_layout.addWidget(profile_header)
        
        self.profile_label = QLabel("No profile active")
        self.profile_label.setWordWrap(True)
        self.profile_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 6px; background: transparent;")
        profile_card_layout.addWidget(self.profile_label)
        right_panel.addWidget(profile_card)
        
        self.settings_info = SettingsInfoCard()
        self.settings_info.setFixedWidth(270)
        self.settings_info.openPreferencesClicked.connect(self._open_preferences)
        right_panel.addWidget(self.settings_info)
        
        self.quick_settings = QuickSettingsCard()
        self.quick_settings.setFixedWidth(270)
        self.quick_settings.settingsChanged.connect(self._on_quick_settings_changed)
        self.quick_settings.hologramModeChanged.connect(self._on_hologram_mode_changed)
        right_panel.addWidget(self.quick_settings)
        
        right_panel.addStretch()
        
        scroll_layout.addLayout(right_panel, stretch=1)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _on_point_count_changed(self, count: int):
        self.total_points = count
        self.progress_bar.setRange(0, count)
        self.progress_label.setText(f"0/{count} points captured")
        self.settings_info.refresh(self.hologram_mode)

    def _on_zoom_changed(self, zoomed_out: bool):
        self.target_zoom = 0.65 if zoomed_out else 1.0
        msg = "🔍 Zoomed out - More area visible" if zoomed_out else "🔍 Normal zoom restored"
        self.instruction.setText(msg)
        self.audio.play('ready')
    
    def _on_hologram_mode_changed(self, enabled: bool):
        self.hologram_mode = enabled
        self.hologram_config.enabled = enabled
        self.hologram_config.theme = self.quick_settings.get_hologram_theme()
        self.hologram_renderer.update_config(self.hologram_config)
        
        self.visualizer.set_hologram_mode(enabled)
        self.live_stats.set_hologram_mode(enabled)
        self.countdown_overlay.set_hologram_mode(enabled)
        self.success_notification.set_hologram_mode(enabled)
        self.settings_info.refresh(enabled)
        
        if enabled:
            self.page_title.setText("⬡ AI Calibration")
            self.page_subtitle.setText("HOLOGRAM MODE - Cyberpunk calibration interface")
            self.audio.play('hologram_on')
            self.notification_manager.add_info(title="⬡ Hologram Mode", message="Cyberpunk visual effects enabled", icon="⬡")
        else:
            self.page_title.setText("🎯 AI Calibration")
            self.page_subtitle.setText("Point at the markers to calibrate your gesture control")
            self.audio.play('hologram_off')
    
    def _on_quick_settings_changed(self):
        self.auto_capture.set_mode(self._get_capture_mode())
        mode_icons = {0: "🖱️", 1: "⏱️", 2: "⏰"}
        self.mode_label.setText(f"{mode_icons.get(config.calibration_capture_mode, '⏰')} {self._get_mode_name()}")
        self.audio.reload_from_config()
        self.settings_info.refresh(self.hologram_mode)
        
        self.hologram_config = self.quick_settings.get_hologram_config()
        self.hologram_renderer.update_config(self.hologram_config)

    def _update_overlay_positions(self):
        self.zoom_btn.update_position()
        self.countdown_overlay.update_position()
        if self.success_notification.isVisible():
            self.success_notification.move(
                (self.cam_preview.width() - self.success_notification.width()) // 2,
                (self.cam_preview.height() - self.success_notification.height()) // 2
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, self._update_overlay_positions)

    def _load_settings_from_config(self):
        self.auto_capture.set_mode(self._get_capture_mode())
        mode_icons = {0: "🖱️", 1: "⏱️", 2: "⏰"}
        self.mode_label.setText(f"{mode_icons.get(config.calibration_capture_mode, '⏰')} {self._get_mode_name()}")
        self.auto_capture.config.stability_required = config.calibration_stability_threshold
        self.auto_capture.config.countdown_seconds = config.calibration_countdown_seconds
        self.audio.reload_from_config()
        
        self.total_points = config.calibration_point_count
        self.point_selector.set_count(config.calibration_point_count)
        self.progress_bar.setRange(0, self.total_points)
        self.progress_label.setText(f"0/{self.total_points} points captured")
        
        self.settings_info.refresh(self.hologram_mode)
        self.quick_settings.refresh()

    def apply_config_changes(self):
        self.auto_capture.set_mode(self._get_capture_mode())
        self.auto_capture.config.stability_required = config.calibration_stability_threshold
        self.auto_capture.config.countdown_seconds = config.calibration_countdown_seconds
        self.audio.reload_from_config()
        
        mode_icons = {0: "🖱️", 1: "⏱️", 2: "⏰"}
        self.mode_label.setText(f"{mode_icons.get(config.calibration_capture_mode, '⏰')} {self._get_mode_name()}")
        
        if not self.calibration_active:
            self.total_points = config.calibration_point_count
            self.point_selector.set_count(config.calibration_point_count)
            self.progress_bar.setRange(0, self.total_points)
            self.progress_label.setText(f"0/{self.total_points} points captured")
        
        self.settings_info.refresh(self.hologram_mode)
        self.quick_settings.refresh()

    def _open_preferences(self):
        self.openPreferencesRequested.emit()

    def _start_camera(self):
        if self.camera_running: return True
        if self.cap is not None: self.cap.release()
        
        self.cap = cv2.VideoCapture(config.camera_index)
        if not self.cap.isOpened():
            self.instruction.setText(f"❌ Failed to open camera {config.camera_index}")
            self.notification_manager.add_error(title="Camera Error", message=f"Failed to open camera {config.camera_index}")
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if MEDIAPIPE_AVAILABLE and self.hands is None:
            self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                min_detection_confidence=0.7, min_tracking_confidence=0.7, model_complexity=0)
        
        self.timer.start(30)
        self.camera_running = True
        self.cam_preview.setStyleSheet("background: rgba(0, 0, 0, 0.5); border: 2px solid rgba(0, 212, 255, 0.5); border-radius: 16px;")
        return True

    def _stop_camera(self):
        self.timer.stop()
        if self.cap is not None: self.cap.release(); self.cap = None
        if self.hands: self.hands.close(); self.hands = None
        
        self.camera_running = False
        self.visualizer.reset()
        self.cam_preview.clear()
        self.cam_preview.setText("📷 Click 'Start Calibration' to begin")
        self.cam_preview.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(8, 8, 26, 0.9), stop:1 rgba(18, 18, 42, 0.9)); border: 2px dashed rgba(0, 212, 255, 0.3); border-radius: 16px; color: rgba(255, 255, 255, 0.5); font-size: 16px;")

    def _change_camera(self, index):
        config.camera_index = index
        config.save_config()
        if self.camera_running:
            self._stop_camera()
            time.sleep(0.2)
            self._start_camera()

    def _start_calibration(self):
        if not self._start_camera():
            return
        
        self.step = 1
        self.captured_points = []
        self.calibration_active = True
        self.session_start = time.time()
        self.detection_samples.clear()
        self.stability_samples.clear()
        
        self.targets, self.target_names = self._generate_targets(self.display_width, self.display_height, self.total_points)
        
        self.zoom_btn.show()
        self.zoom_btn.reset_zoom()
        QTimer.singleShot(100, self._update_overlay_positions)
        
        self.point_selector.set_enabled(False)
        self.profile_btn.setEnabled(False)
        self.action_btn.setVisible(False)
        self.capture_btn.setVisible(True)
        self.stop_btn.setVisible(True)
        self.dashboard_btn.setVisible(False)
        
        self.progress_bar.setRange(0, self.total_points)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"0/{self.total_points} points captured")
        
        mode_text = "⬡ HOLOGRAM MODE - " if self.hologram_mode else ""
        self.instruction.setText(f"{mode_text}📍 Point at {self.target_names[0]} and hold steady")
        self.audio.play('ready')
        
        self.notification_manager.add_info(
            title="Calibration Started",
            message=f"{'⬡ Hologram mode • ' if self.hologram_mode else ''}Calibrating with {self.total_points} points",
            icon="⬡" if self.hologram_mode else "🎯"
        )
        
        print(f"✅ Calibration started with {self.total_points} points {'[HOLOGRAM MODE]' if self.hologram_mode else ''}")
    
    def _stop_calibration(self):
        self._stop_camera()
        self._reset_ui()
        self.instruction.setText("❌ Calibration cancelled")
        self.notification_manager.add_warning(title="Calibration Cancelled", message="Calibration was cancelled before completion.")
    
    def _reset_ui(self):
        self.step = 0
        self.captured_points = []
        self.calibration_active = False
        self.auto_capture.reset()
        self.visualizer.reset()
        self.countdown_overlay.hide()
        self.zoom_btn.hide()
        self.zoom_btn.reset_zoom()
        
        self.progress_bar.setValue(0)
        self.point_selector.set_enabled(True)
        self.profile_btn.setEnabled(True)
        self.action_btn.setVisible(True)
        self.action_btn.setText("🎯 Start Calibration")
        self.capture_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.dashboard_btn.setVisible(False)

    def _show_profile_dialog(self):
        dialog = ModernProfileDialog(self.profile_manager, self)
        dialog.profileSelected.connect(self._load_profile)
        dialog.exec()
        self.quick_profiles.refresh()
        
    def _load_profile(self, name):
        if self.profile_manager.set_active(name):
            profile = self.profile_manager.get_active()
            if profile:
                config.margin_x_min = profile.calibration.margin_x_min
                config.margin_x_max = profile.calibration.margin_x_max
                config.margin_y_min = profile.calibration.margin_y_min
                config.margin_y_max = profile.calibration.margin_y_max
                config.save_config()
                
                # Apply hologram settings from profile
                if profile.is_hologram:
                    self.hologram_mode = True
                    self.hologram_config.enabled = True
                    self.hologram_config.theme = profile.calibration.hologram_theme
                    self.hologram_renderer.update_config(self.hologram_config)
                    self.visualizer.set_hologram_mode(True)
                    self.live_stats.set_hologram_mode(True)
                    self.quick_settings.hologram_toggle.setChecked(True)
                
                self.profile_label.setText(f"{profile.icon} {profile.name}\nUsed {profile.use_count}x")
                holo_badge = " ⬡" if profile.is_hologram else ""
                self.instruction.setText(f"✅ Loaded profile: {profile.name}{holo_badge}")
                self.audio.play('success')
                
                self.notification_manager.add_success(
                    title="Profile Loaded",
                    message=f"Calibration profile '{profile.name}' has been loaded.",
                    icon=profile.icon
                )

    def update_preview(self):
        if self.cap is None or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (self.display_width, self.display_height), interpolation=cv2.INTER_LINEAR)
        h, w = frame.shape[:2]
        
        # Smooth zoom transition
        if abs(self.zoom_scale - self.target_zoom) > 0.01:
            self.zoom_scale += (self.target_zoom - self.zoom_scale) * self.zoom_transition_speed
        else:
            self.zoom_scale = self.target_zoom
        
        # Apply zoom
        if self.zoom_scale < 0.99:
            new_w = int(w * self.zoom_scale)
            new_h = int(h * self.zoom_scale)
            zoomed = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            canvas = np.zeros((h, w, 3), dtype=np.uint8)
            x_offset = (w - new_w) // 2
            y_offset = (h - new_h) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = zoomed
            cv2.rectangle(canvas, (x_offset, y_offset), (x_offset + new_w, y_offset + new_h), (0, 212, 255), 2, cv2.LINE_AA)
            cv2.putText(canvas, f"Zoom: {int(self.zoom_scale * 100)}%", (w - 150, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 212, 255), 2, cv2.LINE_AA)
            frame = canvas
        
        # ⬡ Apply hologram effects BEFORE hand detection overlay
        if self.hologram_mode and self.hologram_config.enabled:
            frame = self.hologram_renderer.render(frame)
        
        # FPS calculation
        self.frame_count += 1
        now = time.time()
        if now - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = now
        
        # Hand detection
        hand_detected = False
        finger_pos = None
        finger_up = False
        landmarks = None
        
        if self.hands and MEDIAPIPE_AVAILABLE:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)
            
            if results.multi_hand_landmarks:
                hand_detected = True
                landmarks = results.multi_hand_landmarks[0].landmark
                index_tip = landmarks[8]
                index_base = landmarks[6]
                finger_up = index_tip.y < index_base.y
                finger_pos = (int(index_tip.x * w), int(index_tip.y * h))
        
        self.detection_samples.append(hand_detected)
        
        is_capturing = self.auto_capture.countdown_active
        self.visualizer.update_state(hand_detected, finger_pos, is_capturing)
        
        # Grid overlay (only if not using hologram grid)
        if config.calibration_show_grid and not (self.hologram_mode and self.hologram_config.grid_enabled):
            for x in range(0, w, 100):
                cv2.line(frame, (x, 0), (x, h), (25, 25, 35), 1, cv2.LINE_AA)
            for y in range(0, h, 100):
                cv2.line(frame, (0, y), (w, y), (25, 25, 35), 1, cv2.LINE_AA)
        
        # Skeleton
        if config.calibration_show_skeleton and landmarks:
            frame = self.visualizer.draw_skeleton(frame, landmarks, w, h)
        
        # Draw targets
        current_target = None
        if self.calibration_active and 1 <= self.step <= self.total_points:
            self.targets, self.target_names = self._generate_targets(w, h, self.total_points)
            
            for i, target in enumerate(self.targets):
                tx = max(30, min(target[0], w - 30))
                ty = max(30, min(target[1], h - 30))
                target = (tx, ty)
                
                if i < len(self.captured_points):
                    # Captured point
                    if self.hologram_mode:
                        cv2.circle(frame, target, 20, (255, 255, 0), -1, cv2.LINE_AA)
                        cv2.circle(frame, target, 20, (255, 255, 255), 2, cv2.LINE_AA)
                    else:
                        cv2.circle(frame, target, 20, (0, 255, 136), -1, cv2.LINE_AA)
                        cv2.circle(frame, target, 20, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(frame, str(i + 1), (target[0] - 6, target[1] + 6),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                elif i == self.step - 1:
                    # Current target
                    current_target = target
                    pulse = 3 + 3 * abs(math.sin(time.time() * 2.5))
                    
                    # Target color based on mode
                    if self.hologram_mode:
                        target_color = (255, 255, 0)  # Cyan in BGR
                    else:
                        target_color = (0, 212, 255)
                    
                    for j in range(3):
                        overlay = frame.copy()
                        cv2.circle(overlay, target, int(45 + j * 8 + pulse), target_color, -1)
                        cv2.addWeighted(overlay, 0.06, frame, 0.94, 0, frame)
                    
                    cv2.circle(frame, target, int(35 + pulse), target_color, 3, cv2.LINE_AA)
                    cv2.circle(frame, target, 20, target_color, -1, cv2.LINE_AA)
                    cv2.circle(frame, target, 8, (255, 255, 255), -1, cv2.LINE_AA)
                    
                    label_y = target[1] - 55 if target[1] > 80 else target[1] + 65
                    cv2.putText(frame, self.target_names[i], (target[0] - 50, label_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, target_color, 2, cv2.LINE_AA)
                else:
                    # Future target
                    cv2.circle(frame, target, 15, (60, 60, 80), -1, cv2.LINE_AA)
                    cv2.circle(frame, target, 15, (80, 80, 100), 1, cv2.LINE_AA)
            
            # Auto capture logic
            if hand_detected and finger_up and current_target:
                stability = self.visualizer.get_stability_percentage()
                self.stability_samples.append(stability)
                
                result = self.auto_capture.update(stability, True, finger_pos, current_target)
                
                if result['countdown'] and result['countdown'] > 0:
                    self.countdown_overlay.set_number(result['countdown'], result['progress'])
                    self.countdown_overlay.show()
                else:
                    self.countdown_overlay.hide()
            else:
                self.auto_capture.reset()
                self.countdown_overlay.hide()
        
        # Status bar
        frame = self.visualizer.draw_status_bar(frame, (w - 220, 10), 200)
        
        # FPS & Points overlay
        overlay_color = (255, 255, 0) if self.hologram_mode else (0, 255, 136)
        cv2.rectangle(frame, (10, 10), (130, 65), (10, 10, 20), -1)
        cv2.rectangle(frame, (10, 10), (130, 65), (40, 40, 55), 1)
        
        if self.hologram_mode:
            cv2.putText(frame, f"⬡ FPS: {self.fps}", (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, overlay_color, 1, cv2.LINE_AA)
        else:
            cv2.putText(frame, f"FPS: {self.fps}", (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5, overlay_color, 2, cv2.LINE_AA)
        
        cv2.putText(frame, f"Points: {len(self.captured_points)}/{self.total_points}", (18, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 212, 255), 1, cv2.LINE_AA)
        
        # Update live stats
        detection_rate = (sum(self.detection_samples) / max(1, len(self.detection_samples))) * 100
        avg_stability = sum(self.stability_samples) / max(1, len(self.stability_samples)) if self.stability_samples else 0
        
        quality = "Poor"
        if detection_rate >= 95 and avg_stability >= 90:
            quality = "Excellent ⭐"
        elif detection_rate >= 85 and avg_stability >= 75:
            quality = "Good"
        elif detection_rate >= 70:
            quality = "Fair"
        
        duration = time.time() - self.session_start if self.session_start else 0
        self.live_stats.update_stats(self.fps, detection_rate, avg_stability, quality, 
                                     len(self.captured_points), self.total_points, duration)
        
        self.progress_label.setText(f"{len(self.captured_points)}/{self.total_points} points captured")
        
        # Display frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(rgb_frame.data, w, h, w * 3, QImage.Format_RGB888)
        self.cam_preview.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.display_width, self.display_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def _on_auto_capture(self):
        self._capture_point()
        
    def _on_countdown_tick(self, num):
        self.audio.play_countdown(num)
        
    def _manual_capture(self):
        if self.visualizer.state != HandState.NOT_DETECTED:
            self.auto_capture.force_capture()
            self._capture_point()

    def _capture_point(self):
        if not self.visualizer.last_position:
            self.instruction.setText("⚠️ No hand detected! Try again.")
            self.audio.play('error')
            self.notification_manager.add_warning(title="Capture Failed", message="No hand detected. Please ensure your hand is visible.")
            return
        
        pos = self.visualizer.last_position
        self.captured_points.append(pos)
        self.progress_bar.setValue(len(self.captured_points))
        
        self.visualizer.capture_flash = 12
        self.audio.play('capture')
        
        print(f"✅ Captured point {len(self.captured_points)}/{self.total_points} at {pos}")
        
        if len(self.captured_points) >= self.total_points:
            self._complete_calibration()
        else:
            self.step += 1
            next_name = self.target_names[self.step - 1] if self.step <= len(self.target_names) else "next point"
            holo_prefix = "⬡ " if self.hologram_mode else ""
            self.instruction.setText(f"{holo_prefix}✅ Captured! Now aim at {next_name}")
            self.auto_capture.reset()

    def _complete_calibration(self):
        """Complete calibration - Show notification then auto-redirect"""
        print(f"🎉 Calibration complete! Captured {len(self.captured_points)} points {'[HOLOGRAM MODE]' if self.hologram_mode else ''}")
        
        self.zoom_btn.reset_zoom()
        
        # Calculate margins
        xs = [p[0] for p in self.captured_points]
        ys = [p[1] for p in self.captured_points]
        
        config.set_calibration_margins(min(xs), max(xs), min(ys), max(ys))
        
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        accuracy = min(100, (area / (self.display_width * self.display_height)) * 150)
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        
        # Add notification
        self.notification_manager.add_calibration(
            title="⬡ Calibration Complete" if self.hologram_mode else "Calibration Complete",
            message=f"{'⬡ Hologram mode • ' if self.hologram_mode else ''}Captured {self.total_points} points. "
                    f"Area: {width}×{height}px | Quality: {accuracy:.0f}%",
            data={
                "points": self.total_points,
                "accuracy": accuracy,
                "area": f"{width}x{height}",
                "hologram_mode": self.hologram_mode,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Show toast
        toast_notif = Notification(
            id="cal_complete_toast",
            title="⬡ Calibration Complete!" if self.hologram_mode else "🎯 Calibration Complete!",
            message=f"Quality: {accuracy:.0f}% | Redirecting to dashboard...",
            type=NotificationType.CALIBRATION,
            timestamp=datetime.now().isoformat(),
            icon="⬡" if self.hologram_mode else "🎯"
        )
        self.toast_manager.show_toast(toast_notif, duration_ms=3500)
        
        self.audio.play('complete')
        
        # Show visual notification
        self._update_overlay_positions()
        self.success_notification.show_notification(duration_ms=3500)
        
        holo_text = "⬡ HOLOGRAM MODE " if self.hologram_mode else ""
        self.instruction.setText(
            f"🎉 {holo_text}CALIBRATION COMPLETE!\n"
            f"Area: {width}×{height}px | Points: {self.total_points} | Quality: {accuracy:.0f}%\n"
            f"Redirecting to dashboard..."
        )
        
        # Update UI
        self.calibration_active = False
        self.action_btn.setVisible(False)
        self.capture_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.dashboard_btn.setVisible(True)
        self.point_selector.set_enabled(True)
        self.profile_btn.setEnabled(True)
        self.countdown_overlay.hide()
        self.zoom_btn.hide()
        
        self.calibrationComplete.emit()
        
        # Auto redirect after 3.8 seconds
        QTimer.singleShot(3800, self._auto_return_to_dashboard)

    def _auto_return_to_dashboard(self):
        """Auto return to dashboard after calibration"""
        print("🏠 Auto-redirecting to dashboard...")
        
        self._stop_camera()
        self._reset_ui()
        self.success_notification.hide()
        self.instruction.setText("Select the number of calibration points and click 'Start Calibration'")
        
        # Navigate
        parent = self.window()
        if hasattr(parent, "switch_page"):
            parent.switch_page(0)
            print("✅ Navigated to dashboard")
        elif hasattr(parent, "show_dashboard"):
            parent.show_dashboard()
            print("✅ Navigated to dashboard")
        else:
            print("⚠️ Could not find dashboard navigation method")

    def _return_to_dashboard(self):
        """Manual return to dashboard"""
        print("🏠 Manual return to dashboard...")
        self._auto_return_to_dashboard()

    def closeEvent(self, event):
        self._stop_camera()
        if hasattr(self, 'success_notification'):
            self.success_notification.cleanup()
        event.accept()
    
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self._load_settings_from_config)
        QTimer.singleShot(150, self._update_overlay_positions)
    
    def hideEvent(self, event):
        self._stop_camera()
        self._reset_ui()
        super().hideEvent(event)


# ============================================================
#                    MODULE TEST
# ============================================================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ CALIBRATION PAGE V3.0 — HOLOGRAM EDITION ⬡                              ║
║  Testing Calibration Interface                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0a0a1a, stop:0.5 #0f0f2d, stop:1 #1a1a3e);
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    window = QMainWindow()
    window.setWindowTitle("⬡ Calibration Page - Hologram Edition")
    window.setMinimumSize(1200, 800)
    
    cal_page = CalibrationPage()
    window.setCentralWidget(cal_page)
    
    window.show()
    sys.exit(app.exec())