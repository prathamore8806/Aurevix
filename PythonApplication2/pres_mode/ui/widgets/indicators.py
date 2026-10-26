"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🎯 GESTURE INDICATOR WIDGET                          ║
║                         FIXED: Proper Fade Timing                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from ...config.colors import FuturisticColors


class GestureIndicator(QWidget):
    """
    Visual indicator for detected gestures.
    
    Features:
    - Shows gesture name with icon
    - Optional sub-text for additional info
    - Customizable indicator color
    - Auto-fade after display
    - FIXED: Proper fade timing
    
    Usage:
        indicator = GestureIndicator(parent)
        indicator.move(x, y)
        
        # Show a gesture
        indicator.show_gesture("NEXT SLIDE", "👉", "Slide 2", QColor("#00d4ff"))
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(400, 120)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.current_gesture = ""
        self.sub_text = ""
        self.opacity = 0.0
        self.indicator_color = QColor(0, 212, 255)
        self._destroyed = False
        
        # Fade timer
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_out)
    
    def cleanup(self):
        """Clean up resources"""
        self._destroyed = True
        try:
            if self._fade_timer:
                self._fade_timer.stop()
        except:
            pass
    
    def show_gesture(
        self,
        gesture_name: str,
        icon: str = "✋",
        sub_text: str = "",
        color: QColor = None
    ):
        """
        Show gesture indicator with optional subtext and color.
        
        Args:
            gesture_name: Name of the gesture (e.g., "NEXT SLIDE")
            icon: Emoji icon to display (e.g., "👉")
            sub_text: Optional secondary text (e.g., "Slide 2")
            color: Indicator color (default: cyan)
        """
        if self._destroyed:
            return
        
        try:
            self.current_gesture = f"{icon} {gesture_name}"
            self.sub_text = sub_text
            self.indicator_color = color if color else QColor(0, 212, 255)
            self.opacity = 1.0
            self.update()
            
            # Stop any existing fade
            self._fade_timer.stop()
            
            # Start fading after 500ms delay, then fade quickly
            QTimer.singleShot(500, self._start_fade)
        except:
            pass
    
    def _start_fade(self):
        """Start the fade out animation"""
        if not self._destroyed:
            self._fade_timer.start(30)  # 30ms interval for smooth fade
    
    def _fade_out(self):
        """Fade out the indicator"""
        if self._destroyed:
            return
        
        try:
            self.opacity -= 0.08  # Fade out in ~375ms (0.08 * 12.5 = 1.0)
            if self.opacity <= 0:
                self.opacity = 0
                self._fade_timer.stop()
            self.update()
        except:
            pass
    
    def hide_immediately(self):
        """Hide the indicator immediately without fade"""
        if self._destroyed:
            return
        
        try:
            self._fade_timer.stop()
            self.opacity = 0
            self.update()
        except:
            pass
    
    def set_fade_speed(self, decrement: float):
        """
        Set fade speed.
        
        Args:
            decrement: Opacity decrement per frame (0.01 to 0.2)
        """
        self._fade_decrement = max(0.01, min(0.2, decrement))
    
    def paintEvent(self, event):
        """Paint the indicator"""
        if self._destroyed or self.opacity <= 0:
            return
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # ═══════════════════════════════════════════════════════════════
            # Background
            # ═══════════════════════════════════════════════════════════════
            bg_color = QColor(self.indicator_color)
            bg_color.setAlphaF(0.15 * self.opacity)
            
            border_color = QColor(self.indicator_color)
            border_color.setAlphaF(0.8 * self.opacity)
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 2))
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 12, 12)
            
            # ═══════════════════════════════════════════════════════════════
            # Main text
            # ═══════════════════════════════════════════════════════════════
            text_color = QColor(255, 255, 255, int(255 * self.opacity))
            painter.setPen(QPen(text_color))
            
            font = QFont("Consolas", 22, QFont.Bold)
            painter.setFont(font)
            
            main_rect = self.rect()
            if self.sub_text:
                main_rect.setHeight(main_rect.height() - 25)
            
            painter.drawText(main_rect, Qt.AlignCenter, self.current_gesture)
            
            # ═══════════════════════════════════════════════════════════════
            # Sub text
            # ═══════════════════════════════════════════════════════════════
            if self.sub_text:
                sub_color = QColor(self.indicator_color)
                sub_color.setAlphaF(0.9 * self.opacity)
                painter.setPen(QPen(sub_color))
                
                font = QFont("Consolas", 11)
                painter.setFont(font)
                
                sub_rect = QRect(0, self.height() - 35, self.width(), 30)
                painter.drawText(sub_rect, Qt.AlignCenter, self.sub_text)
                
        except:
            pass
    
    def is_visible_indicator(self) -> bool:
        """Check if indicator is currently visible"""
        return self.opacity > 0


# ═══════════════════════════════════════════════════════════════════════════════
#                         🔒 ZOOM LOCK INDICATOR
# ═══════════════════════════════════════════════════════════════════════════════

class ZoomLockIndicator(QWidget):
    """
    Persistent zoom lock status indicator.
    
    Shows a small lock icon when zoom is locked.
    
    Usage:
        indicator = ZoomLockIndicator(parent)
        indicator.set_locked(True)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(60, 30)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._is_locked = False
        self._destroyed = False
    
    def set_locked(self, locked: bool):
        """
        Set lock state.
        
        Args:
            locked: Whether zoom is locked
        """
        self._is_locked = locked
        self.update()
    
    def is_locked(self) -> bool:
        """Check if locked"""
        return self._is_locked
    
    def cleanup(self):
        """Clean up resources"""
        self._destroyed = True
    
    def paintEvent(self, event):
        """Paint the lock indicator"""
        if self._destroyed or not self._is_locked:
            return
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Background
            bg_color = QColor(FuturisticColors.YELLOW)
            bg_color.setAlphaF(0.2)
            
            border_color = QColor(FuturisticColors.YELLOW)
            border_color.setAlphaF(0.8)
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
            
            # Lock icon
            text_color = QColor(FuturisticColors.YELLOW)
            painter.setPen(QPen(text_color))
            
            font = QFont("Consolas", 14)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "🔒")
            
        except:
            pass