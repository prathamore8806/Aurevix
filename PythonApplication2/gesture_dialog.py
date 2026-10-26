"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ GESTURE DIALOG MODULE V3.0 — HOLOGRAM EDITION ⬡                          ║
║  Futuristic Navy Blue Design • Cyberpunk Aesthetic                          ║
║  HUD Interface • Neon Glow • HOLOGRAM EFFECTS                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import cv2
import time
import os
import math
import random
import numpy as np
import mediapipe as mp

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QFrame,
    QMessageBox, QProgressBar, QGraphicsDropShadowEffect,
    QWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QPropertyAnimation, QEasingCurve, Property, QRect
from PySide6.QtGui import QImage, QPixmap, QColor, QFont, QPainter, QPen, QLinearGradient, QBrush


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ CYBERPUNK + HOLOGRAM COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Primary Navy Blues
    'bg_darkest': '#050a15',
    'bg_dark': '#0a1628',
    'bg_medium': '#1a2744',
    'bg_light': '#243555',
    
    # Hologram Colors
    'holo_cyan': '#00ffff',
    'holo_blue': '#00d4ff',
    'holo_purple': '#bf00ff',
    'holo_pink': '#ff00ff',
    'holo_green': '#00ff88',
    
    # Accent Colors
    'cyan_primary': '#00d4ff',
    'cyan_light': '#00e5ff',
    'cyan_dark': '#00a8cc',
    'cyan_glow': 'rgba(0, 212, 255, 0.6)',
    
    # Neon Colors
    'neon_green': '#00ff88',
    'neon_red': '#ff3366',
    'neon_orange': '#ff9500',
    'neon_yellow': '#ffcc00',
    'neon_purple': '#bf00ff',
    
    # Text Colors
    'text_primary': '#e8f4f8',
    'text_secondary': '#8aa4b8',
    'text_muted': '#5a7a90',
    
    # Border Colors
    'border_dark': 'rgba(0, 212, 255, 0.2)',
    'border_medium': 'rgba(0, 212, 255, 0.4)',
    'border_light': 'rgba(0, 212, 255, 0.6)',
}


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM SCANLINE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class HologramScanline(QWidget):
    """Animated holographic scanline overlay effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scanline_y = 0
        self.flicker_alpha = 1.0
        
        # Scanline animation timer
        self.scanline_timer = QTimer(self)
        self.scanline_timer.timeout.connect(self.update_scanline)
        self.scanline_timer.start(30)  # ~33 FPS
        
        # Flicker effect timer
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self.update_flicker)
        self.flicker_timer.start(100)
        
    def update_scanline(self):
        self.scanline_y += 3
        if self.scanline_y > self.height():
            self.scanline_y = 0
        self.update()
        
    def update_flicker(self):
        # Random flicker effect
        self.flicker_alpha = random.uniform(0.85, 1.0)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw horizontal scanlines
        painter.setPen(QPen(QColor(0, 255, 255, 15), 1))
        for y in range(0, self.height(), 3):
            painter.drawLine(0, y, self.width(), y)
        
        # Draw moving scanline
        gradient = QLinearGradient(0, self.scanline_y - 20, 0, self.scanline_y + 20)
        gradient.setColorAt(0, QColor(0, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(0, 255, 255, 60))
        gradient.setColorAt(1, QColor(0, 255, 255, 0))
        
        painter.fillRect(0, self.scanline_y - 20, self.width(), 40, gradient)
        
        # Apply flicker
        painter.fillRect(self.rect(), QColor(0, 255, 255, int(10 * (1 - self.flicker_alpha))))


class HologramFrame(QFrame):
    """Frame with holographic border effects and animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.border_phase = 0
        self.glitch_offset = 0
        
        # Border animation timer
        self.border_timer = QTimer(self)
        self.border_timer.timeout.connect(self.animate_border)
        self.border_timer.start(50)
        
        # Random glitch timer
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.trigger_glitch)
        self.glitch_timer.start(3000)  # Glitch every 3 seconds
        
        self.update_style()
        
    def animate_border(self):
        self.border_phase += 0.1
        if self.border_phase > 2 * math.pi:
            self.border_phase = 0
        self.update_style()
        
    def trigger_glitch(self):
        self.glitch_offset = random.randint(-3, 3)
        QTimer.singleShot(100, self.reset_glitch)
        
    def reset_glitch(self):
        self.glitch_offset = 0
        self.update_style()
        
    def update_style(self):
        # Calculate pulsing opacity
        pulse = int(40 + 20 * math.sin(self.border_phase))
        
        self.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 255, 255, 0.03),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba(191, 0, 255, 0.03));
                border: 2px solid rgba(0, 255, 255, {pulse / 100});
                border-radius: 16px;
                margin-left: {self.glitch_offset}px;
            }}
        """)


class HologramLabel(QLabel):
    """Label with holographic text effects."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.glitch_active = False
        
        # Glitch timer
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.maybe_glitch)
        self.glitch_timer.start(2000)
        
    def maybe_glitch(self):
        if random.random() < 0.3:  # 30% chance to glitch
            self.glitch_active = True
            self.apply_glitch()
            QTimer.singleShot(150, self.restore_text)
            
    def apply_glitch(self):
        glitch_chars = "!@#$%^&*<>[]{}|"
        glitched = ""
        for char in self.original_text:
            if random.random() < 0.2:
                glitched += random.choice(glitch_chars)
            else:
                glitched += char
        self.setText(glitched)
        
    def restore_text(self):
        self.glitch_active = False
        self.setText(self.original_text)
        
    def set_hologram_text(self, text):
        self.original_text = text
        self.setText(text)


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM PROGRESS BAR
# ═══════════════════════════════════════════════════════════════════════════════

