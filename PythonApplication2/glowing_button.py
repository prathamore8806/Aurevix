from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class GlowingButton(QPushButton):
    def __init__(self, text="", parent=None, glow_color="#00d4ff"):
        super().__init__(text, parent)
        self._glow_color = glow_color
        self._base_glow = 15
        self.setCursor(Qt.PointingHandCursor)
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setBlurRadius(self._base_glow)
        self._shadow.setColor(QColor(glow_color))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        self._shadow.setBlurRadius(30)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(self._base_glow)
        super().leaveEvent(event)
