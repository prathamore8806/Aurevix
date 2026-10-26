"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ⬡ FUTURISTIC CARD SELECTOR                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, Property
from PySide6.QtGui import QColor

from ...config.colors import FuturisticColors


class FuturisticCard(QFrame):
    """
    Futuristic media type selection card.
    
    Features:
    - Icon, title, and subtitle display
    - Selection state with glow effect
    - Hover animations
    - Click signal emission
    
    Usage:
        card = FuturisticCard("🖼", "IMAGES", "PNG JPG BMP", "images")
        card.clicked.connect(on_card_selected)
        card.set_selected(True)
    """
    
    clicked = Signal(str)
    
    def __init__(self, icon: str, title: str, subtitle: str, card_id: str, parent=None):
        super().__init__(parent)
        
        self.card_id = card_id
        self.selected = False
        self._hover = False
        self._destroyed = False
        
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(140, 110)
        
        self._setup_ui(icon, title, subtitle)
        self._apply_style()
        
        # Glow effect
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor(FuturisticColors.CYAN))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)
        
        # Animation
        self._anim = QPropertyAnimation(self, b"glow_value")
        self._anim.setDuration(200)
    
    def _setup_ui(self, icon: str, title: str, subtitle: str):
        """Set up the card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 15, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            font-weight: bold;
            color: {FuturisticColors.TEXT_PRIMARY};
            background: transparent;
            letter-spacing: 1px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Subtitle
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 9px;
            color: {FuturisticColors.TEXT_MUTED};
            background: transparent;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_label)
    
    def _apply_style(self):
        """Apply styling based on selection state"""
        if self.selected:
            self.setStyleSheet(f"""
                FuturisticCard {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(0, 212, 255, 0.15),
                        stop:1 rgba(0, 180, 255, 0.08));
                    border: 2px solid {FuturisticColors.CYAN};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                FuturisticCard {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(15, 32, 56, 0.6),
                        stop:1 rgba(10, 22, 40, 0.8));
                    border: 1px solid rgba(0, 212, 255, 0.2);
                    border-radius: 8px;
                }}
                FuturisticCard:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(22, 42, 74, 0.8),
                        stop:1 rgba(15, 32, 56, 0.9));
                    border: 1px solid rgba(0, 212, 255, 0.5);
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
    def glow_value(self):
        """Get glow blur radius"""
        try:
            return self.glow.blurRadius()
        except:
            return 0
    
    @glow_value.setter
    def glow_value(self, value):
        """Set glow blur radius"""
        try:
            if self.glow:
                self.glow.setBlurRadius(value)
        except:
            pass
    
    def set_selected(self, selected: bool):
        """
        Set selection state.
        
        Args:
            selected: Whether the card is selected
        """
        self.selected = selected
        self._apply_style()
        
        if self._destroyed:
            return
        
        try:
            self._anim.stop()
            self._anim.setStartValue(self.glow.blurRadius())
            self._anim.setEndValue(20 if selected else 0)
            self._anim.start()
        except:
            pass
    
    def is_selected(self) -> bool:
        """Check if card is selected"""
        return self.selected
    
    def enterEvent(self, event):
        """Handle mouse enter"""
        if self._destroyed or self.selected:
            return super().enterEvent(event)
        
        try:
            self._anim.stop()
            self._anim.setStartValue(self.glow.blurRadius())
            self._anim.setEndValue(12)
            self._anim.start()
        except:
            pass
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        if self._destroyed or self.selected:
            return super().leaveEvent(event)
        
        try:
            self._anim.stop()
            self._anim.setStartValue(self.glow.blurRadius())
            self._anim.setEndValue(0)
            self._anim.start()
        except:
            pass
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if not self._destroyed:
            self.clicked.emit(self.card_id)
        super().mousePressEvent(event)