"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    AUREVIX NEURAL TRAINING INTERFACE                         ║
║               🌟 CYBERPUNK HOLOGRAPHIC EDITION v7.0 🌟                        ║
║                   ⚡ ULTRA FUTURISTIC 3-CARD HUB ⚡                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea,
    QGridLayout, QApplication, QMessageBox,
    QStackedWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, 
    QEasingCurve, Property, QRect, QPoint,
    QSequentialAnimationGroup, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QFont, QPainter, QColor, QLinearGradient,
    QPen, QBrush, QRadialGradient, QPainterPath
)
import math
import random
# ═══════════════════════════════════════════════════════════════════════════════
# 🏠 BACK TO DASHBOARD BUTTON - HOLOGRAPHIC STYLE
# ═══════════════════════════════════════════════════════════════════════════════

class BackToDashboardButton(QPushButton):
    """Holographic back to dashboard button"""
    
    def __init__(self, parent=None):
        super().__init__("◄  BACK TO DASHBOARD", parent)
        self.setFixedSize(240, 50)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Consolas", 12, QFont.Bold))
        
        self._hover = False
        self._pulse = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(Neon.CYAN))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
    
    def animate(self):
        self._pulse = (self._pulse + 0.12) % (2 * math.pi)
        if self._hover:
            self.update()
    
    def enterEvent(self, event):
        self._hover = True
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(45)
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(25)
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background
        path = QPainterPath()
        path.addRoundedRect(2, 2, w-4, h-4, 12, 12)
        
        if self._hover:
            # Animated gradient on hover
            bg_grad = QLinearGradient(0, 0, w, 0)
            pulse_pos = 0.3 + 0.4 * math.sin(self._pulse)
            bg_grad.setColorAt(0, QColor(0, 245, 255, 40))
            bg_grad.setColorAt(pulse_pos, QColor(0, 245, 255, 80))
            bg_grad.setColorAt(1, QColor(0, 245, 255, 40))
            painter.fillPath(path, bg_grad)
        else:
            painter.fillPath(path, QColor(0, 245, 255, 25))
        
        # Border
        pen = QPen(QColor(Neon.CYAN))
        pen.setWidth(2 if self._hover else 1)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Inner glow on hover
        if self._hover:
            inner_path = QPainterPath()
            inner_path.addRoundedRect(5, 5, w-10, h-10, 10, 10)
            inner_pen = QPen(QColor(0, 245, 255, 60))
            inner_pen.setWidth(1)
            painter.setPen(inner_pen)
            painter.drawPath(inner_path)
        
        # Text
        painter.setFont(self.font())
        if self._hover:
            # Text glow effect
            glow_color = QColor(Neon.CYAN)
            glow_color.setAlpha(150)
            painter.setPen(glow_color)
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                painter.drawText(self.rect().adjusted(offset[0], offset[1], offset[0], offset[1]), 
                               Qt.AlignCenter, self.text())
        
        painter.setPen(QColor(Neon.CYAN))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        # Arrow animation on hover
        if self._hover:
            arrow_offset = int(5 * math.sin(self._pulse * 2))
            painter.setPen(QPen(QColor(Neon.CYAN), 2))
            arrow_x = 15 - arrow_offset
            arrow_y = h / 2
            
            # Draw animated arrow
            painter.drawLine(int(arrow_x), int(arrow_y), int(arrow_x + 8), int(arrow_y - 4))
            painter.drawLine(int(arrow_x), int(arrow_y), int(arrow_x + 8), int(arrow_y + 4))


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 NEON HOLOGRAPHIC COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Neon:
    # Primary Neons
    CYAN = "#00f5ff"
    MAGENTA = "#ff00ff"
    YELLOW = "#f0ff00"
    GREEN = "#00ff9f"
    ORANGE = "#ff6b00"
    RED = "#ff0055"
    PURPLE = "#bf00ff"
    PINK = "#ff6bff"
    BLUE = "#0080ff"
    
    # Holographic
    HOLO_1 = "#00ffff"
    HOLO_2 = "#ff00ff"
    HOLO_3 = "#00ff88"
    HOLO_4 = "#ffff00"
    
    # UI
    WHITE = "#ffffff"
    TEXT = "#e0e8ff"
    TEXT_DIM = "#5a7090"
    BG_DARK = "#000510"
    BG_MID = "#050a18"


