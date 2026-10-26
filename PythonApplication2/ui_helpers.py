from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

def apply_neon_glow(widget, color="#00d4ff", radius=20, offset=(0, 0)):
    """Apply neon glow effect to a widget"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setColor(QColor(color))
    shadow.setOffset(offset[0], offset[1])
    widget.setGraphicsEffect(shadow)
