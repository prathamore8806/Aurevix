from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class GestureMappingRow(QFrame):
    def __init__(self, gesture_icon, gesture_name, action_name, color="#00d4ff", parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet("""
            QFrame { background: rgba(255,255,255,0.04); border-radius: 10px;
                     border: 1px solid rgba(255,255,255,0.06); }
            QFrame:hover { background: rgba(255,255,255,0.08);
                           border: 1px solid rgba(255,255,255,0.12); }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        icon = QLabel(gesture_icon)
        icon.setStyleSheet(f"font-size: 18px; background: transparent; color: {color};")
        icon.setFixedWidth(28)
        layout.addWidget(icon)

        name = QLabel(gesture_name)
        name.setStyleSheet("font-size: 13px; font-weight: 600; color: #c8d4e0; background: transparent;")
        layout.addWidget(name)

        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 14px; color: #556677; background: transparent;")
        arrow.setFixedWidth(20)
        layout.addWidget(arrow)

        action = QLabel(action_name)
        action.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {color}; background: transparent;")
        layout.addWidget(action)
        layout.addStretch()
