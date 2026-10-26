from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal

class Sidebar(QFrame):
    pageRequested = Signal(int)
    logoutRequested = Signal()
    profileEditRequested = Signal()
    exitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("sidebar")
        self.buttons = {}
        self._build_ui()

    def _build_ui(self):
        side_layout = QVBoxLayout(self)
        side_layout.setContentsMargins(8, 12, 8, 12)
        side_layout.setSpacing(4)

        # ═══════════════════════════════════════════════════════════════
        # 📋 NAVIGATION BUTTONS
        # 
        # NOTE: Gaming (8) and Training (9) are NOT in sidebar!
        #       They are opened via dashboard cards/buttons only.
        #
        # main.py stack order:
        # 0  = Dashboard
        # 1  = Gestures
        # 2  = Shortcuts
        # 3  = Logs
        # 4  = Settings
        # 5  = Preferences
        # 6  = AI Trainer
        # 7  = Calibration
        # 8  = Gaming Mode    ← NOT in sidebar (opened from dashboard)
        # 9  = Training Mode  ← NOT in sidebar (opened from dashboard)
        # ═══════════════════════════════════════════════════════════════

        pages = [
            ("🏠", "Dashboard", 0),
            ("🖐️", "Gestures", 1),
            ("⌨️", "Shortcuts", 2),
            ("📋", "Logs", 3),
            ("🔧", "Settings", 4),
            ("⚙️", "Preferences", 5),
            ("🤖", "AI Trainer", 6),
            ("🎯", "Calibration", 7),
            # Gaming (8) and Training (9) are NOT here - opened from dashboard only!
        ]

        for icon, name, page_idx in pages:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setObjectName("sideBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda checked, x=page_idx: self.pageRequested.emit(x))
            self.buttons[name] = btn
            side_layout.addWidget(btn)

        side_layout.addStretch()

        # Footer divider
        footer_div = QFrame()
        footer_div.setFixedHeight(1)
        footer_div.setStyleSheet("background: rgba(0, 212, 255, 0.08); margin: 0 8px;")
        side_layout.addWidget(footer_div)

        # Version label
        version_label = QLabel("  v2.0.0 Futuristic")
        version_label.setStyleSheet("color: #334455; font-size: 10px; padding: 4px 0; background: transparent;")
        side_layout.addWidget(version_label)

        # Exit button
        power_btn = QPushButton("⏻  Exit")
        power_btn.setCursor(Qt.PointingHandCursor)
        power_btn.setFixedHeight(38)
        power_btn.setStyleSheet("""
            QPushButton { background: rgba(255,50,50,0.1); border: 1px solid rgba(255,50,50,0.3);
                border-radius: 10px; color: #ff5252; font-size: 13px; font-weight: 600; }
            QPushButton:hover { background: rgba(255,50,50,0.25); border: 1px solid rgba(255,50,50,0.6); }
        """)
        power_btn.clicked.connect(self.exitRequested.emit)
        side_layout.addWidget(power_btn)

    def set_active_page(self, index):
        """Highlight active navigation button."""
        # ═══════════════════════════════════════════════════════════════
        # INDEX TO NAME MAPPING
        # Note: 8 (Gaming) and 9 (Training) have no sidebar buttons
        # ═══════════════════════════════════════════════════════════════
        idx_to_name = {
            0: "Dashboard",
            1: "Gestures",
            2: "Shortcuts",
            3: "Logs",
            4: "Settings",
            5: "Preferences",
            6: "AI Trainer",
            7: "Calibration",
            # 8: Gaming Mode - No sidebar button
            # 9: Training Mode - No sidebar button
        }
        
        # Reset all buttons
        for name, btn in self.buttons.items():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Highlight active button (if it exists in sidebar)
        active_name = idx_to_name.get(index, "")
        if active_name in self.buttons:
            active_btn = self.buttons[active_name]
            active_btn.setProperty("active", True)
            active_btn.style().unpolish(active_btn)
            active_btn.style().polish(active_btn)

    def set_user(self, user_data):
        """Kept for compatibility."""
        pass

    def set_guest(self):
        """Kept for compatibility."""
        pass