# ═══════════════════════════════════════════════════════════════════════════════
# ✨ ANIMATED PARTICLE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-2, -0.5)
        self.life = random.uniform(0.5, 1.0)
        self.decay = random.uniform(0.005, 0.015)
        self.size = random.uniform(2, 5)
        self.color = random.choice([Neon.CYAN, Neon.MAGENTA, Neon.GREEN, Neon.YELLOW])
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0


class ParticleSystem(QWidget):
    """Floating particle effects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.particles = []
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(33)
        
        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.spawn_particle)
        self.spawn_timer.start(100)
    
    def spawn_particle(self):
        if len(self.particles) < 50:
            x = random.randint(0, self.width())
            y = self.height()
            self.particles.append(Particle(x, y))
    
    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for p in self.particles:
            color = QColor(p.color)
            color.setAlphaF(p.life * 0.6)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(p.x), int(p.y), int(p.size), int(p.size))


# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 ANIMATED HOLOGRAPHIC GRID BACKGROUND
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicGridBackground(QWidget):
    """Animated cyberpunk grid background"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.offset = 0
        self.pulse = 0
        self.scan_line = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(33)
    
    def animate(self):
        self.offset = (self.offset + 0.5) % 50
        self.pulse = (self.pulse + 0.03) % (2 * math.pi)
        self.scan_line = (self.scan_line + 3) % (self.height() + 100)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background gradient
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor("#000510"))
        bg.setColorAt(0.3, QColor("#050a18"))
        bg.setColorAt(0.6, QColor("#0a0520"))
        bg.setColorAt(1, QColor("#050510"))
        painter.fillRect(self.rect(), bg)
        
        # Radial glow in center
        center_glow = QRadialGradient(w/2, h/2, max(w, h)/2)
        center_glow.setColorAt(0, QColor(0, 245, 255, 20))
        center_glow.setColorAt(0.3, QColor(255, 0, 255, 10))
        center_glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), center_glow)
        
        # Animated grid lines - Vertical
        pulse_alpha = int(30 + 15 * math.sin(self.pulse))
        
        pen = QPen(QColor(0, 245, 255, pulse_alpha))
        pen.setWidth(1)
        painter.setPen(pen)
        
        grid_size = 50
        for x in range(0, w + grid_size, grid_size):
            painter.drawLine(x, 0, x, h)
        
        # Horizontal lines with perspective
        for y in range(0, h + grid_size, grid_size):
            y_offset = int(y + self.offset) % (h + grid_size)
            alpha = max(10, pulse_alpha - int(y_offset * 0.02))
            pen.setColor(QColor(255, 0, 255, alpha))
            painter.setPen(pen)
            painter.drawLine(0, y_offset, w, y_offset)
        
        # Scan line effect
        scan_grad = QLinearGradient(0, self.scan_line - 50, 0, self.scan_line + 50)
        scan_grad.setColorAt(0, QColor(0, 255, 255, 0))
        scan_grad.setColorAt(0.5, QColor(0, 255, 255, 80))
        scan_grad.setColorAt(1, QColor(0, 255, 255, 0))
        painter.fillRect(0, int(self.scan_line - 50), w, 100, scan_grad)
        
        # Corner decorations
        self.draw_corner_decor(painter, 20, 20, 60, 0)
        self.draw_corner_decor(painter, w - 80, 20, 60, 1)
        self.draw_corner_decor(painter, 20, h - 80, 60, 2)
        self.draw_corner_decor(painter, w - 80, h - 80, 60, 3)
    
    def draw_corner_decor(self, painter, x, y, size, corner):
        """Draw corner decorations"""
        pen = QPen(QColor(Neon.CYAN))
        pen.setWidth(2)
        painter.setPen(pen)
        
        if corner == 0:  # Top-left
            painter.drawLine(x, y, x + size, y)
            painter.drawLine(x, y, x, y + size)
        elif corner == 1:  # Top-right
            painter.drawLine(x, y, x + size, y)
            painter.drawLine(x + size, y, x + size, y + size)
        elif corner == 2:  # Bottom-left
            painter.drawLine(x, y + size, x + size, y + size)
            painter.drawLine(x, y, x, y + size)
        elif corner == 3:  # Bottom-right
            painter.drawLine(x, y + size, x + size, y + size)
            painter.drawLine(x + size, y, x + size, y + size)


