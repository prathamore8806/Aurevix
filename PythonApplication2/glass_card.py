from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient, QPainterPath

class GlassCard(QFrame):
    def __init__(self, parent=None, border_color="#00d4ff", hover_glow=True):
        super().__init__(parent)
        self._border_color = border_color
        self._hover_glow = hover_glow
        self._hovered = False

    def enterEvent(self, event):
        if self._hover_glow:
            self._hovered = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._hover_glow:
            self._hovered = False
            self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h, r = self.width(), self.height(), 16
        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, w - 1, h - 1, r, r)

        bg = QLinearGradient(0, 0, w, h)
        if self._hovered:
            bg.setColorAt(0, QColor(255, 255, 255, 18))
            bg.setColorAt(1, QColor(255, 255, 255, 8))
        else:
            bg.setColorAt(0, QColor(255, 255, 255, 10))
            bg.setColorAt(1, QColor(255, 255, 255, 4))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawPath(path)

        border = QColor(self._border_color)
        border.setAlpha(60 if self._hovered else 30)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.end()
        super().paintEvent(event)