class HologramProgressBar(QProgressBar):
    """Progress bar with holographic effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.glow_phase = 0
        
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.animate_glow)
        self.glow_timer.start(50)
        
    def animate_glow(self):
        self.glow_phase += 0.15
        if self.glow_phase > 2 * math.pi:
            self.glow_phase = 0
        self.update_style()
        
    def update_style(self):
        glow_intensity = int(30 + 20 * math.sin(self.glow_phase))
        
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 12px;
                text-align: center;
                color: {COLORS['cyan_light']};
                font-weight: bold;
                font-size: 11px;
                background: rgba(5, 10, 21, 0.9);
                padding: 2px;
                letter-spacing: 1px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 51, 102, 0.8),
                    stop:0.3 rgba(255, 149, 0, 0.8),
                    stop:0.6 rgba(255, 204, 0, 0.8),
                    stop:1 rgba(0, 255, 255, 0.8));
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, {glow_intensity / 100});
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class HologramButton(QPushButton):
    """Button with holographic hover and click effects."""
    
    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.hover_phase = 0
        self.is_hovered = False
        
        self.setCursor(Qt.PointingHandCursor)
        
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self.animate_hover)
        
        self.update_style()
        
    def enterEvent(self, event):
        self.is_hovered = True
        self.hover_timer.start(30)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.hover_timer.stop()
        self.hover_phase = 0
        self.update_style()
        super().leaveEvent(event)
        
    def animate_hover(self):
        self.hover_phase += 0.2
        if self.hover_phase > 2 * math.pi:
            self.hover_phase = 0
        self.update_style()
        
    def update_style(self):
        if self.button_type == "primary":
            base_color = "0, 212, 255"
            text_color = COLORS['cyan_light']
        elif self.button_type == "danger":
            base_color = "255, 51, 102"
            text_color = COLORS['neon_red']
        else:
            base_color = "90, 122, 144"
            text_color = COLORS['text_secondary']
            
        if self.is_hovered:
            glow = int(40 + 20 * math.sin(self.hover_phase))
            bg_alpha = 0.4
            border_alpha = 0.8
        else:
            glow = 25
            bg_alpha = 0.2
            border_alpha = 0.5
            
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 14px 32px;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({base_color}, {bg_alpha}),
                    stop:0.5 rgba({base_color}, {bg_alpha * 0.5}),
                    stop:1 rgba({base_color}, {bg_alpha}));
                border: 2px solid rgba({base_color}, {border_alpha});
                color: {text_color};
                font-weight: 700;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """)
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(glow)
        shadow.setOffset(0, 0)
        r, g, b = [int(x) for x in base_color.split(", ")]
        shadow.setColor(QColor(r, g, b, 150))
        self.setGraphicsEffect(shadow)


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ CYBERPUNK + HOLOGRAM DIALOG STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

def get_dialog_style():
    """Futuristic Navy Blue Cyberpunk + Hologram style for all dialogs."""
    return f"""
    /* ═══════════════════════════════════════════════════════════════════════
       MAIN DIALOG - Navy Blue HUD Background with Hologram tint
    ═══════════════════════════════════════════════════════════════════════ */
    QDialog {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {COLORS['bg_darkest']},
            stop:0.3 {COLORS['bg_dark']},
            stop:0.7 {COLORS['bg_dark']},
            stop:1 {COLORS['bg_darkest']});
        border: 2px solid {COLORS['border_medium']};
        border-radius: 16px;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       LABELS - Holographic Text Styles
    ═══════════════════════════════════════════════════════════════════════ */
    QLabel {{
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Consolas', monospace;
        font-size: 13px;
        background: transparent;
    }}

    QLabel#dialogTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {COLORS['holo_cyan']};
        padding: 5px 0;
        background: transparent;
        font-family: 'Segoe UI', 'Orbitron', sans-serif;
    }}

    QLabel#dialogSubtitle {{
        font-size: 13px;
        color: {COLORS['text_secondary']};
        padding: 0px;
        background: transparent;
        font-style: italic;
    }}

    QLabel#fieldLabel {{
        font-size: 13px;
        font-weight: 600;
        color: {COLORS['holo_cyan']};
        padding: 4px 0 2px 4px;
        background: transparent;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    QLabel#holoLabel {{
        color: {COLORS['holo_cyan']};
        font-size: 14px;
        font-weight: 600;
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        padding: 8px 12px;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       LINE EDIT - Holographic Input Fields
    ═══════════════════════════════════════════════════════════════════════ */
    QLineEdit {{
        padding: 14px 18px;
        border-radius: 10px;
        background: rgba(5, 10, 21, 0.95);
        color: {COLORS['holo_cyan']};
        border: 2px solid {COLORS['border_dark']};
        font-size: 14px;
        font-family: 'Consolas', 'Segoe UI', monospace;
        selection-background-color: rgba(0, 255, 255, 0.3);
    }}

    QLineEdit:hover {{
        border: 2px solid {COLORS['border_medium']};
        background: rgba(10, 22, 40, 0.95);
    }}

    QLineEdit:focus {{
        border: 2px solid {COLORS['holo_cyan']};
        background: rgba(10, 22, 40, 1.0);
    }}

    QLineEdit::placeholder {{
        color: {COLORS['text_muted']};
        font-style: italic;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       COMBO BOX - Holographic Dropdowns
    ═══════════════════════════════════════════════════════════════════════ */
    QComboBox {{
        padding: 14px 18px;
        border-radius: 10px;
        background: rgba(5, 10, 21, 0.95);
        color: {COLORS['holo_cyan']};
        border: 2px solid {COLORS['border_dark']};
        font-size: 14px;
        font-family: 'Segoe UI', sans-serif;
    }}

    QComboBox:hover {{
        border: 2px solid {COLORS['border_medium']};
    }}

    QComboBox:focus {{
        border: 2px solid {COLORS['holo_cyan']};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 16px;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 8px solid {COLORS['holo_cyan']};
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background: {COLORS['bg_darkest']};
        color: {COLORS['holo_cyan']};
        border: 2px solid {COLORS['border_medium']};
        border-radius: 10px;
        selection-background-color: rgba(0, 255, 255, 0.3);
        padding: 6px;
        outline: none;
    }}

    QComboBox QAbstractItemView::item {{
        padding: 10px 14px;
        border-radius: 6px;
        margin: 2px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background: rgba(0, 255, 255, 0.2);
    }}

    QComboBox QAbstractItemView::item:selected {{
        background: rgba(0, 255, 255, 0.35);
        color: white;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       GLASS CARD FRAME - HUD Panel with Hologram tint
    ═══════════════════════════════════════════════════════════════════════ */
    QFrame#glassCard {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(0, 255, 255, 0.02),
            stop:0.5 rgba(10, 22, 40, 0.9),
            stop:1 rgba(191, 0, 255, 0.02));
        border-radius: 14px;
        border: 1px solid {COLORS['border_dark']};
        padding: 16px;
    }}

    QFrame#hudPanel {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(0, 255, 255, 0.08),
            stop:0.5 rgba(10, 22, 40, 0.95),
            stop:1 rgba(191, 0, 255, 0.05));
        border: 2px solid {COLORS['border_medium']};
        border-radius: 16px;
        padding: 20px;
    }}

    QFrame#cameraFrame {{
        background: rgba(0, 0, 0, 0.95);
        border-radius: 14px;
        border: 3px solid {COLORS['neon_red']};
        padding: 4px;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       SCROLL BAR - Hologram Style
    ═══════════════════════════════════════════════════════════════════════ */
    QScrollBar:vertical {{
        background: rgba(5, 10, 21, 0.5);
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLORS['holo_cyan']},
            stop:0.5 {COLORS['holo_purple']},
            stop:1 {COLORS['holo_cyan']});
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLORS['holo_cyan']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       MESSAGE BOX - Holographic Alerts
    ═══════════════════════════════════════════════════════════════════════ */
    QMessageBox {{
        background: {COLORS['bg_darkest']};
        border: 2px solid {COLORS['holo_cyan']};
        border-radius: 12px;
    }}

    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        font-size: 13px;
    }}

    QMessageBox QPushButton {{
        padding: 10px 24px;
        border-radius: 8px;
        background: rgba(0, 255, 255, 0.15);
        color: {COLORS['holo_cyan']};
        border: 1px solid {COLORS['border_medium']};
        font-weight: 600;
    }}

    QMessageBox QPushButton:hover {{
        background: rgba(0, 255, 255, 0.35);
        color: white;
    }}
    """


