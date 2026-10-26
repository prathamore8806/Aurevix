from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QRadialGradient, QFont

class CircularActivateButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setFixedSize(120, 120)
        self.setCursor(Qt.PointingHandCursor)
        self._active = False
        self._pulse_radius = 0

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.start(50)

    def _update_pulse(self):
        self._pulse_radius = (self._pulse_radius + 2) % 60
        self.update()

    def set_active(self, active):
        self._active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        base_radius = 50

        if self._active:
            for i in range(3):
                glow_r = base_radius + 8 + i * 6 + self._pulse_radius * 0.3
                opacity = max(0, 0.15 - i * 0.04)
                painter.setPen(Qt.NoPen)
                glow_color = QColor("#00d4ff")
                glow_color.setAlphaF(opacity)
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(center, int(glow_r), int(glow_r))

        gradient = QRadialGradient(center.x(), center.y(), base_radius)
        if self._active:
            gradient.setColorAt(0, QColor(0, 212, 255, 200))
            gradient.setColorAt(0.7, QColor(0, 150, 200, 150))
            gradient.setColorAt(1, QColor(0, 80, 120, 100))
        else:
            gradient.setColorAt(0, QColor(60, 60, 100, 180))
            gradient.setColorAt(0.7, QColor(40, 40, 80, 150))
            gradient.setColorAt(1, QColor(20, 20, 50, 120))

        painter.setPen(QPen(QColor("#00d4ff" if self._active else "#3a3a6a"), 2))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, base_radius, base_radius)

        painter.setPen(QColor("#ffffff" if self._active else "#8888aa"))
        font = QFont("Inter", 11, QFont.Bold)
        painter.setFont(font)
        text = "ACTIVE" if self._active else "ACTIVATE"
        painter.drawText(self.rect(), Qt.AlignCenter, text)

        icon_font = QFont("Inter", 22)
        painter.setFont(icon_font)
        icon_rect = QRect(self.rect().x(), self.rect().y() - 14,
                          self.rect().width(), self.rect().height())
        painter.drawText(icon_rect, Qt.AlignCenter, "⚡")
        painter.end()

    def cleanup(self):
        self._pulse_timer.stop()
