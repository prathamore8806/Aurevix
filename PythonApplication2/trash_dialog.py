"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ TRASH DIALOG MODULE V3.0 — HOLOGRAM EDITION ⬡                            ║
║  Futuristic Navy Blue Design • Cyberpunk Aesthetic                          ║
║  HUD Interface • Neon Glow • HOLOGRAM EFFECTS                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import random
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QFrame, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen
from user_gestures import load_trash, restore_gesture, permanent_delete_gesture, empty_trash


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
    
    # Neon Colors
    'neon_green': '#00ff88',
    'neon_red': '#ff3366',
    'neon_orange': '#ff9500',
    'neon_yellow': '#ffcc00',
    'neon_purple': '#bf00ff',
    
    # Trash specific
    'trash_red': '#ff5252',
    'trash_red_light': '#ff7b7b',
    'restore_green': '#00e676',
    
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
        self.scanline_timer.start(30)
        
        # Flicker effect timer
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self.update_flicker)
        self.flicker_timer.start(100)
        
    def update_scanline(self):
        self.scanline_y += 2
        if self.scanline_y > self.height():
            self.scanline_y = 0
        self.update()
        
    def update_flicker(self):
        self.flicker_alpha = random.uniform(0.9, 1.0)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw horizontal scanlines (red tint for trash)
        painter.setPen(QPen(QColor(255, 82, 82, 12), 1))
        for y in range(0, self.height(), 3):
            painter.drawLine(0, y, self.width(), y)
        
        # Draw moving scanline
        gradient = QLinearGradient(0, self.scanline_y - 15, 0, self.scanline_y + 15)
        gradient.setColorAt(0, QColor(255, 82, 82, 0))
        gradient.setColorAt(0.5, QColor(255, 82, 82, 40))
        gradient.setColorAt(1, QColor(255, 82, 82, 0))
        
        painter.fillRect(0, self.scanline_y - 15, self.width(), 30, gradient)

    def stop_animation(self):
        self.scanline_timer.stop()
        self.flicker_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM FRAME
# ═══════════════════════════════════════════════════════════════════════════════

class HologramFrame(QFrame):
    """Frame with holographic border effects and animations."""
    
    def __init__(self, color="cyan", parent=None):
        super().__init__(parent)
        self.border_phase = 0
        self.glitch_offset = 0
        self.color = color
        
        # Border animation timer
        self.border_timer = QTimer(self)
        self.border_timer.timeout.connect(self.animate_border)
        self.border_timer.start(50)
        
        # Random glitch timer
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.trigger_glitch)
        self.glitch_timer.start(4000)
        
        self.update_style()
        
    def animate_border(self):
        self.border_phase += 0.1
        if self.border_phase > 2 * math.pi:
            self.border_phase = 0
        self.update_style()
        
    def trigger_glitch(self):
        self.glitch_offset = random.randint(-2, 2)
        QTimer.singleShot(80, self.reset_glitch)
        
    def reset_glitch(self):
        self.glitch_offset = 0
        self.update_style()
        
    def update_style(self):
        pulse = int(40 + 20 * math.sin(self.border_phase))
        
        if self.color == "red":
            color_str = f"rgba(255, 82, 82, {pulse / 100})"
            bg_color1 = "rgba(255, 82, 82, 0.05)"
            bg_color2 = "rgba(255, 51, 102, 0.03)"
        else:
            color_str = f"rgba(0, 255, 255, {pulse / 100})"
            bg_color1 = "rgba(0, 255, 255, 0.03)"
            bg_color2 = "rgba(191, 0, 255, 0.03)"
        
        self.setStyleSheet(f"""
            HologramFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_color1},
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 {bg_color2});
                border: 2px solid {color_str};
                border-radius: 16px;
                margin-left: {self.glitch_offset}px;
            }}
        """)

    def stop_animation(self):
        self.border_timer.stop()
        self.glitch_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM LABEL
# ═══════════════════════════════════════════════════════════════════════════════

