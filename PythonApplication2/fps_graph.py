from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient, QPainterPath, QFont

class FPSGraphWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setMinimumWidth(200)
        self._data = [0] * 60
        self._max_val = 60

    def add_fps_value(self, fps):
        self._data.append(fps)
        if len(self._data) > 60:
            self._data.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        painter.setPen(Qt.NoPen)
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(10, 10, 40, 180))
        bg.setColorAt(1, QColor(5, 5, 25, 200))
        painter.setBrush(QBrush(bg))
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 12, 12)
        painter.drawPath(path)

        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        for i in range(1, 4):
            y = int(h * i / 4)
            painter.drawLine(10, y, w - 10, y)

        if len(self._data) < 2:
            painter.end()
            return

        points = []
        mx, my = 15, 15
        dw = w - 2 * mx
        dh = h - 2 * my

        for i, val in enumerate(self._data):
            x = mx + (i / max(len(self._data) - 1, 1)) * dw
            y = my + dh - (val / max(self._max_val, 1)) * dh
            points.append((x, y))

        fill_path = QPainterPath()
        fill_path.moveTo(points[0][0], h - my)
        for px, py in points:
            fill_path.lineTo(px, py)
        fill_path.lineTo(points[-1][0], h - my)
        fill_path.closeSubpath()

        fill_grad = QLinearGradient(0, 0, 0, h)
        fill_grad.setColorAt(0, QColor(0, 212, 255, 60))
        fill_grad.setColorAt(1, QColor(0, 100, 200, 10))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill_grad))
        painter.drawPath(fill_path)

        line_path = QPainterPath()
        line_path.moveTo(points[0][0], points[0][1])
        for px, py in points[1:]:
            line_path.lineTo(px, py)
        painter.setPen(QPen(QColor("#00d4ff"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(line_path)

        if self._data:
            current = self._data[-1]
            painter.setPen(QColor("#00d4ff"))
            font = QFont("Inter", 9, QFont.Bold)
            painter.setFont(font)
            painter.drawText(w - 50, 20, f"{current} FPS")

        painter.end()
