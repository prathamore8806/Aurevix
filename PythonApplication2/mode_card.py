from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from glass_card import GlassCard
from glowing_button import GlowingButton

class ModeCard(GlassCard):
    selected = Signal(str)

    def __init__(self, mode_name, icon, description, color="#00d4ff", parent=None):
        super().__init__(parent, border_color=color)
        self._mode_name = mode_name
        self._color = color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 32px; background: transparent; color: {color};")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel(mode_name)
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #e0e8f0; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(description)
        desc.setStyleSheet("font-size: 11px; color: #8899aa; background: transparent;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._select_btn = GlowingButton("Select", glow_color=color)
        self._select_btn.setFixedHeight(32)
        self._select_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid {color}40; border-radius: 8px;
                color: {color}; font-size: 12px; font-weight: 600; padding: 4px 16px;
            }}
            QPushButton:hover {{ background: {color}30; border: 1px solid {color}80; }}
        """)
        self._select_btn.clicked.connect(lambda: self.selected.emit(self._mode_name))
        layout.addWidget(self._select_btn)

    def set_selected(self, selected):
        if selected:
            self._select_btn.setText("✓ Active")
            self._select_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self._color}40; border: 1px solid {self._color}90;
                    border-radius: 8px; color: white; font-size: 12px;
                    font-weight: 700; padding: 4px 16px;
                }}
            """)
        else:
            self._select_btn.setText("Select")
            self._select_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid {self._color}40; border-radius: 8px;
                    color: {self._color}; font-size: 12px; font-weight: 600; padding: 4px 16px;
                }}
                QPushButton:hover {{ background: {self._color}30; border: 1px solid {self._color}80; }}
            """)
