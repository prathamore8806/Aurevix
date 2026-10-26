"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ GESTURES PAGE MODULE V3.0 — HOLOGRAM EDITION ⬡                           ║
║  Gesture Management • Custom Actions • Mode Selection                       ║
║  HUD Interface • Neon Glow • HOLOGRAM EFFECTS                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import random
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSlider, QMessageBox, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QDialogButtonBox, QFileDialog,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush

import config
from glowing_button import GlowingButton
from user_gestures import (
    save_gesture, load_gestures, get_gesture_count, delete_gesture, 
    update_gesture, get_trash_count, backup_gestures, import_gestures,
    restore_gesture, load_trash, permanent_delete_gesture, empty_trash
)
from gesture_dialog import GestureRecordDialog, GestureConfigDialog
import mode_manager


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
    'neon_green': '#00ff88',
    'neon_red': '#ff3366',
    'neon_orange': '#ff9500',
    'neon_yellow': '#ffcc00',
    'neon_purple': '#bf00ff',
    
    # Trash specific
    'trash_red': '#ff5252',
    'restore_green': '#00e676',
    
    # Text Colors
    'text_primary': '#e8f4f8',
    'text_secondary': '#8aa4b8',
    'text_muted': '#5a7a90',
}


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM SCANLINE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class HologramScanline(QWidget):
    """Animated holographic scanline overlay effect."""
    
    def __init__(self, parent=None, color_tint=(0, 212, 255)):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scanline_y = 0
        self.color_tint = color_tint
        
        self.scanline_timer = QTimer(self)
        self.scanline_timer.timeout.connect(self.update_scanline)
        self.scanline_timer.start(30)
        
    def update_scanline(self):
        self.scanline_y += 2
        if self.scanline_y > self.height():
            self.scanline_y = 0
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        r, g, b = self.color_tint
        
        # Draw horizontal scanlines
        painter.setPen(QPen(QColor(r, g, b, 12), 1))
        for y in range(0, self.height(), 3):
            painter.drawLine(0, y, self.width(), y)
        
        # Draw moving scanline
        gradient = QLinearGradient(0, self.scanline_y - 15, 0, self.scanline_y + 15)
        gradient.setColorAt(0, QColor(r, g, b, 0))
        gradient.setColorAt(0.5, QColor(r, g, b, 40))
        gradient.setColorAt(1, QColor(r, g, b, 0))
        
        painter.fillRect(0, self.scanline_y - 15, self.width(), 30, gradient)

    def stop_animation(self):
        self.scanline_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM FRAME
# ═══════════════════════════════════════════════════════════════════════════════

class HologramFrame(QFrame):
    """Frame with holographic border effects."""
    
    def __init__(self, color="cyan", parent=None):
        super().__init__(parent)
        self.border_phase = 0
        self.color = color
        
        self.border_timer = QTimer(self)
        self.border_timer.timeout.connect(self.animate_border)
        self.border_timer.start(50)
        
        self.update_style()
        
    def animate_border(self):
        self.border_phase += 0.1
        if self.border_phase > 2 * math.pi:
            self.border_phase = 0
        self.update_style()
        
    def update_style(self):
        pulse = int(40 + 20 * math.sin(self.border_phase))
        
        color_map = {
            "cyan": ("0, 212, 255", "0, 255, 255", "191, 0, 255"),
            "green": ("0, 230, 118", "0, 255, 136", "0, 200, 100"),
            "red": ("255, 82, 82", "255, 51, 102", "255, 100, 100"),
            "yellow": ("251, 191, 36", "255, 204, 0", "255, 170, 0"),
        }
        
        base_color, glow_color, alt_color = color_map.get(self.color, color_map["cyan"])
        
        self.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({base_color}, 0.05),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba({alt_color}, 0.03));
                border: 2px solid rgba({base_color}, {pulse / 100});
                border-radius: 16px;
            }}
        """)

    def stop_animation(self):
        self.border_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM LABEL
# ═══════════════════════════════════════════════════════════════════════════════

class HologramLabel(QLabel):
    """Label with holographic text glitch effects."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_text = text
        
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.maybe_glitch)
        self.glitch_timer.start(3000)
        
    def maybe_glitch(self):
        if random.random() < 0.2:
            self.apply_glitch()
            QTimer.singleShot(100, self.restore_text)
            
    def apply_glitch(self):
        glitch_chars = "!@#$%^&*<>[]{}|░▒▓"
        glitched = ""
        for char in self.original_text:
            if random.random() < 0.1:
                glitched += random.choice(glitch_chars)
            else:
                glitched += char
        self.setText(glitched)
        
    def restore_text(self):
        self.setText(self.original_text)
        
    def set_hologram_text(self, text):
        self.original_text = text
        self.setText(text)

    def stop_animation(self):
        self.glitch_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class HologramButton(QPushButton):
    """Button with holographic hover effects."""
    
    def __init__(self, text="", color="cyan", parent=None):
        super().__init__(text, parent)
        self.button_color = color
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
        color_map = {
            "cyan": ("0, 212, 255", COLORS['cyan_light']),
            "green": ("0, 230, 118", COLORS['restore_green']),
            "red": ("255, 82, 82", COLORS['trash_red']),
            "yellow": ("251, 191, 36", COLORS['neon_yellow']),
            "purple": ("168, 85, 247", COLORS['neon_purple']),
            "gray": ("139, 148, 158", COLORS['text_secondary']),
        }
        
        base_color, text_color = color_map.get(self.button_color, color_map["cyan"])
            
        if self.is_hovered:
            glow = int(40 + 20 * math.sin(self.hover_phase))
            bg_alpha = 0.35
            border_alpha = 0.9
        else:
            glow = 25
            bg_alpha = 0.15
            border_alpha = 0.5
            
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 12px 24px;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({base_color}, {bg_alpha}),
                    stop:0.5 rgba({base_color}, {bg_alpha * 0.5}),
                    stop:1 rgba({base_color}, {bg_alpha}));
                border: 2px solid rgba({base_color}, {border_alpha});
                color: {text_color};
                font-weight: 700;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
                min-width: 110px;
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
# ⬡ HOLOGRAM LIST WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class HologramListWidget(QListWidget):
    """List widget with holographic styling."""
    
    def __init__(self, color="cyan", parent=None):
        super().__init__(parent)
        self.list_color = color
        self.glow_phase = 0
        
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.animate_glow)
        self.glow_timer.start(80)
        
        self.update_style()
        
    def animate_glow(self):
        self.glow_phase += 0.1
        if self.glow_phase > 2 * math.pi:
            self.glow_phase = 0
        self.update_style()
        
    def update_style(self):
        pulse = int(30 + 15 * math.sin(self.glow_phase))
        
        color_map = {
            "cyan": ("0, 212, 255", "0, 200, 240"),
            "red": ("255, 82, 82", "255, 51, 102"),
            "green": ("0, 230, 118", "0, 200, 100"),
        }
        
        base_color, alt_color = color_map.get(self.list_color, color_map["cyan"])
        
        self.setStyleSheet(f"""
            QListWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({base_color}, 0.03),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba({alt_color}, 0.03));
                border: 2px solid rgba({base_color}, {pulse / 100});
                border-radius: 14px;
                padding: 10px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 14px 16px;
                border-radius: 10px;
                margin: 4px 2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({base_color}, 0.05),
                    stop:0.5 rgba(20, 30, 50, 0.8),
                    stop:1 rgba({base_color}, 0.05));
                border: 1px solid rgba({base_color}, 0.15);
            }}
            QListWidget::item:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({base_color}, 0.15),
                    stop:0.5 rgba(30, 40, 60, 0.9),
                    stop:1 rgba({base_color}, 0.15));
                border: 1px solid rgba({base_color}, 0.4);
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({base_color}, 0.25),
                    stop:0.5 rgba(40, 50, 70, 0.95),
                    stop:1 rgba({base_color}, 0.25));
                border: 2px solid rgba({base_color}, 0.6);
                color: white;
            }}
            QScrollBar:vertical {{
                background: rgba(10, 22, 40, 0.5);
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({base_color}, 0.8),
                    stop:0.5 rgba({alt_color}, 0.9),
                    stop:1 rgba({base_color}, 0.8));
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba({base_color}, 1.0);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
            }}
        """)

    def stop_animation(self):
        self.glow_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ GESTURE MANAGER DIALOG - HOLOGRAM EDITION
