"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ⬡ DECORATIVE WIDGETS                                 ║
║                    Hexagon Decorations & Scanline Effects                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient

from ...config.colors import FuturisticColors


# ═══════════════════════════════════════════════════════════════════════════════
#                         ⬡ HEXAGON DECORATION WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class HexagonDecor(QWidget):
    """
    Animated hexagon decoration for futuristic feel.
    
    Features:
    - Rotating hexagon outline
    - Pulsing opacity animation
    - Customizable size and color
    
    Usage:
        hex_decor = HexagonDecor(size=40, color="#00d4ff")
        hex_decor.move(100, 50)
    """
    
    def __init__(self, size: int = 40, color: str = "#00d4ff", parent=None):
        super().__init__(parent)
        
        self.hex_size = size
        self.color = color
        self.opacity = 0.3
        self.rotation = 0
        self._destroyed = False
        
        self.setFixedSize(size + 10, size + 10)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)
    
    def _animate(self):
        """Animate rotation and opacity"""
        if self._destroyed:
            return
        
        try:
            self.rotation += 0.5
            self.opacity = 0.2 + 0.15 * math.sin(self.rotation * 0.1)
            self.update()
        except:
            pass
    
    def stop_animation(self):
        """Stop the animation"""
        self._destroyed = True
        try:
            if self.timer:
                self.timer.stop()
        except:
            pass
    
    def start_animation(self):
        """Start/resume the animation"""
        if not self._destroyed:
            self.timer.start(50)
    
    def set_color(self, color: str):
        """
        Change hexagon color.
        
        Args:
            color: Hex color string (e.g., "#00d4ff")
        """
        self.color = color
        self.update()
    
    def set_size(self, size: int):
        """
        Change hexagon size.
        
        Args:
            size: Size in pixels
        """
        self.hex_size = size
        self.setFixedSize(size + 10, size + 10)
        self.update()
    
    def paintEvent(self, event):
        """Paint the hexagon"""
        if self._destroyed:
            return
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Translate to center and rotate
            center = self.rect().center()
            painter.translate(center)
            painter.rotate(self.rotation)
            
            # Create hexagon path
            path = QPainterPath()
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 2
                x = self.hex_size / 2 * math.cos(angle)
                y = self.hex_size / 2 * math.sin(angle)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            path.closeSubpath()
            
            # Draw hexagon outline
            color = QColor(self.color)
            color.setAlphaF(self.opacity)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawPath(path)
            
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#                         ▊ SCAN LINE OVERLAY EFFECT
# ═══════════════════════════════════════════════════════════════════════════════

class ScanLineOverlay(QWidget):
    """
    Subtle scanline effect for CRT/futuristic look.
    
    Features:
    - Horizontal scanlines
    - Animated scanning beam
    - Transparent for mouse events
    
    Usage:
        scanlines = ScanLineOverlay(parent_widget)
        scanlines.setGeometry(0, 0, width, height)
        scanlines.lower()  # Send to back
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._destroyed = False
        self.scan_offset = 0
        
        # Make transparent to mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_scan)
        self.timer.start(30)
    
    def _animate_scan(self):
        """Animate the scanning beam"""
        if self._destroyed:
            return
        
        try:
            self.scan_offset = (self.scan_offset + 1) % 100
            self.update()
        except:
            pass
    
    def stop_animation(self):
        """Stop the animation"""
        self._destroyed = True
        try:
            if self.timer:
                self.timer.stop()
        except:
            pass
    
    def start_animation(self):
        """Start/resume the animation"""
        if not self._destroyed:
            self.timer.start(30)
    
    def set_scan_speed(self, interval_ms: int):
        """
        Set scan animation speed.
        
        Args:
            interval_ms: Timer interval in milliseconds (lower = faster)
        """
        try:
            self.timer.setInterval(max(10, interval_ms))
        except:
            pass
    
    def paintEvent(self, event):
        """Paint the scanline effect"""
        if self._destroyed:
            return
        
        try:
            painter = QPainter(self)
            
            # Draw horizontal scanlines
            pen = QPen(QColor(0, 212, 255, 8))
            painter.setPen(pen)
            
            for y in range(0, self.height(), 4):
                painter.drawLine(0, y, self.width(), y)
            
            # Draw animated scanning beam
            scan_y = int((self.scan_offset / 100) * self.height())
            gradient = QLinearGradient(0, scan_y - 20, 0, scan_y + 20)
            gradient.setColorAt(0, QColor(0, 212, 255, 0))
            gradient.setColorAt(0.5, QColor(0, 212, 255, 30))
            gradient.setColorAt(1, QColor(0, 212, 255, 0))
            
            painter.fillRect(0, scan_y - 20, self.width(), 40, gradient)
            
        except:
            pass