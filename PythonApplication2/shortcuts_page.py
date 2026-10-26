from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Signal
import config
from glowing_button import GlowingButton


class ShortcutsPage(QWidget):
    shortcutsToggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("⌨️ Keyboard Shortcuts")
        title.setObjectName("title")
        layout.addWidget(title)

        toggle_card = QFrame()
        toggle_card.setObjectName("card")
        tl = QVBoxLayout(toggle_card)

        self.shortcuts_toggle = QCheckBox("Enable Keyboard Shortcuts")
        self.shortcuts_toggle.setChecked(config.shortcuts_enabled)
        self.shortcuts_toggle.setStyleSheet("""
            QCheckBox { color: white; font-size: 15px; font-weight: bold; spacing: 10px; }
            QCheckBox::indicator { width: 20px; height: 20px; border-radius: 5px;
                border: 2px solid rgba(0,212,255,0.5); background: rgba(22,27,34,0.8); }
            QCheckBox::indicator:checked { background: rgba(0,212,255,0.4); border: 2px solid rgba(0,212,255,0.8); }
        """)
        self.shortcuts_toggle.stateChanged.connect(self._on_shortcuts_toggled)
        tl.addWidget(self.shortcuts_toggle)
        layout.addWidget(toggle_card)

        row1 = QHBoxLayout()
        row1.addWidget(self._shortcut_card("🎯 Mode Shortcuts", [
            ("1", "Desktop Mode", "🖥"), ("2", "Gaming Mode", "🎮"), ("3", "Draw Mode", "✏️"),
        ]))
        row1.addWidget(self._shortcut_card("⚡ Action Shortcuts", [
            ("C", "Clear Canvas", "🗑"), ("M", "Toggle Mirror", "🪞"), ("B", "Toggle Blur", "🔒"),
        ]))
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self._shortcut_card("📷 Camera Shortcuts", [
            ("F", "Toggle Focus", "🎯"), ("+", "Scroll Speed +", "⬆️"), ("-", "Scroll Speed -", "⬇️"),
        ]))
        row2.addWidget(self._shortcut_card("🔧 System Shortcuts", [
            ("H", "Hide/Show Tracker", "👁"), ("Q", "Quit Tracker", "❌"), ("Esc", "Emergency Stop", "🛑"),
        ]))
        layout.addLayout(row2)

        status_card = QFrame()
        status_card.setObjectName("card")
        sl = QVBoxLayout(status_card)
        st = QLabel("📊 Current Status")
        st.setObjectName("cardTitle")
        sl.addWidget(st)
        self.shortcut_status = QLabel(self._get_shortcut_status_text())
        self.shortcut_status.setStyleSheet("color: #00d4ff; font-size: 13px;")
        sl.addWidget(self.shortcut_status)
        layout.addWidget(status_card)
        layout.addStretch()

    def _on_shortcuts_toggled(self, state):
        config.shortcuts_enabled = bool(state)
        config.save_config()
        self.shortcut_status.setText(self._get_shortcut_status_text())
        self.shortcutsToggled.emit(config.shortcuts_enabled)

    def _get_shortcut_status_text(self):
        return (f"Shortcuts: {'✅ Enabled' if config.shortcuts_enabled else '❌ Disabled'}\n"
                f"Mirror: {'ON' if config.mirror else 'OFF'}\n"
                f"Face Blur: {'ON' if config.face_blur else 'OFF'}\nScroll Speed: {config.scroll_speed}")

    def _shortcut_card(self, title, shortcuts):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        layout.addWidget(t)
        for key, desc, emoji_icon in shortcuts:
            row = QHBoxLayout()
            kl = QLabel(key)
            kl.setFixedSize(40, 32)
            kl.setAlignment(Qt.AlignCenter)
            kl.setStyleSheet("""
                background: rgba(0,212,255,0.12); color: #00d4ff; font-weight: 800;
                font-size: 14px; border-radius: 8px; border: 1px solid rgba(0,212,255,0.3);
            """)
            row.addWidget(kl)
            el = QLabel(emoji_icon)
            el.setFixedWidth(30)
            el.setStyleSheet("font-size: 16px; background: transparent;")
            row.addWidget(el)
            dl = QLabel(desc)
            dl.setStyleSheet("color: #c9d1d9; font-size: 13px; background: transparent;")
            row.addWidget(dl)
            row.addStretch()
            layout.addLayout(row)
        return card

    def update_status(self):
        self.shortcut_status.setText(self._get_shortcut_status_text())