# ═══════════════════════════════════════════════════════════════════════════════
# 💫 DATA STREAM WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class DataStreamWidget(QWidget):
    """Matrix-like data stream effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.streams = []
        self.chars = "01"
        
        # Initialize streams
        for _ in range(15):
            self.streams.append({
                'x': random.randint(0, 1920),
                'y': random.randint(-500, 0),
                'speed': random.uniform(2, 6),
                'chars': [random.choice(self.chars) for _ in range(random.randint(5, 15))],
                'color': random.choice([Neon.CYAN, Neon.GREEN, Neon.MAGENTA])
            })
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
    
    def animate(self):
        for stream in self.streams:
            stream['y'] += stream['speed']
            if stream['y'] > self.height() + 200:
                stream['y'] = random.randint(-300, -50)
                stream['x'] = random.randint(0, self.width())
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        font = QFont("Consolas", 12)
        painter.setFont(font)
        
        for stream in self.streams:
            for i, char in enumerate(stream['chars']):
                alpha = max(0, 180 - i * 15)
                color = QColor(stream['color'])
                color.setAlpha(alpha)
                painter.setPen(color)
                painter.drawText(int(stream['x']), int(stream['y'] - i * 18), char)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎴 HOLOGRAPHIC CARD WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicCard(QPushButton):
    """Ultra futuristic holographic card"""
    
    def __init__(self, emoji, title, description, color, mode_id, parent=None):
        super().__init__(parent)
        
        self.emoji = emoji
        self.title = title
        self.description = description
        self.color = color
        self.mode_id = mode_id
        
        self.setFixedSize(340, 280)
        self.setCursor(Qt.PointingHandCursor)
        
        # Animation states
        self._hover = False
        self._glow_intensity = 0.0
        self._scan_pos = 0
        self._holo_phase = random.uniform(0, 2 * math.pi)
        
        # Glow animation
        self.glow_anim = QPropertyAnimation(self, b"glow_intensity")
        self.glow_anim.setDuration(300)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Scan line animation
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.update_scan)
        self.scan_timer.start(30)
        
        # Holographic shimmer
        self.holo_timer = QTimer(self)
        self.holo_timer.timeout.connect(self.update_holo)
        self.holo_timer.start(50)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(self.color))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
    
    def get_glow_intensity(self):
        return self._glow_intensity
    
    def set_glow_intensity(self, value):
        self._glow_intensity = value
        self.update()
    
    glow_intensity = Property(float, get_glow_intensity, set_glow_intensity)
    
    def update_scan(self):
        self._scan_pos = (self._scan_pos + 3) % (self.height() + 60)
        if self._hover:
            self.update()
    
    def update_holo(self):
        self._holo_phase = (self._holo_phase + 0.08) % (2 * math.pi)
        self.update()
    
    def enterEvent(self, event):
        self._hover = True
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow_intensity)
        self.glow_anim.setEndValue(1.0)
        self.glow_anim.start()
        
        # Update shadow
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(60)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow_intensity)
        self.glow_anim.setEndValue(0.0)
        self.glow_anim.start()
        
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(30)
        super().leaveEvent(event)
    
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        r, g, b = self.hex_rgb(self.color)
        
        # === BACKGROUND ===
        bg_path = QPainterPath()
        bg_path.addRoundedRect(2, 2, w-4, h-4, 20, 20)
        
        # Gradient background
        bg_grad = QLinearGradient(0, 0, w, h)
        bg_grad.setColorAt(0, QColor(10, 15, 30, 240))
        bg_grad.setColorAt(0.5, QColor(5, 10, 25, 250))
        bg_grad.setColorAt(1, QColor(8, 12, 28, 240))
        painter.fillPath(bg_path, bg_grad)
        
        # Holographic shimmer overlay
        holo_alpha = int(30 + 20 * math.sin(self._holo_phase))
        holo_grad = QLinearGradient(
            w * (0.3 + 0.4 * math.sin(self._holo_phase)), 0,
            w * (0.7 + 0.3 * math.cos(self._holo_phase)), h
        )
        holo_grad.setColorAt(0, QColor(r, g, b, 0))
        holo_grad.setColorAt(0.5, QColor(r, g, b, holo_alpha))
        holo_grad.setColorAt(1, QColor(r, g, b, 0))
        painter.fillPath(bg_path, holo_grad)
        
        # === BORDER ===
        border_alpha = int(150 + 105 * self._glow_intensity)
        pen = QPen(QColor(r, g, b, border_alpha))
        pen.setWidth(3 if self._hover else 2)
        painter.setPen(pen)
        painter.drawPath(bg_path)
        
        # Inner glow border
        if self._hover:
            inner_pen = QPen(QColor(r, g, b, 60))
            inner_pen.setWidth(1)
            painter.setPen(inner_pen)
            inner_path = QPainterPath()
            inner_path.addRoundedRect(6, 6, w-12, h-12, 18, 18)
            painter.drawPath(inner_path)
        
        # === SCAN LINE (on hover) ===
        if self._hover:
            scan_grad = QLinearGradient(0, self._scan_pos - 30, 0, self._scan_pos + 30)
            scan_grad.setColorAt(0, QColor(r, g, b, 0))
            scan_grad.setColorAt(0.5, QColor(r, g, b, 100))
            scan_grad.setColorAt(1, QColor(r, g, b, 0))
            
            painter.setClipPath(bg_path)
            painter.fillRect(0, int(self._scan_pos - 30), w, 60, scan_grad)
            painter.setClipping(False)
        
        # === TOP DECORATIVE LINE ===
        top_line_grad = QLinearGradient(30, 0, w - 30, 0)
        top_line_grad.setColorAt(0, QColor(r, g, b, 0))
        top_line_grad.setColorAt(0.2, QColor(r, g, b, 200))
        top_line_grad.setColorAt(0.8, QColor(r, g, b, 200))
        top_line_grad.setColorAt(1, QColor(r, g, b, 0))
        painter.fillRect(30, 8, w - 60, 2, top_line_grad)
        
        # === EMOJI ===
        painter.setPen(Qt.white)
        emoji_font = QFont("Segoe UI Emoji", 58)
        painter.setFont(emoji_font)
        
        # Emoji glow
        if self._hover:
            glow_color = QColor(r, g, b, 100)
            painter.setPen(glow_color)
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                painter.drawText(QRect(dx, 30 + dy, w, 80), Qt.AlignCenter, self.emoji)
        
        painter.setPen(Qt.white)
        painter.drawText(QRect(0, 30, w, 80), Qt.AlignCenter, self.emoji)
        
        # === TITLE ===
        title_font = QFont("Consolas", 18, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(self.color))
        painter.drawText(QRect(0, 115, w, 30), Qt.AlignCenter, self.title)
        
        # === SEPARATOR ===
        sep_y = 150
        sep_grad = QLinearGradient(40, 0, w - 40, 0)
        sep_grad.setColorAt(0, QColor(r, g, b, 0))
        sep_grad.setColorAt(0.3, QColor(r, g, b, 180))
        sep_grad.setColorAt(0.7, QColor(r, g, b, 180))
        sep_grad.setColorAt(1, QColor(r, g, b, 0))
        painter.fillRect(40, sep_y, w - 80, 2, sep_grad)
        
        # Center diamond
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        diamond = QPainterPath()
        cx = w / 2
        diamond.moveTo(cx, sep_y - 4)
        diamond.lineTo(cx + 5, sep_y + 1)
        diamond.lineTo(cx, sep_y + 6)
        diamond.lineTo(cx - 5, sep_y + 1)
        diamond.closeSubpath()
        painter.drawPath(diamond)
        
        # === DESCRIPTION ===
        desc_font = QFont("Consolas", 11)
        painter.setFont(desc_font)
        painter.setPen(QColor(Neon.TEXT))
        painter.drawText(QRect(20, 160, w - 40, 50), 
                        Qt.AlignCenter | Qt.TextWordWrap, self.description)
        
        # === BOTTOM STATUS BAR ===
        status_y = h - 45
        
        # Status background
        status_bg = QPainterPath()
        status_bg.addRoundedRect(20, status_y, w - 40, 30, 8, 8)
        painter.fillPath(status_bg, QColor(r, g, b, 30))
        
        # Status text
        status_font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(status_font)
        
        if self._hover:
            # Animated dots
            dots = "●" * (1 + int(self._holo_phase * 2) % 3)
            painter.setPen(QColor(self.color))
            painter.drawText(QRect(20, status_y, w - 40, 30), 
                           Qt.AlignCenter, f"◈ INITIALIZING {dots}")
        else:
            painter.setPen(QColor(Neon.TEXT_DIM))
            painter.drawText(QRect(20, status_y, w - 40, 30), 
                           Qt.AlignCenter, "▶ CLICK TO ACTIVATE")
        
        # === CORNER BRACKETS ===
        bracket_color = QColor(r, g, b, 150 if self._hover else 80)
        pen = QPen(bracket_color)
        pen.setWidth(2)
        painter.setPen(pen)
        
        bracket_size = 15
        margin = 12
        
        # Top-left
        painter.drawLine(margin, margin + bracket_size, margin, margin)
        painter.drawLine(margin, margin, margin + bracket_size, margin)
        
        # Top-right
        painter.drawLine(w - margin - bracket_size, margin, w - margin, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + bracket_size)
        
        # Bottom-left
        painter.drawLine(margin, h - margin - bracket_size, margin, h - margin)
        painter.drawLine(margin, h - margin, margin + bracket_size, h - margin)
        
        # Bottom-right
        painter.drawLine(w - margin - bracket_size, h - margin, w - margin, h - margin)
        painter.drawLine(w - margin, h - margin - bracket_size, w - margin, h - margin)
        
        # === TECH DOTS ===
        painter.setBrush(QColor(r, g, b, 200 if self._hover else 100))
        painter.setPen(Qt.NoPen)
        for i in range(3):
            dot_x = w - 25 - i * 8
            painter.drawEllipse(int(dot_x), 20, 4, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# 🏷️ HOLOGRAPHIC TITLE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicTitle(QWidget):
    """Animated holographic title"""
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setFixedHeight(120)
        
        self._phase = 0
        self._glitch_timer = 0
        self._glitch_active = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
    
    def animate(self):
        self._phase = (self._phase + 0.1) % (2 * math.pi)
        
        # Random glitch
        self._glitch_timer += 1
        if self._glitch_timer > 60:
            self._glitch_active = random.random() < 0.1
            if self._glitch_active:
                self._glitch_timer = 0
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Title font
        font = QFont("Consolas", 42, QFont.Bold)
        painter.setFont(font)
        
        # Calculate text position
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.text)
        x = (w - text_width) / 2
        y = h / 2 + 15
        
        # Glitch effect
        glitch_offset = 3 if self._glitch_active else 0
        
        # Cyan shadow (left)
        painter.setPen(QColor(0, 255, 255, 100))
        painter.drawText(int(x - 3 - glitch_offset), int(y), self.text)
        
        # Magenta shadow (right)
        painter.setPen(QColor(255, 0, 255, 100))
        painter.drawText(int(x + 3 + glitch_offset), int(y), self.text)
        
        # Main text with gradient
        gradient = QLinearGradient(x, y - 30, x + text_width, y)
        phase_offset = self._phase
        gradient.setColorAt(0, QColor(Neon.CYAN))
        gradient.setColorAt(0.3 + 0.2 * math.sin(phase_offset), QColor(Neon.MAGENTA))
        gradient.setColorAt(0.6 + 0.2 * math.cos(phase_offset), QColor(Neon.YELLOW))
        gradient.setColorAt(1, QColor(Neon.CYAN))
        
        painter.setPen(QPen(QBrush(gradient), 1))
        painter.drawText(int(x), int(y), self.text)
        
        # Subtitle
        sub_font = QFont("Consolas", 14)
        painter.setFont(sub_font)
        painter.setPen(QColor(Neon.TEXT_DIM))
        painter.drawText(QRect(0, int(y + 15), w, 30), Qt.AlignCenter, 
                        "⟨ NEURAL TRAINING MODULES ⟩")


# ═══════════════════════════════════════════════════════════════════════════════
# 🔥 ANIMATED FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicFooter(QFrame):
    """Animated cyberpunk footer"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        
        self._pulse = 0
        self._data_offset = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 10, 30, 10)
        
        # Status indicator
        self.status = QLabel("◉ SYSTEM ONLINE")
        self.status.setFont(QFont("Consolas", 12, QFont.Bold))
        self.status.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(self.status)
        
        layout.addStretch()
        
        # Mode info
        self.mode_info = QLabel("◈ SELECT TRAINING MODE")
        self.mode_info.setFont(QFont("Consolas", 12))
        self.mode_info.setStyleSheet(f"color: {Neon.CYAN};")
        layout.addWidget(self.mode_info)
        
        layout.addStretch()
        
        # Version
        self.version = QLabel("AUREVIX v7.0 // HOLOGRAPHIC")
        self.version.setFont(QFont("Consolas", 10))
        self.version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.version)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100)
    
    def animate(self):
        self._pulse = (self._pulse + 0.15) % (2 * math.pi)
        self._data_offset = (self._data_offset + 1) % 20
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background gradient
        bg = QLinearGradient(0, h, 0, 0)
        bg.setColorAt(0, QColor(255, 0, 255, 30))
        bg.setColorAt(0.5, QColor(0, 0, 0, 200))
        bg.setColorAt(1, QColor(0, 0, 0, 250))
        painter.fillRect(self.rect(), bg)
        
        # Top border with pulse
        alpha = int(150 + 105 * math.sin(self._pulse))
        border_grad = QLinearGradient(0, 0, w, 0)
        border_grad.setColorAt(0, QColor(0, 245, 255, 0))
        border_grad.setColorAt(0.2, QColor(0, 245, 255, alpha))
        border_grad.setColorAt(0.5, QColor(255, 0, 255, alpha))
        border_grad.setColorAt(0.8, QColor(0, 245, 255, alpha))
        border_grad.setColorAt(1, QColor(0, 245, 255, 0))
        painter.fillRect(0, 0, w, 3, border_grad)
        
        # Data stream dots
        painter.setPen(Qt.NoPen)
        for i in range(20):
            x = (i * 50 + self._data_offset * 5) % w
            alpha = 50 + 30 * math.sin(self._pulse + i * 0.3)
            painter.setBrush(QColor(0, 255, 255, int(alpha)))
            painter.drawEllipse(int(x), h - 8, 3, 3)


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 EXIT BUTTON - HOLOGRAPHIC
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicExitButton(QPushButton):
    """Holographic exit button"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(220, 55)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Consolas", 13, QFont.Bold))
        
        self._hover = False
        self._pulse = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(Neon.RED))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
    
    def animate(self):
        self._pulse = (self._pulse + 0.15) % (2 * math.pi)
        if self._hover:
            self.update()
    
    def enterEvent(self, event):
        self._hover = True
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(40)
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(20)
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background
        path = QPainterPath()
        path.addRoundedRect(2, 2, w-4, h-4, 15, 15)
        
        if self._hover:
            bg_alpha = int(60 + 30 * math.sin(self._pulse))
            painter.fillPath(path, QColor(255, 0, 85, bg_alpha))
        else:
            painter.fillPath(path, QColor(255, 0, 85, 30))
        
        # Border
        pen = QPen(QColor(Neon.RED))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Text
        painter.setFont(self.font())
        painter.setPen(QColor(Neon.RED))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 TRAINING MODE PAGE - HOLOGRAPHIC EDITION
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingModePage(QWidget):
    mode_closed = Signal()
    
    def __init__(self, parent=None, tracker=None):
        super().__init__(parent)
        self.setWindowTitle("◈ AUREVIX HOLOGRAPHIC TRAINING")
        self.setMinimumSize(1400, 950)
        
        self.shared_tracker = tracker
        self.external_mode = None
        self.mode_container = None
        
        self.setup_ui()
    
    def set_tracker(self, tracker):
        self.shared_tracker = tracker
    
    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        
        # Stacked Widget
        self.mode_stack = QStackedWidget()
        
        # Selection Page
        self.selection_page = self.build_selection_page()
        self.mode_stack.addWidget(self.selection_page)
        
        self.mode_stack.setCurrentIndex(0)
        main.addWidget(self.mode_stack, 1)
        
        # Footer
        self.footer = HolographicFooter()
        main.addWidget(self.footer)
    
    def build_selection_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
    
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    
        # === BACKGROUND LAYERS ===
        # Grid background
        self.grid_bg = HolographicGridBackground(page)
        self.grid_bg.setGeometry(0, 0, 2000, 1200)
        self.grid_bg.lower()
    
        # Data streams
        self.data_streams = DataStreamWidget(page)
        self.data_streams.setGeometry(0, 0, 2000, 1200)
    
        # Particles
        self.particles = ParticleSystem(page)
        self.particles.setGeometry(0, 0, 2000, 1200)
    
        # === CONTENT ===
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(50, 30, 50, 30)
        content_layout.setSpacing(30)
    
        # ═══════════════════════════════════════════════════════════════════════════
        # 🏠 BACK TO DASHBOARD BUTTON (TOP-LEFT)
        # ═══════════════════════════════════════════════════════════════════════════
        back_container = QWidget()
        back_container.setStyleSheet("background: transparent;")
        back_layout = QHBoxLayout(back_container)
        back_layout.setContentsMargins(0, 0, 0, 10)
    
        self.dashboard_btn = BackToDashboardButton()
        self.dashboard_btn.clicked.connect(self.close_training_mode)
        back_layout.addWidget(self.dashboard_btn)
        back_layout.addStretch()
    
        content_layout.addWidget(back_container)
    
        # Title
        self.title = HolographicTitle("🎯 SELECT MODE")
        content_layout.addWidget(self.title)

        
        # Cards Container
        cards_widget = QWidget()
        cards_widget.setStyleSheet("background: transparent;")
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setSpacing(40)
        cards_layout.setContentsMargins(50, 20, 50, 20)
        
        # 3 Holographic Cards
        card1 = HolographicCard(
            emoji="📊",
            title="GESTURE ANALYTICS",
            description="Performance analysis with\nheatmaps & radar charts",
            color=Neon.GREEN,
            mode_id="analytics"
        )
        card1.clicked.connect(lambda: self.open_training_mode("analytics"))
        cards_layout.addWidget(card1, alignment=Qt.AlignCenter)
        
        card2 = HolographicCard(
            emoji="⚡",
            title="REFLEX CHALLENGE",
            description="Speed & memory tests\nwith timed challenges",
            color=Neon.MAGENTA,
            mode_id="reflex"
        )
        card2.clicked.connect(lambda: self.open_training_mode("reflex"))
        cards_layout.addWidget(card2, alignment=Qt.AlignCenter)
        
        card3 = HolographicCard(
            emoji="🤖",
            title="ADAPTIVE TRAINER",
            description="AI adjusts difficulty\nbased on your level",
            color=Neon.ORANGE,
            mode_id="adaptive"
        )
        card3.clicked.connect(lambda: self.open_training_mode("adaptive"))
        cards_layout.addWidget(card3, alignment=Qt.AlignCenter)
        
        content_layout.addWidget(cards_widget, 1, Qt.AlignCenter)
        
        # Exit Button
        exit_container = QWidget()
        exit_container.setStyleSheet("background: transparent;")
        exit_layout = QHBoxLayout(exit_container)
        
        self.exit_btn = HolographicExitButton("✕  EXIT TRAINING")
        self.exit_btn.clicked.connect(self.close_training_mode)
        exit_layout.addWidget(self.exit_btn, alignment=Qt.AlignCenter)
        
        content_layout.addWidget(exit_container)
        content_layout.addStretch()
        
        layout.addWidget(content, 1)
        
        return page
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize background layers
        if hasattr(self, 'grid_bg'):
            self.grid_bg.setGeometry(0, 0, self.width(), self.height())
            self.data_streams.setGeometry(0, 0, self.width(), self.height())
            self.particles.setGeometry(0, 0, self.width(), self.height())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎯 MODE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def open_training_mode(self, mode_id):
        print(f"\n🎯 Opening mode: {mode_id}")
        
        mode_map = {
            "analytics": ("training_modes.gesture_analytics", "GestureAnalyticsMode", 
                         "📊 GESTURE ANALYTICS", Neon.GREEN),
            "reflex": ("training_modes.reflex_challenge", "ReflexChallengeMode", 
                      "⚡ REFLEX CHALLENGE", Neon.MAGENTA),
            "adaptive": ("training_modes.adaptive_trainer", "AdaptiveTrainerMode", 
                        "🤖 ADAPTIVE TRAINER", Neon.ORANGE)
        }
        
        if mode_id not in mode_map:
            print(f"❌ Unknown mode: {mode_id}")
            return
        
        module_name, class_name, title, color = mode_map[mode_id]
        self.load_external_mode(module_name, class_name, title, color)
    
    def load_external_mode(self, module_name, class_name, title, color):
        try:
            print(f"  📦 Loading {title}...")
            
            module = __import__(module_name, fromlist=[class_name])
            mode_class = getattr(module, class_name)
            
            self.cleanup_current_mode()
            
            self.external_mode = mode_class()
            
            if self.shared_tracker and hasattr(self.external_mode, 'set_tracker'):
                self.external_mode.set_tracker(self.shared_tracker)
            
            if hasattr(self.external_mode, 'mode_closed'):
                self.external_mode.mode_closed.connect(self.back_to_mode_selection)
            
            self.mode_container = self.create_mode_container(self.external_mode, title, color)
            
            page_index = self.mode_stack.addWidget(self.mode_container)
            self.mode_stack.setCurrentIndex(page_index)
            
            self.footer.mode_info.setText(f"◈ {title}")
            self.footer.mode_info.setStyleSheet(f"color: {color};")
            
            print(f"  ✅ {title} loaded!")
            
        except ImportError as e:
            print(f"  ❌ Import Error: {e}")
            self.show_mode_error(title, f"Module not found: {module_name}\n\n{e}")
        except AttributeError as e:
            print(f"  ❌ Attribute Error: {e}")
            self.show_mode_error(title, f"Class not found: {class_name}\n\n{e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self.show_mode_error(title, str(e))
    
    def show_mode_error(self, title, error):
        QMessageBox.warning(
            self, "⚠️ Mode Error",
            f"Failed to load {title}\n\n{error}",
            QMessageBox.Ok
        )
        self.mode_stack.setCurrentIndex(0)
    
    def create_mode_container(self, mode_widget, title, color):
        """Create container for external training mode with PROPER SCROLLING"""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000510, stop:0.5 #050a18, stop:1 #0a0520);
            }}
        """)
    
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    
        # ═══ TOP BAR ═══
        top_bar = QFrame()
        top_bar.setFixedHeight(55)
        r, g, b = self.hex_rgb(color)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(5, 10, 25, 0.98), stop:1 rgba(0, 0, 0, 0.95));
                border-bottom: 3px solid {color};
            }}
        """)
    
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(25, 8, 25, 8)
    
        # Back Button
        back_btn = QPushButton("◄  BACK TO MODES")
        back_btn.setFixedSize(200, 38)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 245, 255, 0.2), stop:1 rgba(0, 245, 255, 0.1));
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: rgba(0, 245, 255, 0.35);
                border-width: 3px;
            }}
        """)
        back_btn.clicked.connect(self.back_to_mode_selection)
        bar_layout.addWidget(back_btn)
    
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Consolas", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {color}; background: transparent;")
        bar_layout.addWidget(title_label)
    
        bar_layout.addStretch()
    
        # Status
        status = QLabel("● ACTIVE")
        status.setFont(QFont("Consolas", 11))
        status.setStyleSheet(f"color: {Neon.GREEN}; background: transparent;")
        bar_layout.addWidget(status)
    
        layout.addWidget(top_bar)
    
        # ═══ HIDE MODE'S BUILT-IN CONTROLS ═══
        for attr in ['header', 'back_btn', 'exit_btn', 'title_label']:
            if hasattr(mode_widget, attr):
                widget = getattr(mode_widget, attr)
                if widget:
                    widget.setVisible(False)
    
        # ═══ SCROLL AREA (FIXED!) ═══
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 🔥 IMPORTANT!
    
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: rgba(0, 30, 60, 0.5);
                width: 14px;
                border-radius: 7px;
                margin: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.CYAN}, stop:1 {Neon.MAGENTA});
                border-radius: 6px;
                min-height: 50px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.MAGENTA}, stop:1 {Neon.CYAN});
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
    
        # 🔥 WRAPPER WIDGET FOR PROPER SIZING
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(0)
    
        # Add mode widget
        scroll_layout.addWidget(mode_widget)
        scroll_layout.addStretch()  # 🔥 Bottom padding
    
        scroll.setWidget(scroll_content)
    
        # 🔥 ENSURE MINIMUM SIZE
        mode_widget.setMinimumHeight(800)  # Adjust based on your mode's content
    
        layout.addWidget(scroll, 1)
    
        return container
    
    def cleanup_current_mode(self):
        if self.external_mode:
            print("  🧹 Cleaning up...")
            for method in ['cleanup', 'stop_training_mode']:
                if hasattr(self.external_mode, method):
                    try:
                        getattr(self.external_mode, method)()
                    except:
                        pass
            self.external_mode = None
        
        if self.mode_container:
            self.mode_stack.removeWidget(self.mode_container)
            self.mode_container.deleteLater()
            self.mode_container = None
    
    def back_to_mode_selection(self):
        print("◄ Back to selection...")
        self.cleanup_current_mode()
        
        self.footer.mode_info.setText("◈ SELECT TRAINING MODE")
        self.footer.mode_info.setStyleSheet(f"color: {Neon.CYAN};")
        
        self.mode_stack.setCurrentIndex(0)
    
    def close_training_mode(self):
        print("🚪 Closing Training Mode...")
        self.cleanup_current_mode()
        
        try:
            import hand_tracker
            hand_tracker.set_gesture_state(True)
        except:
            pass
        
        self.mode_closed.emit()
    
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    def cleanup(self):
        print("🧹 Page cleanup...")
        self.cleanup_current_mode()
    
        # Stop timers
        for widget in [self.grid_bg, self.data_streams, self.particles, 
                      self.title, self.footer, self.dashboard_btn]:  # ← Added dashboard_btn
            if hasattr(widget, 'timer'):
                widget.timer.stop()
    
        self.shared_tracker = None
    
    def closeEvent(self, event):
        self.cleanup()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    
    # Dark palette
    from PySide6.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#000510"))
    palette.setColor(QPalette.WindowText, QColor(Neon.TEXT))
    app.setPalette(palette)
    
    window = TrainingModePage()
    window.showMaximized()
    
    sys.exit(app.exec())