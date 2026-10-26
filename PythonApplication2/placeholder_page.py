from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class PlaceholderPage(QWidget):
    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        self._build_ui(title, description)
    
    def _build_ui(self, title, description):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 40, 30, 30)
        layout.setSpacing(16)

        icon_label = QLabel(title.split(" ")[0])
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #e0e8f0; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 14px; color: #7788aa; background: transparent;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)

        coming = QLabel("🚀 Coming Soon")
        coming.setStyleSheet("""
            font-size: 16px; color: #00d4ff; font-weight: 600; padding: 16px 32px;
            background: rgba(0,212,255,0.08); border: 1px solid rgba(0,212,255,0.2); border-radius: 12px;
        """)
        coming.setAlignment(Qt.AlignCenter)
        layout.addWidget(coming, alignment=Qt.AlignCenter)
        layout.addStretch()