# ═══════════════════════════════════════════════════════════════════════════════

class GestureManagerDialog(QDialog):
    """Holographic dialog to manage saved gestures."""
    gestureDeleted = Signal(int)
    gestureToggled = Signal(int, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⬡ GESTURE MANAGER")
        self.setMinimumSize(750, 680)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['bg_darkest']},
                    stop:0.5 {COLORS['bg_dark']},
                    stop:1 {COLORS['bg_darkest']});
                border: 2px solid rgba(0, 212, 255, 0.4);
                border-radius: 16px;
            }}
        """)
        self._build_ui()
        self.load_gestures()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Add scanline overlay
        self.scanline_overlay = HologramScanline(self, (0, 212, 255))
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM HEADER
        # ═══════════════════════════════════════════════════════════════════
        header_card = HologramFrame("cyan")
        header_card.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 212, 255, 0.1),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba(0, 255, 255, 0.05));
                border: 2px solid rgba(0, 212, 255, 0.5);
                border-radius: 14px;
                padding: 18px;
            }}
        """)
        header_layout = QVBoxLayout(header_card)
        
        # Title row
        title_row = QHBoxLayout()
        
        icon_label = QLabel("⚙️")
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        title_row.addWidget(icon_label)
        
        title = HologramLabel("GESTURE MANAGEMENT")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {COLORS['holo_cyan']};
            background: transparent;
            letter-spacing: 2px;
        """)
        title_row.addWidget(title)
        title_row.addStretch()
        
        # Stats badge
        self.stats_badge = QLabel("◈ LOADING...")
        self.stats_badge.setStyleSheet(f"""
            background: rgba(0, 212, 255, 0.15);
            color: {COLORS['cyan_light']};
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid rgba(0, 212, 255, 0.4);
            letter-spacing: 1px;
        """)
        title_row.addWidget(self.stats_badge)
        
        header_layout.addLayout(title_row)
        
        # Subtitle
        subtitle = QLabel("◈ Enable/disable, edit, or delete your custom gestures")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
            padding-top: 4px;
        """)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_card)
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM GESTURE LIST
        # ═══════════════════════════════════════════════════════════════════
        list_container = HologramFrame("cyan")
        list_container.setStyleSheet(f"""
            HologramFrame {{
                background: rgba(10, 22, 40, 0.6);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 14px;
                padding: 8px;
            }}
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(8, 8, 8, 8)
        
        # Section header
        section_header = QLabel("▸ CUSTOM GESTURES")
        section_header.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {COLORS['cyan_primary']};
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 6px 12px;
            background: rgba(0, 212, 255, 0.08);
            border-left: 3px solid {COLORS['cyan_primary']};
            border-radius: 0 8px 8px 0;
        """)
        list_layout.addWidget(section_header)
        
        self.gesture_list = HologramListWidget("cyan")
        self.gesture_list.setMinimumHeight(320)
        list_layout.addWidget(self.gesture_list)
        
        layout.addWidget(list_container)
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM ACTION BUTTONS
        # ═══════════════════════════════════════════════════════════════════
        btn_card = HologramFrame("cyan")
        btn_card.setStyleSheet(f"""
            HologramFrame {{
                background: rgba(10, 22, 40, 0.5);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        btn_layout = QHBoxLayout(btn_card)
        btn_layout.setSpacing(12)
        
        # Toggle button
        self.toggle_btn = HologramButton("⏸ ENABLE/DISABLE", "yellow")
        self.toggle_btn.clicked.connect(self.toggle_gesture)
        self.toggle_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.toggle_btn)
        
        # Edit button
        self.edit_btn = HologramButton("✏️ EDIT", "cyan")
        self.edit_btn.clicked.connect(self.edit_gesture)
        self.edit_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = HologramButton("🗑 DELETE", "red")
        self.delete_btn.clicked.connect(self.delete_gesture)
        self.delete_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        # Close button
        self.close_btn = HologramButton("✖ CLOSE", "gray")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.close_btn)
        
        layout.addWidget(btn_card)
    
    def resizeEvent(self, event):
        """Update scanline overlay size on resize."""
        super().resizeEvent(event)
        self.scanline_overlay.setGeometry(self.rect())
        self.scanline_overlay.raise_()
        
    def load_gestures(self):
        """Load and display gestures with holographic styling."""
        self.gesture_list.clear()
        gestures = load_gestures()
        
        # Update stats badge
        if not gestures:
            self.stats_badge.setText("◈ EMPTY")
            self.stats_badge.setStyleSheet(f"""
                background: rgba(139, 148, 158, 0.15);
                color: {COLORS['text_muted']};
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid rgba(139, 148, 158, 0.4);
                letter-spacing: 1px;
            """)
            
            item = QListWidgetItem("📭 NO GESTURES YET — ADD SOME FROM THE MAIN PAGE!")
            item.setForeground(QColor(COLORS['text_muted']))
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.gesture_list.addItem(item)
            return
        
        active_count = sum(1 for g in gestures if g.get('enabled', True))
        self.stats_badge.setText(f"◈ {len(gestures)} TOTAL • {active_count} ACTIVE")
        self.stats_badge.setStyleSheet(f"""
            background: rgba(0, 212, 255, 0.15);
            color: {COLORS['cyan_light']};
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid rgba(0, 212, 255, 0.4);
            letter-spacing: 1px;
        """)
        
        for gesture in gestures:
            enabled = gesture.get('enabled', True)
            status = "✅ ACTIVE" if enabled else "⏸ DISABLED"
            mode = gesture.get('mode', 'ALL')
            action_type = gesture['action']['type']
            action = gesture['action']['target']
            created = gesture.get('created_at', 'Unknown')
            
            item_text = (
                f"⬡ {status} | {gesture['name'].upper()}\n"
                f"   ▸ Mode: {mode}  ▸ Type: {action_type}\n"
                f"   ▸ Target: {action}\n"
                f"   ◈ Created: {created}"
            )
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, gesture)
            
            if not enabled:
                item.setForeground(QColor(COLORS['text_muted']))
                
            self.gesture_list.addItem(item)
    
    def _show_hologram_message(self, title, message, msg_type="info"):
        """Show holographic styled message box."""
        msg = QMessageBox(self)
        msg.setWindowTitle(f"⬡ {title}")
        
        if msg_type == "warning":
            msg.setIcon(QMessageBox.Warning)
            color = COLORS['neon_orange']
        elif msg_type == "error":
            msg.setIcon(QMessageBox.Critical)
            color = COLORS['neon_red']
        elif msg_type == "question":
            msg.setIcon(QMessageBox.Question)
            color = COLORS['holo_cyan']
        else:
            msg.setIcon(QMessageBox.Information)
            color = COLORS['neon_green']
        
        msg.setText(f"<p style='color: {color}; font-size: 14px;'>{message}</p>")
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid rgba(0, 212, 255, 0.5);
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(0, 212, 255, 0.15);
                color: {COLORS['holo_cyan']};
                border: 1px solid rgba(0, 212, 255, 0.4);
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.35);
                color: white;
            }}
        """)
        return msg
    
    def toggle_gesture(self):
        """Toggle gesture enabled/disabled state."""
        current = self.gesture_list.currentItem()
        if not current or not current.data(Qt.UserRole):
            msg = self._show_hologram_message(
                "Selection Required",
                "◈ Please select a gesture!",
                "warning"
            )
            msg.exec()
            return
            
        gesture = current.data(Qt.UserRole)
        gesture['enabled'] = not gesture.get('enabled', True)
        update_gesture(gesture)
        
        status = "ENABLED" if gesture['enabled'] else "DISABLED"
        self.gestureToggled.emit(gesture['id'], gesture['enabled'])
        self.load_gestures()
        
        msg = self._show_hologram_message(
            "Status Updated",
            f"✓ Gesture '<b>{gesture['name']}</b>' {status}!",
            "info"
        )
        msg.exec()
        
    def edit_gesture(self):
        """Edit selected gesture."""
        current = self.gesture_list.currentItem()
        if not current or not current.data(Qt.UserRole):
            msg = self._show_hologram_message(
                "Selection Required",
                "◈ Please select a gesture to edit!",
                "warning"
            )
            msg.exec()
            return
            
        gesture = current.data(Qt.UserRole)
        dialog = GestureConfigDialog(self)
        dialog.name_input.setText(gesture['name'])
        
        # Set mode combo
        mode_map = {"DESKTOP": "⬡  DESKTOP", "GAMING": "⬡  GAMING", "DRAW": "⬡  DRAW", "ALL": "⬡  ALL MODES"}
        dialog.mode_combo.setCurrentText(mode_map.get(gesture.get('mode', 'ALL'), "⬡  ALL MODES"))
        
        # Set action type combo
        action_map = {
            "KEY_PRESS": "◈  Key Press",
            "MOUSE_CLICK": "◈  Mouse Click",
            "SCROLL": "◈  Scroll",
            "APP_LAUNCH": "◈  App Launch",
            "HOTKEY": "◈  Keyboard Shortcut (Hotkey)",
            "VOLUME": "◈  Volume Control",
            "TEXT": "◈  Type Text"
        }
        dialog.action_type_combo.setCurrentText(action_map.get(gesture['action']['type'], "◈  Key Press"))
        
        dialog.target_input.setText(gesture['action']['target'])
        
        if dialog.exec():
            data = dialog.get_data()
            gesture['name'] = data['name']
            gesture['mode'] = data['mode']
            gesture['action'] = {
                'type': data['action_type'],
                'target': data['target']
            }
            update_gesture(gesture)
            self.load_gestures()
            
            msg = self._show_hologram_message(
                "Update Complete",
                f"✓ Gesture '<b>{data['name']}</b>' updated!",
                "info"
            )
            msg.exec()
    
    def delete_gesture(self):
        """Delete selected gesture (move to trash)."""
        current = self.gesture_list.currentItem()
        if not current or not current.data(Qt.UserRole):
            msg = self._show_hologram_message(
                "Selection Required",
                "◈ Please select a gesture to delete!",
                "warning"
            )
            msg.exec()
            return
            
        gesture = current.data(Qt.UserRole)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ Confirm Delete")
        msg.setIcon(QMessageBox.Question)
        msg.setText(
            f"<p style='color: {COLORS['holo_cyan']}; font-size: 14px;'>"
            f"◈ Move '<b>{gesture['name']}</b>' to trash?</p>"
            f"<p style='color: {COLORS['text_secondary']}; font-size: 12px;'>"
            f"You can restore it later from the trash.</p>"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
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
                background: rgba(0, 212, 255, 0.15);
                color: {COLORS['holo_cyan']};
                border: 1px solid rgba(0, 212, 255, 0.4);
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.35);
            }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            delete_gesture(gesture['id'])
            self.gestureDeleted.emit(gesture['id'])
            self.load_gestures()
            
            success_msg = self._show_hologram_message(
                "Moved to Trash",
                "🗑️ Gesture moved to trash successfully!",
                "info"
            )
            success_msg.exec()

    def closeEvent(self, event):
        """Stop animations on close."""
        self.scanline_overlay.stop_animation()
        self.gesture_list.stop_animation()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ TRASH DIALOG - HOLOGRAM EDITION