def add_shadow(widget, blur=25, offset=4, color=QColor(0, 255, 255, 60)):
    """Add cyberpunk neon glow shadow effect to widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(offset, offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


def add_hologram_glow(widget, color=QColor(0, 255, 255, 100)):
    """Add holographic glow effect (no offset, just blur)."""
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(40)
    glow.setOffset(0, 0)
    glow.setColor(color)
    widget.setGraphicsEffect(glow)


def create_hologram_header(title_text, subtitle_text=None, icon="⬡"):
    """Create a futuristic HUD-style header widget with hologram effects."""
    header_frame = HologramFrame()
    header_frame.setStyleSheet(f"""
        HologramFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(0, 255, 255, 0.08),
                stop:0.5 rgba(10, 22, 40, 0.95),
                stop:1 rgba(191, 0, 255, 0.05));
            border: 2px solid rgba(0, 255, 255, 0.4);
            border-radius: 14px;
            padding: 16px;
        }}
    """)
    
    layout = QVBoxLayout(header_frame)
    layout.setSpacing(6)
    
    # Title row with icon
    title_row = QHBoxLayout()
    
    icon_label = QLabel(icon)
    icon_label.setStyleSheet(f"""
        font-size: 28px;
        color: {COLORS['holo_cyan']};
        background: transparent;
    """)
    title_row.addWidget(icon_label)
    
    title_label = HologramLabel(title_text)
    title_label.setStyleSheet(f"""
        font-size: 22px;
        font-weight: 700;
        color: {COLORS['holo_cyan']};
        background: transparent;
        letter-spacing: 2px;
    """)
    title_row.addWidget(title_label)
    title_row.addStretch()
    
    layout.addLayout(title_row)
    
    if subtitle_text:
        subtitle = QLabel(f"◈ {subtitle_text}")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        layout.addWidget(subtitle)
    
    add_hologram_glow(header_frame, QColor(0, 255, 255, 50))
    
    return header_frame


def create_status_badge(text, status="waiting"):
    """Create a holographic status badge."""
    badge = QLabel(text)
    
    styles = {
        "waiting": f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 204, 0, 0.1),
                stop:0.5 rgba(255, 204, 0, 0.2),
                stop:1 rgba(255, 204, 0, 0.1));
            color: {COLORS['neon_yellow']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(255, 204, 0, 0.5);
            text-transform: uppercase;
            letter-spacing: 1px;
        """,
        "recording": f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 51, 102, 0.1),
                stop:0.5 rgba(255, 51, 102, 0.25),
                stop:1 rgba(255, 51, 102, 0.1));
            color: {COLORS['neon_red']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(255, 51, 102, 0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
        """,
        "success": f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(0, 255, 136, 0.1),
                stop:0.5 rgba(0, 255, 136, 0.2),
                stop:1 rgba(0, 255, 136, 0.1));
            color: {COLORS['neon_green']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(0, 255, 136, 0.5);
            text-transform: uppercase;
            letter-spacing: 1px;
        """,
        "error": f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 51, 102, 0.15),
                stop:0.5 rgba(255, 51, 102, 0.3),
                stop:1 rgba(255, 51, 102, 0.15));
            color: {COLORS['neon_red']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(255, 51, 102, 0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
        """
    }
    
    badge.setStyleSheet(styles.get(status, styles["waiting"]))
    return badge


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ RECORDING THREAD - Camera Capture with Hologram HUD Overlay
# ═══════════════════════════════════════════════════════════════════════════════

class RecordingThread(QThread):
    """Background thread for recording gesture from camera with holographic HUD overlay."""
    frame_ready = Signal(np.ndarray)
    hand_detected = Signal(bool, int)
    recording_done = Signal(list)
    no_hand_detected = Signal()
    progress_update = Signal(float)

    def __init__(self, camera_index=0, duration=5):
        super().__init__()
        self.camera_index = camera_index
        self.duration = duration
        self.running = True
        self.frame_count = 0

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def draw_hologram_scanlines(self, frame):
        """Draw holographic scanline effect on frame."""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Horizontal scanlines
        for y in range(0, h, 3):
            cv2.line(overlay, (0, y), (w, y), (255, 255, 0), 1)
        
        # Moving scanline
        scanline_y = (self.frame_count * 4) % h
        cv2.rectangle(overlay, (0, scanline_y - 15), (w, scanline_y + 15), 
                     (255, 255, 0), -1)
        
        # Blend with low opacity
        frame = cv2.addWeighted(overlay, 0.03, frame, 0.97, 0)
        
        return frame

    def draw_chromatic_aberration(self, frame, offset=2):
        """Add chromatic aberration (RGB split) effect."""
        h, w = frame.shape[:2]
        
        # Create separate channels with offset
        b, g, r = cv2.split(frame)
        
        # Offset red channel right
        r_shifted = np.zeros_like(r)
        r_shifted[:, offset:] = r[:, :-offset]
        
        # Offset blue channel left
        b_shifted = np.zeros_like(b)
        b_shifted[:, :-offset] = b[:, offset:]
        
        # Merge back
        frame = cv2.merge([b_shifted, g, r_shifted])
        
        return frame

    def draw_hologram_overlay(self, frame, elapsed, remaining, hand_detected, points_count):
        """Draw futuristic holographic HUD overlay on camera frame."""
        h, w = frame.shape[:2]
        self.frame_count += 1
        
        # Apply hologram effects
        frame = self.draw_hologram_scanlines(frame)
        
        # Random glitch effect
        if random.random() < 0.02:  # 2% chance per frame
            frame = self.draw_chromatic_aberration(frame, random.randint(2, 5))
        
        overlay = frame.copy()
        
        # ═══════════════════════════════════════════════════════════════════
        # TOP HUD BAR - Holographic gradient
        # ═══════════════════════════════════════════════════════════════════
        for i in range(80):
            alpha = 1.0 - (i / 80.0)
            # Cyan-tinted navy gradient
            b = int(60 * alpha)
            g = int(40 * alpha)
            r = int(10 * alpha)
            cv2.line(overlay, (0, i), (w, i), (b, g, r), 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # BOTTOM HUD BAR
        # ═══════════════════════════════════════════════════════════════════
        for i in range(80):
            y = h - 80 + i
            alpha = i / 80.0
            b = int(60 * alpha)
            g = int(40 * alpha)
            r = int(10 * alpha)
            cv2.line(overlay, (0, y), (w, y), (b, g, r), 1)
        
        frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)
        
        # ═══════════════════════════════════════════════════════════════════
        # HOLOGRAM CORNER BRACKETS - Animated
        # ═══════════════════════════════════════════════════════════════════
        pulse = int(200 + 55 * math.sin(elapsed * 4))
        bracket_color = (255, 255, 0)  # Cyan in BGR
        bracket_len = 50
        bracket_thickness = 2
        margin = 20
        
        # Outer glow for brackets
        glow_color = (pulse, pulse, 0)
        
        # Top-left corner
        cv2.line(frame, (margin, margin), (margin + bracket_len, margin), glow_color, bracket_thickness + 2)
        cv2.line(frame, (margin, margin), (margin, margin + bracket_len), glow_color, bracket_thickness + 2)
        cv2.line(frame, (margin, margin), (margin + bracket_len, margin), bracket_color, bracket_thickness)
        cv2.line(frame, (margin, margin), (margin, margin + bracket_len), bracket_color, bracket_thickness)
        
        # Top-right corner
        cv2.line(frame, (w - margin, margin), (w - margin - bracket_len, margin), glow_color, bracket_thickness + 2)
        cv2.line(frame, (w - margin, margin), (w - margin, margin + bracket_len), glow_color, bracket_thickness + 2)
        cv2.line(frame, (w - margin, margin), (w - margin - bracket_len, margin), bracket_color, bracket_thickness)
        cv2.line(frame, (w - margin, margin), (w - margin, margin + bracket_len), bracket_color, bracket_thickness)
        
        # Bottom-left corner
        cv2.line(frame, (margin, h - margin), (margin + bracket_len, h - margin), glow_color, bracket_thickness + 2)
        cv2.line(frame, (margin, h - margin), (margin, h - margin - bracket_len), glow_color, bracket_thickness + 2)
        cv2.line(frame, (margin, h - margin), (margin + bracket_len, h - margin), bracket_color, bracket_thickness)
        cv2.line(frame, (margin, h - margin), (margin, h - margin - bracket_len), bracket_color, bracket_thickness)
        
        # Bottom-right corner
        cv2.line(frame, (w - margin, h - margin), (w - margin - bracket_len, h - margin), glow_color, bracket_thickness + 2)
        cv2.line(frame, (w - margin, h - margin), (w - margin, h - margin - bracket_len), glow_color, bracket_thickness + 2)
        cv2.line(frame, (w - margin, h - margin), (w - margin - bracket_len, h - margin), bracket_color, bracket_thickness)
        cv2.line(frame, (w - margin, h - margin), (w - margin, h - margin - bracket_len), bracket_color, bracket_thickness)
        
        # ═══════════════════════════════════════════════════════════════════
        # HOLOGRAM GRID PATTERN
        # ═══════════════════════════════════════════════════════════════════
        grid_color = (255, 128, 0, 20)  # Faint cyan
        for x in range(0, w, 40):
            cv2.line(frame, (x, 80), (x, h - 80), (255, 128, 0), 1)
        for y in range(80, h - 80, 40):
            cv2.line(frame, (0, y), (w, y), (255, 128, 0), 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # RECORDING INDICATOR - Pulsing hologram dot
        # ═══════════════════════════════════════════════════════════════════
        rec_pulse = int(8 + 4 * math.sin(elapsed * 6))
        if int(elapsed * 3) % 2 == 0:
            cv2.circle(frame, (40, 40), rec_pulse + 4, (102, 51, 255), 2)
            cv2.circle(frame, (40, 40), rec_pulse, (102, 102, 255), -1)
        else:
            cv2.circle(frame, (40, 40), rec_pulse, (102, 51, 255), -1)
        
        # Holographic REC text with glow
        cv2.putText(frame, "REC", (60, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (102, 51, 255), 3)
        cv2.putText(frame, "REC", (60, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 150, 255), 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # HOLOGRAM TIMER DISPLAY
        # ═══════════════════════════════════════════════════════════════════
        timer_text = f"{remaining:.1f}s"
        # Glow effect
        cv2.putText(frame, timer_text, (w - 100, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 150, 0), 4)
        cv2.putText(frame, timer_text, (w - 100, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
        
        # ═══════════════════════════════════════════════════════════════════
        # HOLOGRAPHIC PROGRESS BAR
        # ═══════════════════════════════════════════════════════════════════
        bar_y = h - 50
        bar_margin = 35
        bar_width = w - (bar_margin * 2)
        bar_height = 16
        
        # Background with hologram effect
        cv2.rectangle(frame, (bar_margin - 2, bar_y - 2), 
                     (bar_margin + bar_width + 2, bar_y + bar_height + 2), 
                     (255, 255, 0), 1)
        cv2.rectangle(frame, (bar_margin, bar_y), 
                     (bar_margin + bar_width, bar_y + bar_height), 
                     (40, 30, 10), -1)
        
        # Progress fill with holographic gradient
        progress_width = int((elapsed / self.duration) * bar_width)
        if progress_width > 0:
            for x in range(bar_margin, min(bar_margin + progress_width, bar_margin + bar_width)):
                ratio = (x - bar_margin) / bar_width
                # Holographic color shift: cyan -> purple -> pink
                phase = ratio * 2 * math.pi + elapsed * 2
                r = int(128 + 127 * math.sin(phase))
                g = int(128 + 127 * math.sin(phase + 2))
                b = int(200 + 55 * math.sin(phase + 4))
                cv2.line(frame, (x, bar_y + 2), (x, bar_y + bar_height - 2), (b, g, r), 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # HOLOGRAM STATUS TEXT
        # ═══════════════════════════════════════════════════════════════════
        if hand_detected:
            status_text = f"[TRACKING ACTIVE] FRAMES: {points_count}"
            status_color = (136, 255, 0)  # Neon green in BGR
        else:
            status_text = "[AWAITING HAND DETECTION]"
            status_color = (0, 200, 255)  # Orange in BGR
        
        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = (w - text_size[0]) // 2
        
        # Glow effect for text
        cv2.putText(frame, status_text, (text_x, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
        cv2.putText(frame, status_text, (text_x, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # DATA READOUT - Top right
        # ═══════════════════════════════════════════════════════════════════
        data_text = f"DATA: {points_count}"
        cv2.putText(frame, data_text, (w - 120, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # System info text
        sys_text = f"FPS: {int(self.frame_count / max(elapsed, 0.1))}"
        cv2.putText(frame, sys_text, (45, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)
        
        return frame

    def draw_hologram_hand(self, frame, hand_lm, elapsed):
        """Draw holographic hand landmarks with chromatic effect."""
        lm = hand_lm.landmark
        h, w = frame.shape[:2]
        
        connections = self.mp_hands.HAND_CONNECTIONS
        tips = [4, 8, 12, 16, 20]
        
        # Draw connections with holographic glow effect
        for connection in connections:
            start_idx, end_idx = connection
            x1 = int(lm[start_idx].x * w)
            y1 = int(lm[start_idx].y * h)
            x2 = int(lm[end_idx].x * w)
            y2 = int(lm[end_idx].y * h)
            
            # Calculate color based on position for holographic effect
            phase = elapsed * 3 + (x1 + y1) * 0.01
            r = int(128 + 127 * math.sin(phase))
            g = int(200 + 55 * math.sin(phase + 1))
            b = 255
            
            # Outer glow
            cv2.line(frame, (x1, y1), (x2, y2), (b, int(g*0.5), int(r*0.5)), 8)
            # Inner line
            cv2.line(frame, (x1, y1), (x2, y2), (b, g, r), 2)
        
        # Draw landmarks with holographic effect
        for i, l in enumerate(lm):
            x = int(l.x * w)
            y = int(l.y * h)
            
            phase = elapsed * 4 + i * 0.3
            pulse = int(4 + 2 * math.sin(phase))
            
            if i in tips:
                # Fingertips - larger with holographic rings
                cv2.circle(frame, (x, y), 14 + pulse, (255, 200, 0), 1)
                cv2.circle(frame, (x, y), 10 + pulse, (255, 255, 0), 2)
                cv2.circle(frame, (x, y), 6, (255, 255, 200), -1)
            elif i == 0:
                # Wrist - special hologram marker
                cv2.circle(frame, (x, y), 12 + pulse, (255, 0, 191), 2)
                cv2.circle(frame, (x, y), 8, (255, 100, 220), -1)
            else:
                # Other landmarks
                cv2.circle(frame, (x, y), 5, (255, 255, 0), -1)
                cv2.circle(frame, (x, y), 3, (255, 255, 200), -1)
        
        return frame

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            self.no_hand_detected.emit()
            return

        recorded_points = []
        hand_seen = False
        start_time = time.time()

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            elapsed = time.time() - start_time
            remaining = max(0, self.duration - elapsed)

            self.progress_update.emit(elapsed)

            hand_detected = False
            points_count = len(recorded_points)

            if results.multi_hand_landmarks:
                hand_seen = True
                hand_detected = True
                self.hand_detected.emit(True, len(recorded_points))

                for hand_lm in results.multi_hand_landmarks:
                    # Draw holographic hand
                    frame = self.draw_hologram_hand(frame, hand_lm, elapsed)
                    
                    # Record data
                    point = {
                        "time": round(elapsed, 3),
                        "landmarks": [
                            {"id": i, "x": round(l.x, 4),
                             "y": round(l.y, 4), "z": round(l.z, 4)}
                            for i, l in enumerate(hand_lm.landmark)
                        ]
                    }
                    recorded_points.append(point)
            else:
                self.hand_detected.emit(False, len(recorded_points))

            # Draw holographic HUD overlay
            frame = self.draw_hologram_overlay(frame, elapsed, remaining, 
                                                hand_detected, len(recorded_points))

            self.frame_ready.emit(frame)

            if elapsed >= self.duration:
                break

        cap.release()

        if not hand_seen or len(recorded_points) < 10:
            self.no_hand_detected.emit()
        else:
            self.recording_done.emit(recorded_points)

    def stop(self):
        self.running = False
        self.wait(3000)


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ GESTURE RECORD DIALOG - Holographic Camera Interface
# ═══════════════════════════════════════════════════════════════════════════════

class GestureRecordDialog(QDialog):
    """Futuristic holographic camera recording dialog."""

    def __init__(self, parent=None, camera_index=0, duration=5):
        super().__init__(parent)
        self.setWindowTitle("⬡ HOLOGRAM GESTURE RECORDER")
        self.setFixedSize(800, 720)
        self.setModal(True)
        self.setStyleSheet(get_dialog_style())

        self.recorded_data = None
        self.camera_index = camera_index
        self.duration = duration

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM HEADER SECTION
        # ═══════════════════════════════════════════════════════════════════
        header_card = HologramFrame()
        header_card.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 51, 102, 0.08),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba(0, 255, 255, 0.05));
                border: 2px solid rgba(255, 51, 102, 0.5);
                border-radius: 14px;
                padding: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header_card)

        header_left = QVBoxLayout()

        title = HologramLabel("⬡ HOLOGRAM CAPTURE SYSTEM")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {COLORS['neon_red']};
            background: transparent;
            letter-spacing: 2px;
        """)
        header_left.addWidget(title)

        subtitle = QLabel("◈ Perform your gesture within the holographic zone")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
            font-style: italic;
        """)
        header_left.addWidget(subtitle)

        header_layout.addLayout(header_left)
        header_layout.addStretch()

        self.status_badge = create_status_badge("⏳ INITIALIZING", "waiting")
        header_layout.addWidget(self.status_badge)

        add_hologram_glow(header_card, QColor(255, 51, 102, 50))
        layout.addWidget(header_card)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAPHIC CAMERA DISPLAY
        # ═══════════════════════════════════════════════════════════════════
        cam_container = QWidget()
        cam_container_layout = QVBoxLayout(cam_container)
        cam_container_layout.setContentsMargins(0, 0, 0, 0)
        
        cam_frame = HologramFrame()
        cam_frame.setStyleSheet(f"""
            HologramFrame {{
                background: rgba(0, 0, 0, 0.95);
                border-radius: 14px;
                border: 3px solid {COLORS['holo_cyan']};
                padding: 4px;
            }}
        """)
        cam_layout = QVBoxLayout(cam_frame)
        cam_layout.setContentsMargins(4, 4, 4, 4)

        self.camera_label = QLabel()
        self.camera_label.setFixedSize(740, 420)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #020510,
                stop:0.5 #050a18,
                stop:1 #020510);
            border-radius: 10px;
            color: {COLORS['holo_cyan']};
            font-size: 16px;
            font-family: 'Consolas', monospace;
        """)
        self.camera_label.setText("⬡ INITIALIZING HOLOGRAM FEED...")
        cam_layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)

        # Add scanline overlay to camera
        self.scanline_overlay = HologramScanline(self.camera_label)
        self.scanline_overlay.setGeometry(0, 0, 740, 420)
        self.scanline_overlay.raise_()

        add_hologram_glow(cam_frame, QColor(0, 255, 255, 60))
        cam_container_layout.addWidget(cam_frame)
        layout.addWidget(cam_container)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAPHIC PROGRESS BAR
        # ═══════════════════════════════════════════════════════════════════
        self.progress = HologramProgressBar()
        self.progress.setRange(0, duration * 10)
        self.progress.setValue(0)
        self.progress.setFixedHeight(36)
        self.progress.setFormat("◈ AWAITING CAPTURE START...")
        layout.addWidget(self.progress)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM INFO ROW
        # ═══════════════════════════════════════════════════════════════════
        info_card = HologramFrame()
        info_card.setStyleSheet(f"""
            HologramFrame {{
                background: rgba(5, 10, 21, 0.85);
                border-radius: 12px;
                border: 1px solid {COLORS['border_dark']};
                padding: 12px 16px;
            }}
        """)
        info_row = QHBoxLayout(info_card)

        self.hand_indicator = HologramLabel("◈ AWAITING HAND DETECTION...")
        self.hand_indicator.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            letter-spacing: 1px;
        """)
        info_row.addWidget(self.hand_indicator)

        info_row.addStretch()

        self.points_label = HologramLabel("▸ DATA FRAMES: 0")
        self.points_label.setStyleSheet(f"""
            color: {COLORS['holo_cyan']};
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            letter-spacing: 1px;
        """)
        info_row.addWidget(self.points_label)

        layout.addWidget(info_card)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM CANCEL BUTTON
        # ═══════════════════════════════════════════════════════════════════
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = HologramButton("✖  ABORT CAPTURE", "danger")
        cancel_btn.setMinimumHeight(50)
        cancel_btn.clicked.connect(self.cancel_recording)
        btn_row.addWidget(cancel_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Start recording
        self.recording_thread = None
        QTimer.singleShot(500, self.start_recording)

    def start_recording(self):
        self.recording_thread = RecordingThread(
            camera_index=self.camera_index,
            duration=self.duration
        )
        self.recording_thread.frame_ready.connect(self.update_frame)
        self.recording_thread.hand_detected.connect(self.update_hand_status)
        self.recording_thread.recording_done.connect(self.on_done)
        self.recording_thread.no_hand_detected.connect(self.on_no_hand)
        self.recording_thread.progress_update.connect(self.update_progress)
        self.recording_thread.start()

        self.status_badge.setText("⬡ RECORDING")
        self.status_badge.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 51, 102, 0.15),
                stop:0.5 rgba(255, 51, 102, 0.3),
                stop:1 rgba(255, 51, 102, 0.15));
            color: {COLORS['neon_red']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(255, 51, 102, 0.6);
            letter-spacing: 2px;
        """)

    def update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (740, 420))
        h, w, ch = resized.shape
        qimg = QImage(resized.data, w, h, ch * w, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qimg))

    def update_hand_status(self, detected, points):
        if detected:
            self.hand_indicator.set_hologram_text("◈ HAND LOCKED — CAPTURING HOLOGRAM DATA")
            self.hand_indicator.setStyleSheet(f"""
                color: {COLORS['neon_green']};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
                letter-spacing: 1px;
            """)
            self.points_label.set_hologram_text(f"▸ DATA FRAMES: {points}")
        else:
            self.hand_indicator.set_hologram_text("◈ NO HAND DETECTED — SHOW YOUR HAND")
            self.hand_indicator.setStyleSheet(f"""
                color: {COLORS['neon_orange']};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
                letter-spacing: 1px;
            """)

    def update_progress(self, elapsed):
        val = int(elapsed * 10)
        self.progress.setValue(min(val, self.duration * 10))
        remaining = max(0, self.duration - elapsed)
        self.progress.setFormat(f"◈ HOLOGRAM CAPTURE: {remaining:.1f}s REMAINING")

    def on_done(self, points):
        self.recorded_data = points
        self.progress.setValue(self.duration * 10)
        self.progress.setFormat("◈ HOLOGRAM CAPTURE COMPLETE")
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid rgba(0, 255, 136, 0.6);
                border-radius: 12px;
                text-align: center;
                color: {COLORS['neon_green']};
                font-weight: bold;
                font-size: 11px;
                background: rgba(5, 10, 21, 0.9);
                letter-spacing: 1px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 255, 136, 0.5),
                    stop:0.5 rgba(0, 255, 200, 0.7),
                    stop:1 rgba(0, 255, 136, 0.5));
                border-radius: 10px;
            }}
        """)

        self.status_badge.setText("✓ COMPLETE")
        self.status_badge.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(0, 255, 136, 0.15),
                stop:0.5 rgba(0, 255, 136, 0.25),
                stop:1 rgba(0, 255, 136, 0.15));
            color: {COLORS['neon_green']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(0, 255, 136, 0.6);
            letter-spacing: 2px;
        """)

        # Stop scanline animation
        self.scanline_overlay.scanline_timer.stop()
        self.scanline_overlay.flicker_timer.stop()

        if self.recording_thread:
            self.recording_thread.stop()

        QTimer.singleShot(800, self.accept)

    def on_no_hand(self):
        if self.recording_thread:
            self.recording_thread.stop()

        self.status_badge.setText("✖ FAILED")
        self.status_badge.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 51, 102, 0.2),
                stop:0.5 rgba(255, 51, 102, 0.35),
                stop:1 rgba(255, 51, 102, 0.2));
            color: {COLORS['neon_red']};
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 12px;
            border: 2px solid rgba(255, 51, 102, 0.7);
            letter-spacing: 2px;
        """)

        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ Hologram Capture Failed")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"<h3 style='color: {COLORS['neon_red']};'>✖ NO GESTURE DETECTED</h3>"
            f"<p style='color: {COLORS['text_secondary']};'>"
            "No hand was detected during the hologram capture.<br><br>"
            f"<b style='color: {COLORS['holo_cyan']};'>◈ DIAGNOSTIC CHECKS:</b><br>"
            "▸ Verify hand is visible to camera<br>"
            "▸ Ensure adequate lighting conditions<br>"
            "▸ Position hand within hologram zone<br>"
            "▸ Confirm camera is not obstructed</p>"
        )
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid {COLORS['holo_cyan']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(0, 255, 255, 0.15);
                color: {COLORS['holo_cyan']};
                border: 1px solid {COLORS['border_medium']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(0, 255, 255, 0.35);
            }}
        """)
        msg.exec()
        self.reject()

    def cancel_recording(self):
        # Stop scanline animation
        self.scanline_overlay.scanline_timer.stop()
        self.scanline_overlay.flicker_timer.stop()
        
        if self.recording_thread:
            self.recording_thread.stop()
        self.reject()

    def get_recorded_data(self):
        """Return averaged landmarks from recording in the format recognizer expects."""
        if not self.recorded_data or len(self.recorded_data) == 0:
            return None
        
        # Average the middle 50% of frames (ignore start/end jitter)
        total_frames = len(self.recorded_data)
        start_idx = total_frames // 4
        end_idx = 3 * total_frames // 4
        
        frames_to_average = self.recorded_data[start_idx:end_idx]
        
        if len(frames_to_average) == 0:
            frames_to_average = self.recorded_data
        
        # Average all landmark positions
        num_landmarks = 21  # MediaPipe hand has 21 landmarks
        averaged = []
        
        for lm_id in range(num_landmarks):
            x_sum = 0
            y_sum = 0
            z_sum = 0
            count = 0
            
            for frame in frames_to_average:
                if lm_id < len(frame["landmarks"]):
                    lm = frame["landmarks"][lm_id]
                    x_sum += lm["x"]
                    y_sum += lm["y"]
                    z_sum += lm["z"]
                    count += 1
            
            if count > 0:
                averaged.append({
                    "x": x_sum / count,
                    "y": y_sum / count,
                    "z": z_sum / count
                })
        
        print(f"⬡ Processed {len(averaged)} landmarks from {len(frames_to_average)} hologram frames")
        return averaged if len(averaged) == 21 else None

    def closeEvent(self, event):
        # Stop scanline animation
        self.scanline_overlay.scanline_timer.stop()
        self.scanline_overlay.flicker_timer.stop()
        
        if self.recording_thread:
            self.recording_thread.stop()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ GESTURE CONFIG DIALOG - Holographic Configuration Interface
