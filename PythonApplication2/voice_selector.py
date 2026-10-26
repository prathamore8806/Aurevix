"""
╔══════════════════════════════════════════════════════════════╗
║              🎤 VOICE GENDER SELECTOR DROPDOWN               ║
║         👨 Male Voice  |  👩 Female Voice                     ║
╚══════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize, QPoint, QTimer
from PySide6.QtGui import QFont, QColor


class VoiceGenderSelector(QFrame):
    """
    Dropdown popup for selecting Male/Female voice.
    
    Signals:
        voice_selected(str): Emits "male" or "female"
    """
    
    voice_selected = Signal(str)  # "male" or "female"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(220, 160)
        
        self._selected_gender = "female"  # Default
        self._build_ui()
        self._apply_styles()
    
    def _build_ui(self):
        """Build the dropdown UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # ═══════════════════════════════════════════════════════
        # TITLE
        # ═══════════════════════════════════════════════════════
        title = QLabel("🎤 Select Voice")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet("color: #E0E0E0; padding: 4px;")
        layout.addWidget(title)
        
        # ═══════════════════════════════════════════════════════
        # SEPARATOR
        # ═══════════════════════════════════════════════════════
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: rgba(0, 230, 118, 0.3); max-height: 1px;")
        layout.addWidget(separator)
        
        # ═══════════════════════════════════════════════════════
        # VOICE BUTTONS
        # ═══════════════════════════════════════════════════════
        
        # 👩 Female Voice Button
        self.female_btn = QPushButton("👩  Nova (Female)")
        self.male_btn = QPushButton("👨  Nick (Male)")
        self.female_btn.setFixedHeight(40)
        self.female_btn.setCursor(Qt.PointingHandCursor)
        self.female_btn.setFont(QFont("Segoe UI", 10))
        self.female_btn.clicked.connect(lambda: self._on_select("female"))
        layout.addWidget(self.female_btn)
        
        # 👨 Male Voice Button
        self.male_btn = QPushButton("👨  Male Voice")
        self.male_btn.setFixedHeight(40)
        self.male_btn.setCursor(Qt.PointingHandCursor)
        self.male_btn.setFont(QFont("Segoe UI", 10))
        self.male_btn.clicked.connect(lambda: self._on_select("male"))
        layout.addWidget(self.male_btn)
        
        # Update button styles
        self._update_selection_style()
    
    def _apply_styles(self):
        """Apply dark futuristic styles."""
        self.setStyleSheet("""
            VoiceGenderSelector {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 20, 40, 240),
                    stop:1 rgba(15, 15, 30, 250)
                );
                border: 1px solid rgba(0, 230, 118, 0.4);
                border-radius: 12px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 230, 118, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _update_selection_style(self):
        """Update button styles based on selection."""
        # Active style
        active_style = """
            QPushButton {
                background: rgba(0, 230, 118, 0.3);
                border: 2px solid rgba(0, 230, 118, 0.8);
                border-radius: 8px;
                color: #00E676;
                text-align: left;
                padding-left: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 230, 118, 0.4);
            }
        """
        
        # Inactive style
        inactive_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: #B0B0B0;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(0, 230, 118, 0.5);
                color: #E0E0E0;
            }
        """
        
        if self._selected_gender == "female":
            self.female_btn.setStyleSheet(active_style)
            self.female_btn.setText("👩  Nova (Female)  ✅")
            self.male_btn.setStyleSheet(inactive_style)
            self.male_btn.setText("👨  Nick (Male)")
        else:
            self.male_btn.setStyleSheet(active_style)
            self.male_btn.setText("👨  Nick (Male)  ✅")
            self.female_btn.setStyleSheet(inactive_style)
            self.female_btn.setText("👩  Nova (Female)")
    
    def _on_select(self, gender):
        """Handle voice selection."""
        self._selected_gender = gender
        self._update_selection_style()
        
        print(f"🎤 Voice selected: {'👩 Female' if gender == 'female' else '👨 Male'}")
        
        # Emit signal
        self.voice_selected.emit(gender)
        
        # Close dropdown after short delay
        QTimer.singleShot(300, self.close)
    
    def get_selected_gender(self):
        """Get currently selected gender."""
        return self._selected_gender
    
    def set_selected_gender(self, gender):
        """Set selected gender without emitting signal."""
        if gender in ("male", "female"):
            self._selected_gender = gender
            self._update_selection_style()
    
    def show_at(self, global_pos):
        """Show dropdown at specific position."""
        # Adjust position so dropdown appears above the button
        adjusted_pos = QPoint(
            global_pos.x() - self.width() // 2,
            global_pos.y() - self.height() - 10
        )
        self.move(adjusted_pos)
        self.show()
        self.raise_()