# ═══════════════════════════════════════════════════════════════════════════════

class TrashDialog(QDialog):
    """Holographic dialog to manage deleted gestures."""
    gestureRestored = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⬡ GESTURE TRASH")
        self.setMinimumSize(700, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['bg_darkest']},
                    stop:0.5 {COLORS['bg_dark']},
                    stop:1 {COLORS['bg_darkest']});
                border: 2px solid rgba(255, 82, 82, 0.4);
                border-radius: 16px;
            }}
        """)
        self._build_ui()
        self.load_trash()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Add scanline overlay
        self.scanline_overlay = HologramScanline(self, (255, 82, 82))
        
        # Header
        header_card = HologramFrame("red")
        header_card.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 82, 82, 0.1),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba(255, 51, 102, 0.05));
                border: 2px solid rgba(255, 82, 82, 0.5);
                border-radius: 14px;
                padding: 18px;
            }}
        """)
        header_layout = QVBoxLayout(header_card)
        
        title_row = QHBoxLayout()
        icon_label = QLabel("🗑️")
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        title_row.addWidget(icon_label)
        
        title = HologramLabel("GESTURE TRASH SYSTEM")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {COLORS['trash_red']};
            background: transparent;
            letter-spacing: 2px;
        """)
        title_row.addWidget(title)
        title_row.addStretch()
        
        self.stats_badge = QLabel("◈ LOADING...")
        self.stats_badge.setStyleSheet(f"""
            background: rgba(255, 82, 82, 0.15);
            color: {COLORS['trash_red']};
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid rgba(255, 82, 82, 0.4);
            letter-spacing: 1px;
        """)
        title_row.addWidget(self.stats_badge)
        
        header_layout.addLayout(title_row)
        
        subtitle = QLabel("◈ Restore or permanently delete your trashed gestures")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
            padding-top: 4px;
        """)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_card)
        
        # List
        list_container = HologramFrame("red")
        list_container.setStyleSheet(f"""
            HologramFrame {{
                background: rgba(10, 22, 40, 0.6);
                border: 1px solid rgba(255, 82, 82, 0.3);
                border-radius: 14px;
                padding: 8px;
            }}
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(8, 8, 8, 8)
        
        section_header = QLabel("▸ DELETED ITEMS")
        section_header.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {COLORS['trash_red']};
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 6px 12px;
            background: rgba(255, 82, 82, 0.08);
            border-left: 3px solid {COLORS['trash_red']};
            border-radius: 0 8px 8px 0;
        """)
        list_layout.addWidget(section_header)
        
        self.trash_list = HologramListWidget("red")
        self.trash_list.setMinimumHeight(280)
        list_layout.addWidget(self.trash_list)
        
        layout.addWidget(list_container)
        
        # Buttons
        btn_card = HologramFrame("red")
        btn_card.setStyleSheet(f"""
            HologramFrame {{
                background: rgba(10, 22, 40, 0.5);
                border: 1px solid rgba(255, 82, 82, 0.2);
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        btn_layout = QHBoxLayout(btn_card)
        btn_layout.setSpacing(12)
        
        self.restore_btn = HologramButton("♻️ RESTORE", "green")
        self.restore_btn.clicked.connect(self.restore_selected)
        self.restore_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.restore_btn)
        
        self.delete_btn = HologramButton("🗑️ DELETE FOREVER", "red")
        self.delete_btn.clicked.connect(self.delete_selected_permanently)
        self.delete_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.delete_btn)
        
        self.empty_btn = HologramButton("🧹 EMPTY TRASH", "yellow")
        self.empty_btn.clicked.connect(self.empty_trash_action)
        self.empty_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.empty_btn)
        
        btn_layout.addStretch()
        
        self.close_btn = HologramButton("✖ CLOSE", "cyan")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setMinimumHeight(48)
        btn_layout.addWidget(self.close_btn)
        
        layout.addWidget(btn_card)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scanline_overlay.setGeometry(self.rect())
        self.scanline_overlay.raise_()
        
    def load_trash(self):
        self.trash_list.clear()
        trash = load_trash()
        
        if not trash:
            self.stats_badge.setText("◈ EMPTY")
            self.stats_badge.setStyleSheet(f"""
                background: rgba(0, 230, 118, 0.15);
                color: {COLORS['neon_green']};
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid rgba(0, 230, 118, 0.4);
                letter-spacing: 1px;
            """)
            
            item = QListWidgetItem("🎉 TRASH IS EMPTY — NO DELETED GESTURES")
            item.setForeground(QColor(COLORS['neon_green']))
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.trash_list.addItem(item)
            return
        
        self.stats_badge.setText(f"◈ {len(trash)} ITEM{'S' if len(trash) != 1 else ''}")
        self.stats_badge.setStyleSheet(f"""
            background: rgba(255, 82, 82, 0.15);
            color: {COLORS['trash_red']};
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid rgba(255, 82, 82, 0.4);
            letter-spacing: 1px;
        """)
        
        for gesture in trash:
            deleted_at = gesture.get('deleted_at', 'Unknown')
            mode = gesture.get('mode', 'ALL')
            action = gesture['action']['target']
            action_type = gesture['action'].get('type', 'KEY_PRESS')
            
            item_text = (
                f"⬡ {gesture['name'].upper()}\n"
                f"   ▸ Mode: {mode}  ▸ Type: {action_type}\n"
                f"   ▸ Target: {action}\n"
                f"   ◈ Deleted: {deleted_at}"
            )
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, gesture)
            self.trash_list.addItem(item)
    
    def _show_hologram_message(self, title, message, msg_type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"⬡ {title}")
        
        if msg_type == "warning":
            msg.setIcon(QMessageBox.Warning)
            color = COLORS['neon_orange']
        else:
            msg.setIcon(QMessageBox.Information)
            color = COLORS['neon_green']
        
        msg.setText(f"<p style='color: {color}; font-size: 14px;'>{message}</p>")
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid rgba(255, 82, 82, 0.5);
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(0, 212, 255, 0.15);
                color: {COLORS['holo_cyan']};
                border: 1px solid rgba(0, 212, 255, 0.4);
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.35);
            }}
        """)
        return msg
    
    def restore_selected(self):
        current = self.trash_list.currentItem()
        if not current or not current.data(Qt.UserRole):
            msg = self._show_hologram_message("Selection Required", "◈ Please select a gesture to restore!", "warning")
            msg.exec()
            return
        
        gesture = current.data(Qt.UserRole)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ Confirm Restore")
        msg.setIcon(QMessageBox.Question)
        msg.setText(f"<p style='color: {COLORS['holo_cyan']};'>◈ Restore '<b>{gesture['name']}</b>'?</p>")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {COLORS['bg_darkest']}; border: 2px solid {COLORS['holo_cyan']}; }}
            QMessageBox QLabel {{ color: {COLORS['text_primary']}; }}
            QPushButton {{ padding: 10px 24px; border-radius: 8px; background: rgba(0, 212, 255, 0.15);
                color: {COLORS['holo_cyan']}; border: 1px solid rgba(0, 212, 255, 0.4); font-weight: 600; }}
            QPushButton:hover {{ background: rgba(0, 212, 255, 0.35); }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            if restore_gesture(gesture['id']):
                self.gestureRestored.emit(gesture['id'])
                self.load_trash()
                success_msg = self._show_hologram_message("Restore Complete", f"✓ Gesture '<b>{gesture['name']}</b>' restored!")
                success_msg.exec()
    
    def delete_selected_permanently(self):
        current = self.trash_list.currentItem()
        if not current or not current.data(Qt.UserRole):
            msg = self._show_hologram_message("Selection Required", "◈ Please select a gesture to delete!", "warning")
            msg.exec()
            return
        
        gesture = current.data(Qt.UserRole)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ PERMANENT DELETE")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"<h3 style='color: {COLORS['neon_red']};'>⚠ PERMANENT DELETION</h3>"
            f"<p style='color: {COLORS['text_primary']};'>Delete '<b>{gesture['name']}</b>' forever?</p>"
            f"<p style='color: {COLORS['neon_orange']};'>◈ THIS CANNOT BE UNDONE!</p>"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {COLORS['bg_darkest']}; border: 2px solid {COLORS['neon_red']}; }}
            QMessageBox QLabel {{ color: {COLORS['text_primary']}; }}
            QPushButton {{ padding: 10px 24px; border-radius: 8px; background: rgba(255, 82, 82, 0.15);
                color: {COLORS['trash_red']}; border: 1px solid rgba(255, 82, 82, 0.4); font-weight: 600; }}
            QPushButton:hover {{ background: rgba(255, 82, 82, 0.35); color: white; }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            if permanent_delete_gesture(gesture['id']):
                self.load_trash()
                success_msg = self._show_hologram_message("Deleted", "🗑️ Gesture permanently deleted!")
                success_msg.exec()
    
    def empty_trash_action(self):
        trash = load_trash()
        if not trash:
            msg = self._show_hologram_message("Trash Empty", "◈ Trash is already empty!")
            msg.exec()
            return
        
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ EMPTY TRASH")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"<h3 style='color: {COLORS['neon_red']};'>⚠ EMPTY ALL TRASH</h3>"
            f"<p style='color: {COLORS['text_primary']};'>Permanently delete all <b>{len(trash)}</b> gesture(s)?</p>"
            f"<p style='color: {COLORS['neon_orange']};'>◈ THIS CANNOT BE UNDONE!</p>"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {COLORS['bg_darkest']}; border: 2px solid {COLORS['neon_orange']}; }}
            QMessageBox QLabel {{ color: {COLORS['text_primary']}; }}
            QPushButton {{ padding: 10px 24px; border-radius: 8px; background: rgba(251, 191, 36, 0.15);
                color: {COLORS['neon_yellow']}; border: 1px solid rgba(251, 191, 36, 0.4); font-weight: 600; }}
            QPushButton:hover {{ background: rgba(251, 191, 36, 0.35); color: white; }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            if empty_trash():
                self.load_trash()
                success_msg = self._show_hologram_message("Trash Emptied", "🧹 All gestures permanently deleted!")
                success_msg.exec()

    def closeEvent(self, event):
        self.scanline_overlay.stop_animation()
        self.trash_list.stop_animation()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ GESTURES PAGE - MAIN WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class GesturesPage(QWidget):
    """Main gestures page widget with holographic styling."""
    
    modeChanged = Signal(str)
    gestureAdded = Signal(dict)
    gestureDeleted = Signal(int)
    gestureToggled = Signal(int, bool)
    trackingPauseRequested = Signal()
    trackingResumeRequested = Signal()
    
    def __init__(self, draw_canvas=None, parent=None):
        super().__init__(parent)
        self.draw_canvas = draw_canvas
        self._parent = parent
        self._was_tracking = False
        self._build_ui()
        self.update_gesture_list()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        self.title_label = QLabel("⬡ GESTURE MAPPING SYSTEM")
        self.title_label.setObjectName("title")
        self.title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {COLORS['holo_cyan']};
            letter-spacing: 2px;
            padding: 10px 0;
        """)
        layout.addWidget(self.title_label)

        # ═══════════════════════════════════════════════════════════════════
        # ✅ First row of buttons - ALL stored as self.
        # ═══════════════════════════════════════════════════════════════════
        btn_row = QHBoxLayout()
        
        self.add_btn = GlowingButton("➕ ADD NEW GESTURE", glow_color="#00e676")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 14px 24px;
                border-radius: 14px;
                background: rgba(0, 230, 118, 0.15);
                border: 2px solid rgba(0, 230, 118, 0.4);
                color: white;
                font-weight: bold;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: rgba(0, 230, 118, 0.3);
                border: 2px solid rgba(0, 230, 118, 0.6);
            }}
        """)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_gesture_clicked)
        btn_row.addWidget(self.add_btn)

        # ✅ MANAGE BUTTON - Fixed
        self.manage_btn = GlowingButton("⚙️ MANAGE", glow_color="#fbbf24")
        self.manage_btn.setObjectName("modeBtn")
        self.manage_btn.setCursor(Qt.PointingHandCursor)
        self.manage_btn.clicked.connect(self.manage_gestures)
        btn_row.addWidget(self.manage_btn)

        # ✅ TRASH BUTTON - Fixed
        self.trash_btn = GlowingButton("🗑️ TRASH", glow_color="#ff5252")
        self.trash_btn.setObjectName("modeBtn")
        self.trash_btn.setCursor(Qt.PointingHandCursor)
        self.trash_btn.clicked.connect(self.open_trash)
        btn_row.addWidget(self.trash_btn)

        # ✅ CLEAR BUTTON - Fixed
        self.clear_btn = GlowingButton("🧹 CLEAR CANVAS", glow_color="#a855f7")
        self.clear_btn.setObjectName("modeBtn")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear_canvas)
        btn_row.addWidget(self.clear_btn)

        layout.addLayout(btn_row)

        # ═══════════════════════════════════════════════════════════════════
        # ✅ Second row - Import/Export
        # ═══════════════════════════════════════════════════════════════════
        btn_row2 = QHBoxLayout()
        
        self.export_btn = GlowingButton("📤 EXPORT", glow_color="#00d4ff")
        self.export_btn.setObjectName("modeBtn")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_gestures)
        btn_row2.addWidget(self.export_btn)
        
        self.import_btn = GlowingButton("📥 IMPORT", glow_color="#00d4ff")
        self.import_btn.setObjectName("modeBtn")
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.clicked.connect(self.import_gestures)
        btn_row2.addWidget(self.import_btn)
        
        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        # ═══════════════════════════════════════════════════════════════════
        # Stats row
        # ═══════════════════════════════════════════════════════════════════
        stats_layout = QHBoxLayout()
        
        self.gesture_count_label = QLabel(f"◈ TOTAL: {get_gesture_count()}")
        self.gesture_count_label.setStyleSheet(f"""
            color: {COLORS['holo_cyan']};
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        
        self.active_gestures_label = QLabel("◈ ACTIVE: 0")
        self.active_gestures_label.setStyleSheet(f"""
            color: {COLORS['neon_green']};
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        
        self.trash_count_label = QLabel(f"◈ TRASH: {get_trash_count()}")
        self.trash_count_label.setStyleSheet(f"""
            color: {COLORS['trash_red']};
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        
        stats_layout.addWidget(self.gesture_count_label)
        stats_layout.addWidget(self.active_gestures_label)
        stats_layout.addWidget(self.trash_count_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # ═══════════════════════════════════════════════════════════════════
        # Sliders
        # ═══════════════════════════════════════════════════════════════════
        row1 = QHBoxLayout()
        row1.addWidget(self.card_slider("Gesture Sensitivity", 1, 10, config.gesture_sensitivity,
                                         lambda v: setattr(config, "gesture_sensitivity", v)))
        row1.addWidget(self.card_slider("Match Threshold %", 50, 100, 
                                        getattr(config, 'gesture_match_threshold', 75),
                                        lambda v: setattr(config, "gesture_match_threshold", v)))
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self.card_slider("Mouse Speed", 1, 20, config.mouse_speed,
                                         lambda v: setattr(config, "mouse_speed", v)))
        row2.addWidget(self.card_slider("Gesture Cooldown (ms)", 100, 2000, 
                                        getattr(config, 'gesture_cooldown', 500),
                                        lambda v: setattr(config, "gesture_cooldown", v)))
        layout.addLayout(row2)

        # ═══════════════════════════════════════════════════════════════════
        # Info cards
        # ═══════════════════════════════════════════════════════════════════
        row3 = QHBoxLayout()
        row3.addWidget(self.glass_card("Built-in Desktop", "☝️ Index → Cursor\n✊ Fist → Click\n✌️ Two → Scroll"))
        row3.addWidget(self.glass_card("Built-in Gaming", "☝️ Dir → WASD\n🖐 Open → Jump\n✊ Fist → Sprint"))
        row3.addWidget(self.glass_card("Custom Gestures", "📝 Record your own\n⚙️ Configure actions\n🎯 Real-time execution"))
        layout.addLayout(row3)

        # Mode selector
        row4 = QHBoxLayout()
        row4.addWidget(self.card_mode_selector())
        layout.addLayout(row4)

        layout.addStretch()

    # ═══════════════════════════════════════════════════════════════════════════
    # ⬡ ACTION METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _clear_canvas(self):
        """Clear the drawing canvas."""
        print("🧹 Clear canvas clicked")
        if self.draw_canvas:
            self.draw_canvas.clear()

    def _pause_main_tracking(self):
        """Pause main tracking for recording."""
        self._was_tracking = False
        if self._parent and hasattr(self._parent, '_tracking_active'):
            self._was_tracking = self._parent._tracking_active
            if self._was_tracking:
                print("⏸️ Pausing main tracking...")
                self._parent._stop_tracking()
                QTimer.singleShot(300, lambda: None)
                return True
        return False
    
    def _resume_main_tracking(self):
        """Resume main tracking after recording."""
        if self._was_tracking and self._parent and hasattr(self._parent, '_start_tracking'):
            print("▶️ Resuming main tracking...")
            QTimer.singleShot(500, self._parent._start_tracking)
            self._was_tracking = False

    def add_gesture_clicked(self):
        """Show recording confirmation dialog."""
        print("➕ Add gesture clicked")
        
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ Record New Gesture")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            f"<h2 style='color: {COLORS['holo_cyan']};'>🖐 RECORD NEW GESTURE</h2>"
            f"<p style='color: {COLORS['text_secondary']};'>"
            f"Camera will open for <b style='color: {COLORS['neon_yellow']};'>5 seconds</b>.<br>"
            f"Perform your gesture clearly and hold it steady.</p>"
            f"<p style='color: {COLORS['neon_orange']};'>⚠ Main tracking will pause during recording.</p>"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid {COLORS['holo_cyan']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
                min-width: 380px;
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 10px;
                font-weight: bold;
                min-width: 100px;
                background: rgba(0, 212, 255, 0.15);
                color: white;
                border: 1px solid rgba(0, 212, 255, 0.3);
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.35);
            }}
        """)
        
        if msg.exec() == QMessageBox.Ok:
            self._pause_main_tracking()
            QTimer.singleShot(400, self.open_recording_dialog)

    def open_recording_dialog(self):
        """Open the gesture recording dialog."""
        print("📷 Opening recording dialog")
        dialog = GestureRecordDialog(self, config.camera_index, 5)
        result = dialog.exec()
        
        if hasattr(dialog, 'cleanup'):
            dialog.cleanup()
        elif hasattr(dialog, 'cap') and dialog.cap is not None:
            dialog.cap.release()
            dialog.cap = None
        
        if result:
            data = dialog.get_recorded_data()
            if data and len(data) > 0:
                self.configure_gesture(data)
        
        self._resume_main_tracking()

    def configure_gesture(self, recorded_data):
        """Configure recorded gesture."""
        print("⚙️ Configuring gesture")
        dialog = GestureConfigDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            gesture = {
                "id": int(time.time() * 1000),
                "name": data["name"],
                "mode": data["mode"],
                "action": {
                    "type": data["action_type"],
                    "target": data["target"]
                },
                "signature": recorded_data,
                "points_count": len(recorded_data),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "enabled": True
            }
            save_gesture(gesture)
            self.update_gesture_list()
            self.gestureAdded.emit(gesture)
            
            QMessageBox.information(
                self, 
                "⬡ Gesture Saved",
                f"✓ Gesture '{data['name']}' saved!\n\n"
                f"▸ Mode: {data['mode']}\n"
                f"▸ Action: {data['action_type']} → {data['target']}"
            )

    def manage_gestures(self):
        """Open gesture management dialog."""
        print("⚙️ Manage gestures clicked")
        
        try:
            dialog = GestureManagerDialog(self)
            dialog.gestureDeleted.connect(self.on_gesture_deleted)
            dialog.gestureToggled.connect(self.on_gesture_toggled)
            dialog.exec()
            self.update_gesture_list()
        except Exception as e:
            print(f"❌ Error opening manage dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to open manager:\n{e}")

    def open_trash(self):
        """Open trash dialog."""
        print("🗑️ Trash clicked")
        
        try:
            dialog = TrashDialog(self)
            dialog.gestureRestored.connect(self.on_gesture_restored)
            dialog.exec()
            self.update_gesture_list()
        except Exception as e:
            print(f"❌ Error opening trash dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to open trash:\n{e}")

    def on_gesture_deleted(self, gesture_id):
        self.gestureDeleted.emit(gesture_id)
        self.update_gesture_list()

    def on_gesture_toggled(self, gesture_id, enabled):
        self.gestureToggled.emit(gesture_id, enabled)
        self.update_gesture_list()

    def on_gesture_restored(self, gesture_id):
        self.update_gesture_list()

    def export_gestures(self):
        """Export gestures to file."""
        print("📤 Export clicked")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "⬡ Export Gestures",
            f"gestures_backup_{int(time.time())}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            result = backup_gestures(file_path)
            if result:
                QMessageBox.information(self, "⬡ Export Success", f"📤 Exported to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "❌ Failed to export!")

    def import_gestures(self):
        """Import gestures from file."""
        print("📥 Import clicked")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "⬡ Import Gestures",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            count = import_gestures(file_path)
            if count > 0:
                self.update_gesture_list()
                QMessageBox.information(self, "⬡ Import Success", f"📥 Imported {count} gesture(s)!")
            elif count == 0:
                QMessageBox.information(self, "Info", "ℹ️ No new gestures (duplicates skipped)")
            else:
                QMessageBox.critical(self, "Error", "❌ Failed to import!")

    def update_gesture_list(self):
        """Update all gesture counts."""
        total = get_gesture_count()
        gestures = load_gestures()
        active = sum(1 for g in gestures if g.get('enabled', True))
        trash = get_trash_count()
        
        self.gesture_count_label.setText(f"◈ TOTAL: {total}")
        self.active_gestures_label.setText(f"◈ ACTIVE: {active}")
        self.trash_count_label.setText(f"◈ TRASH: {trash}")

    # ═══════════════════════════════════════════════════════════════════════════
    # ⬡ UI HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def glass_card(self, title, text):
        """Create a holographic info card."""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 212, 255, 0.05),
                    stop:0.5 rgba(10, 22, 40, 0.9),
                    stop:1 rgba(191, 0, 255, 0.03));
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        
        lay = QVBoxLayout(card)
        t = QLabel(title)
        t.setStyleSheet(f"color: {COLORS['holo_cyan']}; font-size: 14px; font-weight: 700; letter-spacing: 1px;")
        lay.addWidget(t)
        
        c = QLabel(text)
        c.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        lay.addWidget(c)
        return card

    def card_slider(self, title, minv, maxv, value, on_change=None):
        """Create a holographic slider card."""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 212, 255, 0.05),
                    stop:0.5 rgba(10, 22, 40, 0.9),
                    stop:1 rgba(191, 0, 255, 0.03));
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        label = QLabel(title)
        label.setStyleSheet(f"color: {COLORS['holo_cyan']}; font-size: 14px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minv, maxv)
        slider.setValue(value)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid rgba(0, 212, 255, 0.3);
                height: 8px;
                background: rgba(10, 22, 40, 0.8);
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['holo_cyan']};
                border: 1px solid rgba(0, 255, 255, 0.6);
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['holo_cyan']}, stop:1 rgba(0, 212, 255, 0.5));
                border-radius: 4px;
            }}
        """)
        layout.addWidget(slider)
        
        val = QLabel(str(value))
        val.setAlignment(Qt.AlignRight)
        val.setStyleSheet(f"color: {COLORS['holo_cyan']}; font-weight: bold; font-size: 14px;")
        layout.addWidget(val)

        def handle(v):
            val.setText(str(v))
            if on_change:
                on_change(v)
        slider.valueChanged.connect(handle)
        return card

    def card_mode_selector(self):
        """Create holographic mode selector card."""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 212, 255, 0.05),
                    stop:0.5 rgba(10, 22, 40, 0.9),
                    stop:1 rgba(191, 0, 255, 0.03));
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        title = QLabel("⬡ MODE SELECTOR")
        title.setStyleSheet(f"color: {COLORS['holo_cyan']}; font-size: 14px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(title)

        btn_row = QHBoxLayout()
        
        self.desktop_btn = GlowingButton("🖥 DESKTOP", glow_color="#00d4ff")
        self.desktop_btn.setCheckable(True)
        self.desktop_btn.setChecked(mode_manager.mode == "DESKTOP")
        self.desktop_btn.setObjectName("modeBtn")
        self.desktop_btn.setCursor(Qt.PointingHandCursor)
        self.desktop_btn.clicked.connect(lambda: self.set_mode("DESKTOP"))

        self.gaming_btn = GlowingButton("🎮 GAMING", glow_color="#ff6b35")
        self.gaming_btn.setCheckable(True)
        self.gaming_btn.setChecked(mode_manager.mode == "GAMING")
        self.gaming_btn.setObjectName("modeBtn")
        self.gaming_btn.setCursor(Qt.PointingHandCursor)
        self.gaming_btn.clicked.connect(lambda: self.set_mode("GAMING"))

        self.draw_btn = GlowingButton("✏️ DRAW", glow_color="#a855f7")
        self.draw_btn.setCheckable(True)
        self.draw_btn.setChecked(mode_manager.mode == "DRAW")
        self.draw_btn.setObjectName("modeBtn")
        self.draw_btn.setCursor(Qt.PointingHandCursor)
        self.draw_btn.clicked.connect(lambda: self.set_mode("DRAW"))

        btn_row.addWidget(self.desktop_btn)
        btn_row.addWidget(self.gaming_btn)
        btn_row.addWidget(self.draw_btn)
        layout.addLayout(btn_row)
        return card

    def set_mode(self, mode):
        """Set active mode."""
        print(f"🎯 Mode: {mode}")
        self.desktop_btn.setChecked(mode == "DESKTOP")
        self.gaming_btn.setChecked(mode == "GAMING")
        self.draw_btn.setChecked(mode == "DRAW")
        self.modeChanged.emit(mode)

    def update_mode_buttons(self, mode):
        """Update mode button states."""
        self.desktop_btn.setChecked(mode == "DESKTOP")
        self.gaming_btn.setChecked(mode == "GAMING")
        self.draw_btn.setChecked(mode == "DRAW")


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ MODULE INFO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ GESTURES PAGE MODULE V3.0 — HOLOGRAM EDITION ⬡                           ║
║  All dialogs and buttons fully functional!                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)