# ═══════════════════════════════════════════════════════════════════════════════

class GestureConfigDialog(QDialog):
    """Futuristic holographic gesture configuration dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⬡ CONFIGURE GESTURE")
        self.setFixedSize(560, 620)
        self.setModal(True)
        self.setStyleSheet(get_dialog_style())

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(28, 28, 28, 28)

        # Add scanline overlay to entire dialog
        self.scanline_overlay = HologramScanline(self)
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM HEADER CARD
        # ═══════════════════════════════════════════════════════════════════
        header_card = HologramFrame()
        header_card.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 255, 255, 0.1),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba(191, 0, 255, 0.05));
                border: 2px solid {COLORS['holo_cyan']};
                border-radius: 14px;
                padding: 18px;
            }}
        """)
        header_layout = QVBoxLayout(header_card)

        title = HologramLabel("⬡ GESTURE CONFIGURATION")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['holo_cyan']};
            background: transparent;
            letter-spacing: 2px;
        """)
        header_layout.addWidget(title)

        subtitle = QLabel("◈ Define holographic action parameters")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        header_layout.addWidget(subtitle)

        add_hologram_glow(header_card, QColor(0, 255, 255, 50))
        layout.addWidget(header_card)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM FORM CARD
        # ═══════════════════════════════════════════════════════════════════
        form_card = HologramFrame()
        form_card.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 255, 255, 0.03),
                    stop:0.5 rgba(10, 22, 40, 0.9),
                    stop:1 rgba(191, 0, 255, 0.03));
                border-radius: 14px;
                border: 1px solid {COLORS['border_dark']};
                padding: 20px;
            }}
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(8)

        # ─────────────────────────────────────────────────────────────
        # Gesture Name
        # ─────────────────────────────────────────────────────────────
        name_label = QLabel("▸ GESTURE IDENTIFIER")
        name_label.setObjectName("fieldLabel")
        form_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter name (e.g. Screenshot, Volume Up, Next Tab)")
        self.name_input.setMinimumHeight(48)
        form_layout.addWidget(self.name_input)

        form_layout.addSpacing(6)

        # ─────────────────────────────────────────────────────────────
        # Mode Selection
        # ─────────────────────────────────────────────────────────────
        mode_label = QLabel("▸ TARGET MODE")
        mode_label.setObjectName("fieldLabel")
        form_layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "⬡  DESKTOP",
            "⬡  GAMING",
            "⬡  DRAW",
            "⬡  ALL MODES"
        ])
        self.mode_combo.setMinimumHeight(48)
        form_layout.addWidget(self.mode_combo)

        form_layout.addSpacing(6)

        # ─────────────────────────────────────────────────────────────
        # Action Type
        # ─────────────────────────────────────────────────────────────
        action_label = QLabel("▸ ACTION TYPE")
        action_label.setObjectName("fieldLabel")
        form_layout.addWidget(action_label)

        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems([
            "◈  Key Press",
            "◈  Mouse Click",
            "◈  Scroll",
            "◈  App Launch",
            "◈  Keyboard Shortcut (Hotkey)",
            "◈  Volume Control",
            "◈  Type Text"
        ])
        self.action_type_combo.setMinimumHeight(48)
        self.action_type_combo.currentIndexChanged.connect(self._update_target_placeholder)
        form_layout.addWidget(self.action_type_combo)

        form_layout.addSpacing(6)

        # ─────────────────────────────────────────────────────────────
        # Target
        # ─────────────────────────────────────────────────────────────
        target_label = QLabel("▸ ACTION TARGET")
        target_label.setObjectName("fieldLabel")
        form_layout.addWidget(target_label)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter target (e.g. space, ctrl+c, notepad.exe)")
        self.target_input.setMinimumHeight(48)
        form_layout.addWidget(self.target_input)

        # Help text with hologram style
        self.help_label = QLabel("◈ Examples: space, enter, ctrl+c, win+shift+s")
        self.help_label.setStyleSheet(f"""
            color: {COLORS['holo_cyan']};
            font-size: 11px;
            padding: 8px 12px;
            background: rgba(0, 255, 255, 0.05);
            border-left: 3px solid {COLORS['holo_cyan']};
            border-radius: 0 6px 6px 0;
        """)
        form_layout.addWidget(self.help_label)

        add_shadow(form_card, blur=25, color=QColor(0, 255, 255, 40))
        layout.addWidget(form_card)

        layout.addSpacing(12)

        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM BUTTONS
        # ═══════════════════════════════════════════════════════════════════
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        cancel_btn = HologramButton("✖  CANCEL", "secondary")
        cancel_btn.setMinimumHeight(52)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = HologramButton("◈  SAVE GESTURE", "primary")
        save_btn.setMinimumHeight(52)
        save_btn.clicked.connect(self.validate_and_accept)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def resizeEvent(self, event):
        """Update scanline overlay size on resize."""
        super().resizeEvent(event)
        self.scanline_overlay.setGeometry(self.rect())

    def _update_target_placeholder(self, index):
        """Update placeholder text based on selected action type."""
        placeholders = {
            0: "Enter key (e.g. space, enter, tab, escape, f1)",
            1: "Enter button (left, right, middle)",
            2: "Enter direction (up, down)",
            3: "Enter app path (e.g. notepad.exe, calc.exe)",
            4: "Enter hotkey (e.g. ctrl+c, win+shift+s, alt+tab)",
            5: "Enter action (up, down, mute)",
            6: "Enter text to type"
        }
        help_texts = {
            0: "◈ Keys: space, enter, tab, escape, backspace, f1-f12",
            1: "◈ Buttons: left, right, middle",
            2: "◈ Directions: up, down",
            3: "◈ Apps: notepad.exe, calc.exe, C:\\Program Files\\app.exe",
            4: "◈ Hotkeys: ctrl+c, ctrl+v, win+shift+s, alt+f4",
            5: "◈ Volume: up, down, mute",
            6: "◈ Any text that will be typed on gesture detection"
        }
        self.target_input.setPlaceholderText(placeholders.get(index, "Enter target"))
        self.help_label.setText(help_texts.get(index, "◈ Enter the action target"))

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            self.show_error("Gesture identifier is required!")
            self.name_input.setFocus()
            return

        if not self.target_input.text().strip():
            self.show_error("Action target is required!")
            self.target_input.setFocus()
            return

        self.accept()

    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ Validation Error")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"<p style='color: {COLORS['neon_orange']}; font-size: 14px;'>◈ {message}</p>")
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid {COLORS['holo_cyan']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(0, 255, 255, 0.15);
                color: {COLORS['holo_cyan']};
                border: 1px solid {COLORS['border_medium']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(0, 255, 255, 0.35);
            }}
        """)
        msg.exec()

    def get_data(self):
        """Return formatted gesture configuration data."""
        # Clean mode text (remove emoji)
        mode_text = self.mode_combo.currentText()
        mode_map = {
            "⬡  DESKTOP": "DESKTOP",
            "⬡  GAMING": "GAMING",
            "⬡  DRAW": "DRAW",
            "⬡  ALL MODES": "ALL"
        }
        mode = mode_map.get(mode_text, "DESKTOP")

        # Clean action text
        action_text = self.action_type_combo.currentText()
        action_map = {
            "◈  Key Press": "KEY_PRESS",
            "◈  Mouse Click": "MOUSE_CLICK",
            "◈  Scroll": "SCROLL",
            "◈  App Launch": "APP_LAUNCH",
            "◈  Keyboard Shortcut (Hotkey)": "HOTKEY",
            "◈  Volume Control": "VOLUME",
            "◈  Type Text": "TEXT"
        }
        action_type = action_map.get(action_text, "KEY_PRESS")

        return {
            "name": self.name_input.text().strip(),
            "mode": mode,
            "action_type": action_type,
            "target": self.target_input.text().strip()
        }

    def closeEvent(self, event):
        """Stop animations on close."""
        self.scanline_overlay.scanline_timer.stop()
        self.scanline_overlay.flicker_timer.stop()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ MODULE INFO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ GESTURE DIALOG MODULE V3.0 — HOLOGRAM EDITION ⬡                          ║
║  Futuristic Navy Blue Design • Cyberpunk Aesthetic                          ║
║  HUD Interface • Neon Glow • HOLOGRAM EFFECTS                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  HOLOGRAM FEATURES:                                                         ║
║  ▸ HologramScanline   - Animated scanline overlay with flicker              ║
║  ▸ HologramFrame      - Pulsing borders with glitch effects                 ║
║  ▸ HologramLabel      - Text with random glitch animation                   ║
║  ▸ HologramProgressBar - Animated glow progress indicator                   ║
║  ▸ HologramButton     - Hover-reactive buttons with neon glow               ║
║  ▸ Chromatic Aberration - RGB split effect on camera feed                   ║
║  ▸ Grid Overlay       - Holographic grid pattern on video                   ║
║  ▸ Color Shifting     - Dynamic holographic color animation                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)