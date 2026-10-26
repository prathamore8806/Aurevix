from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QRadialGradient, QFont

class AIStatusIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 36)
        self._active = False
        self._blink = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start(800)

    def _toggle_blink(self):
        self._blink = not self._blink
        self.update()

    def set_active(self, active):
        self._active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        bg_c = QColor(0, 180, 100, 40) if self._active else QColor(180, 50, 50, 40)
        bd_c = QColor("#00e676") if self._active else QColor("#ff5252")
        painter.setPen(QPen(bd_c, 1.5))
        painter.setBrush(QBrush(bg_c))
        painter.drawRoundedRect(1, 1, w - 2, h - 2, h // 2, h // 2)

        dot_x, dot_y, dot_r = 18, h // 2, 5
        if self._active and self._blink:
            glow = QRadialGradient(dot_x, dot_y, dot_r * 3)
            glow.setColorAt(0, QColor(0, 230, 118, 100))
            glow.setColorAt(1, QColor(0, 230, 118, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPoint(dot_x, dot_y), dot_r * 3, dot_r * 3)

        dot_color = QColor("#00e676") if self._active else QColor("#ff5252")
        if not self._active and not self._blink:
            dot_color.setAlpha(80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(QPoint(dot_x, dot_y), dot_r, dot_r)

        painter.setPen(QColor("#e0e0e0"))
        painter.setFont(QFont("Inter", 10, QFont.Bold))
        text = "AI Active" if self._active else "AI Inactive"
        painter.drawText(QRect(32, 0, w - 36, h), Qt.AlignVCenter, text)
        painter.end()

    def cleanup(self):
        self._blink_timer.stop()
