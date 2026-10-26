"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🔷 FUTURISTIC BUTTON                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor

from ...config.colors import FuturisticColors


class FuturisticButton(QPushButton):
    """
    Sleek futuristic button with neon glow effect.
    
    Features:
    - Neon glow on hover
    - Smooth animations
    - Customizable accent color
    - Cyberpunk aesthetic
    
    Usage:
        btn = FuturisticButton("LAUNCH", FuturisticColors.CYAN)
        btn.clicked.connect(on_click)
    """
    
    def __init__(self, text: str, accent_color: str = "#00d4ff", parent=None):
        super().__init__(text, parent)
        
        self.accent_color = accent_color
        self._glow_intensity = 0
        self._destroyed = False
        
        self.setCursor(Qt.PointingHandCursor)
        
        # Glow effect
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor(accent_color))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)
        
        # Animation
        self._anim = QPropertyAnimation(self, b"glow_intensity")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self._apply_style()
    
    def _apply_style(self):
        """Apply futuristic styling"""
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 32, 56, 0.9),
                    stop:1 rgba(10, 22, 40, 0.95));
                border: 1px solid {self.accent_color}60;
                border-left: 3px solid {self.accent_color};
                border-radius: 4px;
                color: {self.accent_color};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                font-weight: bold;
                padding: 12px 24px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(22, 42, 74, 0.95),
                    stop:1 rgba(15, 32, 56, 0.98));
                border: 1px solid {self.accent_color};
                color: white;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10, 22, 40, 1),
                    stop:1 rgba(5, 16, 32, 1));
            }}
            QPushButton:disabled {{
                background: rgba(15, 32, 56, 0.4);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-left: 3px solid rgba(100, 116, 139, 0.3);
                color: rgba(100, 116, 139, 0.5);
            }}
        """)
    
    def cleanup(self):
        """Clean up resources"""
        self._destroyed = True
        try:
            if self._anim:
                self._anim.stop()
        except:
            pass
    
    @Property(float)
    def glow_intensity(self):
        """Get glow intensity"""
        return self._glow_intensity
    
    @glow_intensity.setter
    def glow_intensity(self, value):
        """Set glow intensity"""
        self._glow_intensity = value
        try:
            if self.glow:
                self.glow.setBlurRadius(value)
        except:
            pass
    
    def enterEvent(self, event):
        """Handle mouse enter"""
        if self._destroyed:
            return
        try:
            self._anim.stop()
            self._anim.setStartValue(self._glow_intensity)
            self._anim.setEndValue(25)
            self._anim.start()
        except:
            pass
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        if self._destroyed:
            return
        try:
            self._anim.stop()
            self._anim.setStartValue(self._glow_intensity)
            self._anim.setEndValue(0)
            self._anim.start()
        except:
            pass
        super().leaveEvent(event)
    
    def set_accent_color(self, color: str):
        """
        Change accent color.
        
        Args:
            color: Hex color string (e.g., "#00d4ff")
        """
        self.accent_color = color
        try:
            if self.glow:
                self.glow.setColor(QColor(color))
        except:
            pass
        self._apply_style()