class HologramLabel(QLabel):
    """Label with holographic text effects."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.glitch_active = False
        
        # Glitch timer
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.maybe_glitch)
        self.glitch_timer.start(3000)
        
    def maybe_glitch(self):
        if random.random() < 0.25:
            self.glitch_active = True
            self.apply_glitch()
            QTimer.singleShot(120, self.restore_text)
            
    def apply_glitch(self):
        glitch_chars = "!@#$%^&*<>[]{}|░▒▓"
        glitched = ""
        for char in self.original_text:
            if random.random() < 0.15:
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

    def stop_animation(self):
        self.glitch_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class HologramButton(QPushButton):
    """Button with holographic hover and click effects."""
    
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
            "red": ("255, 82, 82", COLORS['trash_red']),
            "green": ("0, 230, 118", COLORS['restore_green']),
            "yellow": ("251, 191, 36", COLORS['neon_yellow']),
            "purple": ("191, 0, 255", COLORS['neon_purple']),
        }
        
        base_color, text_color = color_map.get(self.button_color, color_map["cyan"])
            
        if self.is_hovered:
            glow = int(40 + 20 * math.sin(self.hover_phase))
            bg_alpha = 0.4
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
                min-width: 130px;
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        self.setStyleSheet(f"""
            QListWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 82, 82, 0.03),
                    stop:0.5 rgba(10, 22, 40, 0.95),
                    stop:1 rgba(255, 51, 102, 0.03));
                border: 2px solid rgba(255, 82, 82, {pulse / 100});
                border-radius: 14px;
                padding: 8px;
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
                    stop:0 rgba(255, 82, 82, 0.05),
                    stop:0.5 rgba(20, 30, 50, 0.8),
                    stop:1 rgba(255, 82, 82, 0.05));
                border: 1px solid rgba(255, 82, 82, 0.15);
            }}
            QListWidget::item:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 82, 82, 0.15),
                    stop:0.5 rgba(30, 40, 60, 0.9),
                    stop:1 rgba(255, 82, 82, 0.15));
                border: 1px solid rgba(255, 82, 82, 0.4);
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 82, 82, 0.25),
                    stop:0.5 rgba(40, 50, 70, 0.95),
                    stop:1 rgba(255, 82, 82, 0.25));
                border: 2px solid rgba(255, 82, 82, 0.6);
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
                    stop:0 {COLORS['trash_red']},
                    stop:0.5 {COLORS['neon_purple']},
                    stop:1 {COLORS['trash_red']});
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['trash_red_light']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
            }}
        """)

    def stop_animation(self):
        self.glow_timer.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ HOLOGRAM DIALOG STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

def get_trash_dialog_style():
    """Futuristic hologram style for trash dialog."""
    return f"""
    QDialog {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {COLORS['bg_darkest']},
            stop:0.3 {COLORS['bg_dark']},
            stop:0.7 {COLORS['bg_dark']},
            stop:1 {COLORS['bg_darkest']});
        border: 2px solid rgba(255, 82, 82, 0.4);
        border-radius: 16px;
    }}
    
    QLabel {{
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Consolas', monospace;
        font-size: 13px;
        background: transparent;
    }}
    
    QMessageBox {{
        background: {COLORS['bg_darkest']};
        border: 2px solid rgba(255, 82, 82, 0.5);
        border-radius: 12px;
    }}
    
    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        font-size: 13px;
    }}
    
    QMessageBox QPushButton {{
        padding: 10px 24px;
        border-radius: 8px;
        background: rgba(255, 82, 82, 0.15);
        color: {COLORS['trash_red']};
        border: 1px solid rgba(255, 82, 82, 0.4);
        font-weight: 600;
        min-width: 80px;
    }}
    
    QMessageBox QPushButton:hover {{
        background: rgba(255, 82, 82, 0.35);
        color: white;
    }}
    """


def add_hologram_glow(widget, color=QColor(255, 82, 82, 80)):
    """Add holographic glow effect."""
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(35)
    glow.setOffset(0, 0)
    glow.setColor(color)
    widget.setGraphicsEffect(glow)


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ TRASH DIALOG - HOLOGRAM EDITION
# ═══════════════════════════════════════════════════════════════════════════════

class TrashDialog(QDialog):
    """Holographic dialog to manage deleted gestures (recycle bin)."""
    gestureRestored = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⬡ GESTURE TRASH — HOLOGRAM")
        self.setMinimumSize(700, 600)
        self.setStyleSheet(get_trash_dialog_style())
        self._build_ui()
        self.load_trash()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Add scanline overlay
        self.scanline_overlay = HologramScanline(self)
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM HEADER
        # ═══════════════════════════════════════════════════════════════════
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
        
        # Title with icon
        title_row = QHBoxLayout()
        
        icon_label = QLabel("🗑️")
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            background: transparent;
        """)
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
        
        # Stats badge
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
        
        # Subtitle
        subtitle = QLabel("◈ Deleted gestures are stored here. Restore or permanently delete them.")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            background: transparent;
            padding-top: 4px;
        """)
        header_layout.addWidget(subtitle)
        
        add_hologram_glow(header_card, QColor(255, 82, 82, 50))
        layout.addWidget(header_card)
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM TRASH LIST
        # ═══════════════════════════════════════════════════════════════════
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
        
        # Section header
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
        
        self.trash_list = HologramListWidget()
        self.trash_list.setMinimumHeight(280)
        list_layout.addWidget(self.trash_list)
        
        layout.addWidget(list_container)
        
        # ═══════════════════════════════════════════════════════════════════
        # ⬡ HOLOGRAM ACTION BUTTONS
        # ═══════════════════════════════════════════════════════════════════
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
        
        # Restore button
        restore_btn = HologramButton("♻️ RESTORE", "green")
        restore_btn.clicked.connect(self.restore_selected)
        restore_btn.setMinimumHeight(48)
        btn_layout.addWidget(restore_btn)
        
        # Delete forever button
        delete_btn = HologramButton("🗑️ DELETE FOREVER", "red")
        delete_btn.clicked.connect(self.delete_selected_permanently)
        delete_btn.setMinimumHeight(48)
        btn_layout.addWidget(delete_btn)
        
        # Empty trash button
        empty_btn = HologramButton("🧹 EMPTY TRASH", "yellow")
        empty_btn.clicked.connect(self.empty_trash)
        empty_btn.setMinimumHeight(48)
        btn_layout.addWidget(empty_btn)
        
        btn_layout.addStretch()
        
        # Close button
        close_btn = HologramButton("✖ CLOSE", "cyan")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(48)
        btn_layout.addWidget(close_btn)
        
        layout.addWidget(btn_card)
    
    def resizeEvent(self, event):
        """Update scanline overlay size on resize."""
        super().resizeEvent(event)
        self.scanline_overlay.setGeometry(self.rect())
        self.scanline_overlay.raise_()
        
    def load_trash(self):
        """Load and display deleted gestures with holographic styling."""
        self.trash_list.clear()
        trash = load_trash()
        
        # Update stats badge
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
            
            # Empty state item
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
            
            # Format with cyberpunk styling
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
        """Show a holographic styled message box."""
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
                border: 2px solid rgba(255, 82, 82, 0.5);
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
    
    def restore_selected(self):
        """Restore selected gesture with holographic feedback."""
        current = self.trash_list.currentItem()
        if not current:
            msg = self._show_hologram_message(
                "Selection Required",
                "◈ Please select a gesture to restore!",
                "warning"
            )
            msg.exec()
            return
        
        gesture = current.data(Qt.UserRole)
        if not gesture:
            return
            
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ Confirm Restore")
        msg.setIcon(QMessageBox.Question)
        msg.setText(
            f"<p style='color: {COLORS['holo_cyan']}; font-size: 14px;'>"
            f"◈ Restore gesture '<b>{gesture['name']}</b>'?</p>"
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
            if restore_gesture(gesture['id']):
                self.gestureRestored.emit(gesture['id'])
                self.load_trash()
                
                success_msg = self._show_hologram_message(
                    "Restore Complete",
                    f"✓ Gesture '<b>{gesture['name']}</b>' has been restored!",
                    "info"
                )
                success_msg.exec()
    
    def delete_selected_permanently(self):
        """Permanently delete selected gesture with holographic warning."""
        current = self.trash_list.currentItem()
        if not current:
            msg = self._show_hologram_message(
                "Selection Required",
                "◈ Please select a gesture to delete!",
                "warning"
            )
            msg.exec()
            return
        
        gesture = current.data(Qt.UserRole)
        if not gesture:
            return
            
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ PERMANENT DELETE")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"<h3 style='color: {COLORS['neon_red']};'>⚠ PERMANENT DELETION</h3>"
            f"<p style='color: {COLORS['text_primary']}; font-size: 13px;'>"
            f"Delete '<b style='color: {COLORS['trash_red']};'>{gesture['name']}</b>' permanently?</p>"
            f"<p style='color: {COLORS['neon_orange']}; font-size: 12px;'>"
            f"◈ THIS ACTION CANNOT BE UNDONE!</p>"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid {COLORS['neon_red']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(255, 82, 82, 0.15);
                color: {COLORS['trash_red']};
                border: 1px solid rgba(255, 82, 82, 0.4);
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 82, 82, 0.35);
                color: white;
            }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            if permanent_delete_gesture(gesture['id']):
                self.load_trash()
                
                success_msg = self._show_hologram_message(
                    "Deleted",
                    "🗑️ Gesture permanently deleted from system.",
                    "info"
                )
                success_msg.exec()
    
    def empty_trash(self):
        """Empty entire trash with holographic confirmation."""
        trash = load_trash()
        if not trash:
            msg = self._show_hologram_message(
                "Trash Empty",
                "◈ Trash is already empty — nothing to delete!",
                "info"
            )
            msg.exec()
            return
            
        msg = QMessageBox(self)
        msg.setWindowTitle("⬡ EMPTY TRASH")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"<h3 style='color: {COLORS['neon_red']};'>⚠ EMPTY ALL TRASH</h3>"
            f"<p style='color: {COLORS['text_primary']}; font-size: 13px;'>"
            f"Permanently delete all <b style='color: {COLORS['trash_red']};'>{len(trash)}</b> gesture(s) in trash?</p>"
            f"<p style='color: {COLORS['neon_orange']}; font-size: 12px;'>"
            f"◈ THIS ACTION CANNOT BE UNDONE!</p>"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['bg_darkest']};
                border: 2px solid {COLORS['neon_orange']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                padding: 10px 24px;
                border-radius: 8px;
                background: rgba(251, 191, 36, 0.15);
                color: {COLORS['neon_yellow']};
                border: 1px solid rgba(251, 191, 36, 0.4);
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(251, 191, 36, 0.35);
                color: white;
            }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            if empty_trash():
                self.load_trash()
                
                success_msg = self._show_hologram_message(
                    "Trash Emptied",
                    "🧹 All deleted gestures have been permanently removed!",
                    "info"
                )
                success_msg.exec()

    def closeEvent(self, event):
        """Stop all animations on close."""
        self.scanline_overlay.stop_animation()
        # Stop list animation
        self.trash_list.stop_animation()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# ⬡ MODULE INFO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ TRASH DIALOG MODULE V3.0 — HOLOGRAM EDITION ⬡                            ║
║  Futuristic Navy Blue Design • Cyberpunk Aesthetic                          ║
║  HUD Interface • Neon Glow • HOLOGRAM EFFECTS                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  HOLOGRAM FEATURES:                                                         ║
║  ▸ HologramScanline   - Red-tinted scanline overlay                         ║
║  ▸ HologramFrame      - Pulsing red borders with glitch                     ║
║  ▸ HologramLabel      - Text with glitch animation                          ║
║  ▸ HologramButton     - Color-coded buttons with glow                       ║
║  ▸ HologramListWidget - Animated list with neon styling                     ║
║  ▸ Stats Badge        - Dynamic item counter                                ║
║  ▸ Holographic Dialogs - Styled message boxes                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)