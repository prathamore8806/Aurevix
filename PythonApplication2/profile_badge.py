from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class ProfileBadge(QFrame):
    def __init__(self, name, icon, color="#00d4ff", active=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,{'0.08' if active else '0.04'});
                border-radius: 12px;
                border: 1px solid {color + ('60' if active else '20')};
            }}
            QFrame:hover {{ background: rgba(255,255,255,0.10); border: 1px solid {color}50; }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        icon_l = QLabel(icon)
        icon_l.setStyleSheet(f"font-size: 20px; background: transparent; color: {color};")
        layout.addWidget(icon_l)

        name_l = QLabel(name)
        name_l.setStyleSheet("font-size: 13px; font-weight: 600; color: #d0daea; background: transparent;")
        layout.addWidget(name_l)
        layout.addStretch()

        if active:
            badge = QLabel("● Active")
            badge.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: 600; background: transparent;")
            layout.addWidget(badge)
