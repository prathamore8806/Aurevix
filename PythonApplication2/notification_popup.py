
# notification_popup.py - Toast Notification Popups

import math
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPoint
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPen

from notification_manager import Notification, NotificationType


class NotificationToast(QWidget):
    """Single toast notification popup"""
    
    def __init__(self, notification: Notification, parent=None):
        super().__init__(parent)
        self.notification = notification
        self._opacity = 0.0
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 90)
        
        self._build_ui()
        self._setup_animations()
        self._apply_shadow()
    
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        icon = QLabel(self.notification.icon)
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"""
            background: {self._get_color(0.2)};
            border-radius: 20px;
            font-size: 18px;
        """)
        layout.addWidget(icon)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(2)
        
        title = QLabel(self.notification.title)
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: white; background: transparent;")
        content.addWidget(title)
        
        message = QLabel(self.notification.message)
        message.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.7); background: transparent;")
        message.setWordWrap(True)
        content.addWidget(message)
        
        layout.addLayout(content, stretch=1)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
        """)
        close_btn.clicked.connect(self._dismiss)
        layout.addWidget(close_btn, alignment=Qt.AlignTop)
    
    def _get_color(self, alpha: float = 1.0) -> str:
        colors = {
            NotificationType.SUCCESS: f"rgba(0, 255, 136, {alpha})",
            NotificationType.ERROR: f"rgba(255, 85, 85, {alpha})",
            NotificationType.WARNING: f"rgba(255, 170, 0, {alpha})",
            NotificationType.INFO: f"rgba(0, 212, 255, {alpha})",
            NotificationType.CALIBRATION: f"rgba(138, 43, 226, {alpha})",
            NotificationType.GESTURE: f"rgba(255, 105, 180, {alpha})",
            NotificationType.SYSTEM: f"rgba(100, 149, 237, {alpha})",
        }
        return colors.get(self.notification.type, f"rgba(0, 212, 255, {alpha})")
    
    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
    
    def _setup_animations(self):
        self._fade_in = QPropertyAnimation(self, b"opacity")
        self._fade_in.setDuration(300)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        self._fade_out = QPropertyAnimation(self, b"opacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)
        self._fade_out.finished.connect(self.close)
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.update()
    
    opacity = Property(float, get_opacity, set_opacity)
    
    def show_toast(self, duration_ms: int = 4000):
        self.show()
        self._fade_in.start()
        QTimer.singleShot(duration_ms, self._dismiss)
    
    def _dismiss(self):
        self._fade_out.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)
        
        # Background
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(25, 25, 45, 245))
        gradient.setColorAt(1, QColor(35, 35, 55, 245))
        
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        
        # Left accent
        accent_color = QColor(self._get_color(1))
        painter.setBrush(accent_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 10, 4, self.height() - 20, 2, 2)


class NotificationToastManager(QWidget):
    """Manages toast notification display and positioning"""
    
    _instance = None
    
    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, parent=None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        
        self.toasts = []
        self.max_visible = 5
        self.spacing = 10
        self.margin_right = 20
        self.margin_top = 70  # Below top nav
        
        self.hide()  # Manager widget is invisible
    
    def show_toast(self, notification: Notification, duration_ms: int = 4000):
        """Show a toast notification"""
        toast = NotificationToast(notification)
        toast.show_toast(duration_ms)
        
        self.toasts.append(toast)
        if len(self.toasts) > self.max_visible:
            old_toast = self.toasts.pop(0)
            old_toast.close()
        
        self._reposition_toasts()
        
        # Clean up when toast closes
        def remove_toast():
            if toast in self.toasts:
                self.toasts.remove(toast)
                self._reposition_toasts()
        
        QTimer.singleShot(duration_ms + 500, remove_toast)
    
    def _reposition_toasts(self):
        """Reposition all visible toasts"""
        try:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            
            y = self.margin_top
            for toast in self.toasts:
                x = screen.width() - toast.width() - self.margin_right
                toast.move(x, y)
                y += toast.height() + self.spacing
        except:
            pass


def get_toast_manager() -> NotificationToastManager:
    return NotificationToastManager()