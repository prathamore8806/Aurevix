import os
import base64
import re
from io import BytesIO

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QMenu, QGraphicsDropShadowEffect,
    QLineEdit, QDialog, QTextEdit, QFileDialog,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QRect, QTimer
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QFont, QAction,
    QPixmap, QImage, QBrush, QPen, QRegion, QLinearGradient
)

import database


# ─── AVATAR WIDGET WITH DP SUPPORT ──────────────────────────────────
class AvatarWidget(QWidget):
    """Circular avatar: shows uploaded image or initials fallback."""
    clicked = Signal()

    def __init__(self, initials="?", color="#2563eb", size=36, parent=None):
        super().__init__(parent)
        self.initials = initials
        self.color = color
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self._pixmap = None
        self._has_image = False

    def set_image_from_bytes(self, image_bytes):
        """Load avatar from raw bytes (from database BLOB)."""
        if image_bytes:
            img = QImage()
            if img.loadFromData(image_bytes):
                self._pixmap = QPixmap.fromImage(img)
                self._has_image = True
                self.update()
                return True
        self._pixmap = None
        self._has_image = False
        self.update()
        return False

    def set_image_from_b64(self, b64_string):
        """Load avatar from base64 encoded string."""
        if b64_string:
            try:
                raw = base64.b64decode(b64_string)
                return self.set_image_from_bytes(raw)
            except Exception:
                pass
        self._pixmap = None
        self._has_image = False
        self.update()
        return False

    def set_image_from_path(self, path):
        """Load avatar from file path."""
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._pixmap = pixmap
                self._has_image = True
                self.update()
                return True
        return False

    def clear_image(self):
        """Remove profile picture, revert to initials."""
        self._pixmap = None
        self._has_image = False
        self.update()

    def update_avatar(self, initials, color):
        """Update initials and color (fallback when no image)."""
        self.initials = initials
        self.color = color
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size

        if self._has_image and self._pixmap:
            scaled = self._pixmap.scaled(
                s, s,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            x_off = (scaled.width() - s) // 2
            y_off = (scaled.height() - s) // 2
            cropped = scaled.copy(x_off, y_off, s, s)

            mask = QPixmap(s, s)
            mask.fill(Qt.transparent)
            mask_painter = QPainter(mask)
            mask_painter.setRenderHint(QPainter.Antialiasing)
            mask_painter.setBrush(Qt.white)
            mask_painter.setPen(Qt.NoPen)
            mask_painter.drawEllipse(0, 0, s, s)
            mask_painter.end()

            cropped.setMask(mask.createMaskFromColor(
                Qt.transparent, Qt.MaskInColor
            ))

            path = QPainterPath()
            path.addEllipse(0, 0, s, s)
            p.setClipPath(path)
            p.drawPixmap(0, 0, cropped)
            p.setClipping(False)

            # Glow ring
            p.setPen(QPen(QColor(37, 99, 235, 100), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(1, 1, s - 2, s - 2)

            # Online indicator
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#22c55e"))
            dot_size = max(8, s // 5)
            p.drawEllipse(
                s - dot_size - 1, s - dot_size - 1,
                dot_size, dot_size
            )
            p.setPen(QPen(QColor("#0f172a"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(
                s - dot_size - 1, s - dot_size - 1,
                dot_size, dot_size
            )

        else:
            # Gradient background
            gradient = QLinearGradient(0, 0, s, s)
            gradient.setColorAt(0, QColor(self.color))
            gradient.setColorAt(1, QColor(self.color).darker(120))

            path = QPainterPath()
            path.addEllipse(0, 0, s, s)
            p.fillPath(path, gradient)

            # Shine effect
            p.setBrush(QColor(255, 255, 255, 30))
            p.setPen(Qt.NoPen)
            half_path = QPainterPath()
            half_path.addEllipse(0, 0, s, s // 2 + 4)
            p.drawPath(half_path & path)

            # Border glow
            p.setPen(QPen(QColor(255, 255, 255, 50), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(1, 1, s - 2, s - 2)

            # Initials
            p.setPen(QColor("white"))
            font_size = max(8, s // 3)
            font = QFont("Inter", font_size, QFont.Bold)
            p.setFont(font)
            p.drawText(self.rect(), Qt.AlignCenter, self.initials.upper())

        p.end()


# ─── LARGE AVATAR FOR PROFILE EDIT ──────────────────────────────────
class LargeAvatarWidget(AvatarWidget):
    """Bigger avatar with upload overlay on hover."""

    def __init__(self, initials="?", color="#2563eb", size=100, parent=None):
        super().__init__(initials, color, size, parent)
        self._hovering = False

    def enterEvent(self, event):
        self._hovering = True
        self.update()

    def leaveEvent(self, event):
        self._hovering = False
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._hovering:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            s = self._size

            # Dark overlay with gradient
            path = QPainterPath()
            path.addEllipse(0, 0, s, s)

            gradient = QLinearGradient(0, 0, 0, s)
            gradient.setColorAt(0, QColor(0, 0, 0, 160))
            gradient.setColorAt(1, QColor(0, 0, 0, 200))
            p.fillPath(path, gradient)

            # Upload icon and text
            p.setPen(QColor("white"))
            font = QFont("Inter", s // 8, QFont.Bold)
            p.setFont(font)
            p.drawText(self.rect().adjusted(0, -10, 0, 0), Qt.AlignCenter, "📷")

            font2 = QFont("Inter", s // 10)
            p.setFont(font2)
            p.drawText(self.rect().adjusted(0, 20, 0, 0), Qt.AlignCenter, "Change")

            p.end()


# ─── MODERN STYLED INPUT ────────────────────────────────────────────
class ModernInput(QLineEdit):
    """Modern styled input field."""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(48)
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                color: #e2e8f0;
                font-size: 13px;
                font-family: 'Inter', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
                background: rgba(37, 99, 235, 0.05);
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)


# ─── MODERN STYLED TEXT AREA ────────────────────────────────────────
class ModernTextEdit(QTextEdit):
    """Modern styled text area."""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                color: #e2e8f0;
                font-size: 13px;
                font-family: 'Inter', sans-serif;
            }
            QTextEdit:focus {
                border: 1px solid #2563eb;
                background: rgba(37, 99, 235, 0.05);
            }
        """)


# ─── MODERN BUTTON ──────────────────────────────────────────────────
class ModernButton(QPushButton):
    """Modern styled button."""

    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Inter", 13, QFont.Bold))

        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1d4ed8, stop:1 #2563eb);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-weight: 700;
                    font-size: 14px;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2563eb, stop:1 #3b82f6);
                }
                QPushButton:pressed {
                    background: #1d4ed8;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    color: #94a3b8;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #e2e8f0;
                }
            """)


# ─── STATUS LABEL ───────────────────────────────────────────────────
class StatusLabel(QLabel):
    """Animated status message label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(40)
        self.setStyleSheet("color: transparent; font-size: 12px;")
        self.hide()

    def show_error(self, msg):
        self.setText(f"❌  {msg}")
        self.setStyleSheet("""
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        """)
        self.show()
        QTimer.singleShot(5000, self.hide)

    def show_success(self, msg):
        self.setText(f"✅  {msg}")
        self.setStyleSheet("""
            color: #86efac;
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        """)
        self.show()
        QTimer.singleShot(3000, self.hide)


# ─── PROFILE WIDGET (SIDEBAR) ───────────────────────────────────────
class ProfileWidget(QWidget):
    """Top-right profile badge with dropdown menu."""
    logoutClicked = Signal()
    profileClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        self.avatar = AvatarWidget("?", "#475569", 40)
        layout.addWidget(self.avatar)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel("Guest")
        self.name_label.setStyleSheet("""
            font-size: 14px; font-weight: 700; color: #f1f5f9;
            background: transparent; border: none;
        """)

        self.status_label = QLabel("Not signed in")
        self.status_label.setStyleSheet("""
            font-size: 11px; color: #64748b;
            background: transparent; border: none;
        """)

        text_col.addWidget(self.name_label)
        text_col.addWidget(self.status_label)
        layout.addLayout(text_col)

        layout.addStretch()

        arrow = QLabel("▾")
        arrow.setStyleSheet("""
            font-size: 14px; color: #64748b;
            background: transparent; border: none;
        """)
        layout.addWidget(arrow)

        self.setStyleSheet("""
            ProfileWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.03));
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            ProfileWidget:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.12),
                    stop:1 rgba(255, 255, 255, 0.06));
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
        """)

    def set_user(self, user_data):
        """Update profile widget with user data."""
        self.user_data = user_data

        raw_display = user_data.get("display_name") or "User"
        raw_username = user_data.get("username") or "user"

        # Remove numbers from display_name and username (keep only clean name)
        clean_display = re.sub(r'\d+', '', raw_display).strip()
        clean_display = re.sub(r'[_.-]+', ' ', clean_display).strip()
        if not clean_display:
            clean_display = "User"
        elif clean_display.lower() == "prathamore":
            clean_display = "Pratha More"
        else:
            clean_display = clean_display.title()

        clean_username = re.sub(r'\d+', '', raw_username).strip()
        clean_username = re.sub(r'[^a-zA-Z_]', '', clean_username).lower() or "user"

        avatar_color = user_data.get("avatar_color", "#2563eb")

        parts = clean_display.split()
        if len(parts) >= 2:
            initials = (parts[0][0] + parts[1][0]).upper()
        else:
            initials = clean_display[:2].upper()

        self.avatar.update_avatar(initials, avatar_color)

        avatar_b64 = user_data.get("avatar_image_b64")
        if avatar_b64:
            self.avatar.set_image_from_b64(avatar_b64)
        else:
            self.avatar.clear_image()

        self.name_label.setText(clean_display)
        self.status_label.setText(f"@{clean_username}")

    def set_guest(self):
        """Reset to guest state."""
        self.user_data = None
        self.avatar.update_avatar("?", "#475569")
        self.avatar.clear_image()
        self.name_label.setText("Guest")
        self.status_label.setText("Not signed in")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._show_menu()

    def _show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 23, 42, 0.98),
                    stop:1 rgba(15, 23, 42, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 8px;
                min-width: 300px;
            }
            QMenu::item {
                padding: 12px 20px;
                border-radius: 10px;
                color: #e2e8f0;
                font-size: 13px;
                margin: 2px 4px;
            }
            QMenu::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(37, 99, 235, 0.2),
                    stop:1 rgba(37, 99, 235, 0.1));
                color: #60a5fa;
            }
            QMenu::item:disabled {
                color: #64748b;
            }
            QMenu::separator {
                height: 1px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.5 rgba(255, 255, 255, 0.1),
                    stop:1 transparent);
                margin: 6px 16px;
            }
        """)

        if self.user_data:
            # Profile Header
            header = QAction(
                f"  👤  {self.user_data.get('display_name', 'User')}", self
            )
            header.setEnabled(False)
            menu.addAction(header)

            # Username
            username_action = QAction(
                f"  🔖  @{self.user_data.get('username', '')}", self
            )
            username_action.setEnabled(False)
            menu.addAction(username_action)

            # Email
            email_action = QAction(
                f"  ✉️  {self.user_data.get('email', '')}", self
            )
            email_action.setEnabled(False)
            menu.addAction(email_action)

            # Bio (if exists)
            bio = self.user_data.get('bio', '').strip()
            if bio:
                display_bio = bio if len(bio) <= 45 else bio[:42] + "..."
                bio_action = QAction(f"  💬  {display_bio}", self)
                bio_action.setEnabled(False)
                menu.addAction(bio_action)

            menu.addSeparator()

            # Edit Profile
            profile_action = QAction("  ✏️  Edit Profile", self)
            profile_action.triggered.connect(self.profileClicked.emit)
            menu.addAction(profile_action)

            # Stats
            stats_action = QAction(
                f"  📊  {self.user_data.get('total_sessions', 0)} sessions • "
                f"{self.user_data.get('total_gestures', 0)} gestures",
                self
            )
            stats_action.setEnabled(False)
            menu.addAction(stats_action)

            menu.addSeparator()

            # Logout
            logout_action = QAction("  🚪  Sign Out", self)
            logout_action.triggered.connect(self.logoutClicked.emit)
            menu.addAction(logout_action)
        else:
            login_action = QAction("  🔑  Sign In", self)
            login_action.triggered.connect(self.logoutClicked.emit)
            menu.addAction(login_action)

        pos = self.mapToGlobal(QPoint(0, self.height() + 6))
        menu.exec(pos)


# ─── MODERN PROFILE EDIT DIALOG ─────────────────────────────────────
class ProfileEditDialog(QDialog):
    """Modern dialog for editing user profile."""
    profileUpdated = Signal(dict)

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data.copy()
        self.new_avatar_bytes = None
        self.new_avatar_path = ""
        self.setWindowTitle("Edit Profile")
        self.setFixedSize(480, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._build_ui()

    def _build_ui(self):
        # Main container
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Background container
        self.bg_container = QFrame()
        self.bg_container.setObjectName("bgContainer")
        self.bg_container.setStyleSheet("""
            #bgContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)

        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 15)
        self.bg_container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.bg_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # ── Title Bar ──
        title_bar = QFrame()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 0, 14, 0)

        # Logo
        logo = QLabel("✨")
        logo.setStyleSheet("font-size: 22px; background: transparent;")
        title_bar_layout.addWidget(logo)

        title = QLabel("Edit Profile")
        title.setStyleSheet("""
            font-size: 16px; font-weight: 700; color: #f1f5f9;
            background: transparent; margin-left: 8px;
        """)
        title_bar_layout.addWidget(title)
        title_bar_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 16px;
                color: #64748b;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
                color: #f87171;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_bar_layout.addWidget(close_btn)

        container_layout.addWidget(title_bar)

        # ── Scroll Area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.02);
                width: 6px;
                border-radius: 3px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(14)

        # ── Status Label ──
        self.status = StatusLabel()
        layout.addWidget(self.status)

        # ══════════════════════════════════════════════════════════════
        # AVATAR SECTION
        # ══════════════════════════════════════════════════════════════
        avatar_card = QFrame()
        avatar_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(37, 99, 235, 0.1),
                    stop:1 rgba(139, 92, 246, 0.06));
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
        """)
        avatar_layout = QVBoxLayout(avatar_card)
        avatar_layout.setAlignment(Qt.AlignCenter)
        avatar_layout.setContentsMargins(20, 20, 20, 20)
        avatar_layout.setSpacing(14)

        # Section label
        avatar_title = QLabel("PROFILE PHOTO")
        avatar_title.setStyleSheet("""
            font-size: 10px; font-weight: 700; color: #60a5fa;
            letter-spacing: 1.5px;
            background: transparent;
        """)
        avatar_layout.addWidget(avatar_title, alignment=Qt.AlignCenter)

        # Large avatar
        display_name = self.user_data.get("display_name", "User")
        parts = display_name.split()
        initials = parts[0][0] + parts[1][0] if len(parts) >= 2 else display_name[:2]

        self.large_avatar = LargeAvatarWidget(
            initials,
            self.user_data.get("avatar_color", "#2563eb"),
            90
        )
        self.large_avatar.clicked.connect(self._pick_avatar)

        avatar_b64 = self.user_data.get("avatar_image_b64")
        if avatar_b64:
            self.large_avatar.set_image_from_b64(avatar_b64)

        avatar_layout.addWidget(self.large_avatar, alignment=Qt.AlignCenter)

        # Upload/Remove buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        upload_btn = QPushButton("📷  Upload")
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.setFixedHeight(36)
        upload_btn.setStyleSheet("""
            QPushButton {
                background: rgba(37, 99, 235, 0.15);
                border: 1px solid rgba(37, 99, 235, 0.3);
                border-radius: 10px;
                color: #60a5fa;
                font-size: 12px;
                font-weight: 600;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: rgba(37, 99, 235, 0.25);
                border: 1px solid rgba(37, 99, 235, 0.5);
            }
        """)
        upload_btn.clicked.connect(self._pick_avatar)
        btn_row.addWidget(upload_btn)

        remove_btn = QPushButton("🗑  Remove")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setFixedHeight(36)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 10px;
                color: #f87171;
                font-size: 12px;
                font-weight: 600;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
        """)
        remove_btn.clicked.connect(self._remove_avatar)
        btn_row.addWidget(remove_btn)

        avatar_layout.addLayout(btn_row)

        # Image info
        self.image_info = QLabel("Click avatar or Upload to change")
        self.image_info.setAlignment(Qt.AlignCenter)
        self.image_info.setStyleSheet("""
            font-size: 10px; color: #64748b;
            background: transparent;
        """)
        avatar_layout.addWidget(self.image_info)

        layout.addWidget(avatar_card)

        # ══════════════════════════════════════════════════════════════
        # COLOR PICKER
        # ══════════════════════════════════════════════════════════════
        color_label = QLabel("AVATAR COLOR")
        color_label.setStyleSheet("""
            font-size: 10px; font-weight: 700; color: #94a3b8;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(color_label)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)
        self.color_buttons = []
        colors = [
            "#2563eb", "#7c3aed", "#059669", "#d97706",
            "#dc2626", "#0891b2", "#4f46e5", "#be185d"
        ]

        current_color = self.user_data.get("avatar_color", "#2563eb")
        for color in colors:
            btn = QPushButton()
            btn.setFixedSize(34, 34)
            btn.setCursor(Qt.PointingHandCursor)
            is_selected = color == current_color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {color}, stop:1 {QColor(color).darker(120).name()});
                    border-radius: 17px;
                    border: {'3px solid white' if is_selected else '2px solid transparent'};
                }}
                QPushButton:hover {{
                    border: 2px solid rgba(255, 255, 255, 0.6);
                }}
            """)
            btn.clicked.connect(lambda checked, c=color: self._select_color(c))
            color_row.addWidget(btn)
            self.color_buttons.append((btn, color))

        color_row.addStretch()
        layout.addLayout(color_row)

        self.selected_color = current_color

        # ══════════════════════════════════════════════════════════════
        # FORM FIELDS
        # ══════════════════════════════════════════════════════════════
        layout.addSpacing(4)

        # Username
        username_label = QLabel("USERNAME")
        username_label.setStyleSheet("""
            font-size: 10px; font-weight: 700; color: #94a3b8;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(username_label)

        self.username_input = ModernInput("Choose a unique username")
        self.username_input.setText(self.user_data.get("username", ""))
        layout.addWidget(self.username_input)

        # Display Name
        name_label = QLabel("DISPLAY NAME")
        name_label.setStyleSheet("""
            font-size: 10px; font-weight: 700; color: #94a3b8;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(name_label)

        self.name_input = ModernInput("Your display name")
        self.name_input.setText(self.user_data.get("display_name", ""))
        layout.addWidget(self.name_input)

        # Bio
        bio_label = QLabel("BIO")
        bio_label.setStyleSheet("""
            font-size: 10px; font-weight: 700; color: #94a3b8;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(bio_label)

        self.bio_input = ModernTextEdit("Tell us about yourself...")
        self.bio_input.setPlainText(self.user_data.get("bio", ""))
        self.bio_input.setFixedHeight(80)
        layout.addWidget(self.bio_input)

        # Bio counter
        self.bio_counter = QLabel("0/200 characters")
        self.bio_counter.setStyleSheet("""
            font-size: 10px; color: #64748b;
            background: transparent;
        """)
        self.bio_counter.setAlignment(Qt.AlignRight)
        self.bio_input.textChanged.connect(self._update_bio_counter)
        layout.addWidget(self.bio_counter)

        # Update counter on load
        self._update_bio_counter()

        # ══════════════════════════════════════════════════════════════
        # ACTION BUTTONS
        # ══════════════════════════════════════════════════════════════
        layout.addSpacing(8)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(12)

        cancel_btn = ModernButton("Cancel", primary=False)
        cancel_btn.clicked.connect(self.reject)
        btn_row2.addWidget(cancel_btn)

        save_btn = ModernButton("💾  Save Changes", primary=True)
        save_btn.clicked.connect(self._save)
        btn_row2.addWidget(save_btn)

        layout.addLayout(btn_row2)

        scroll.setWidget(content_widget)
        container_layout.addWidget(scroll)

        main_layout.addWidget(self.bg_container)

    def _update_bio_counter(self):
        """Update bio character counter."""
        text = self.bio_input.toPlainText()
        count = len(text)
        max_chars = 200

        self.bio_counter.setText(f"{count}/{max_chars} characters")

        if count > max_chars:
            self.bio_counter.setStyleSheet("""
                font-size: 10px; color: #f87171;
                background: transparent;
            """)
        elif count > max_chars * 0.9:
            self.bio_counter.setStyleSheet("""
                font-size: 10px; color: #facc15;
                background: transparent;
            """)
        else:
            self.bio_counter.setStyleSheet("""
                font-size: 10px; color: #64748b;
                background: transparent;
            """)

    def _pick_avatar(self):
        """Open file picker for avatar image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose Profile Picture",
            os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"
        )

        if not file_path:
            return

        file_size = os.path.getsize(file_path)
        if file_size > 2 * 1024 * 1024:
            self.image_info.setText("❌ File too large! Max 2MB")
            self.image_info.setStyleSheet("""
                font-size: 10px; color: #f87171;
                background: transparent;
            """)
            return

        try:
            with open(file_path, 'rb') as f:
                self.new_avatar_bytes = f.read()
            self.new_avatar_path = file_path

            self.large_avatar.set_image_from_bytes(self.new_avatar_bytes)

            size_kb = file_size / 1024
            filename = os.path.basename(file_path)
            self.image_info.setText(f"✅ {filename} ({size_kb:.0f} KB)")
            self.image_info.setStyleSheet("""
                font-size: 10px; color: #4ade80;
                background: transparent;
            """)

        except Exception as e:
            self.image_info.setText("❌ Failed to load")
            self.image_info.setStyleSheet("""
                font-size: 10px; color: #f87171;
                background: transparent;
            """)

    def _remove_avatar(self):
        """Remove current avatar image."""
        self.new_avatar_bytes = b''
        self.large_avatar.clear_image()
        self.image_info.setText("Avatar removed • Will show initials")
        self.image_info.setStyleSheet("""
            font-size: 10px; color: #facc15;
            background: transparent;
        """)

    def _select_color(self, color):
        """Select avatar fallback color."""
        self.selected_color = color
        self.large_avatar.color = color
        self.large_avatar.update()

        for btn, c in self.color_buttons:
            is_sel = c == color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {c}, stop:1 {QColor(c).darker(120).name()});
                    border-radius: 17px;
                    border: {'3px solid white' if is_sel else '2px solid transparent'};
                }}
                QPushButton:hover {{
                    border: 2px solid rgba(255, 255, 255, 0.6);
                }}
            """)

    def _save(self):
        """Save profile changes to database."""
        new_username = self.username_input.text().strip().lower()
        new_name = self.name_input.text().strip()
        new_bio = self.bio_input.toPlainText().strip()

        # Validation
        if not new_name:
            self.status.show_error("Display name is required")
            return

        if not new_username:
            self.status.show_error("Username is required")
            return

        if len(new_username) < 3:
            self.status.show_error("Username must be at least 3 characters")
            return

        # Check if username is alphanumeric + underscore only
        if not re.match(r'^[a-z0-9_]+$', new_username):
            self.status.show_error("Username: letters, numbers, _ only")
            return

        # Check if username changed and if new one is available
        old_username = self.user_data.get("username", "")
        if new_username != old_username:
            if database.check_username_exists(new_username):
                self.status.show_error("Username already taken")
                return

        # Check bio length
        if len(new_bio) > 200:
            new_bio = new_bio[:200]

        # Prepare avatar bytes
        avatar_bytes_to_save = None
        avatar_path_to_save = None

        if self.new_avatar_bytes is not None:
            if self.new_avatar_bytes == b'':
                avatar_bytes_to_save = None
                avatar_path_to_save = ""
                self.user_data["avatar_image_b64"] = None
            else:
                avatar_bytes_to_save = self._resize_image(
                    self.new_avatar_bytes, 256
                )
                avatar_path_to_save = self.new_avatar_path
                self.user_data["avatar_image_b64"] = base64.b64encode(
                    avatar_bytes_to_save
                ).decode('utf-8')

        # Update database
        database.update_user_profile(
            self.user_data["id"],
            username=new_username,
            display_name=new_name,
            bio=new_bio,
            avatar_color=self.selected_color,
            avatar_image_bytes=avatar_bytes_to_save,
            avatar_path=avatar_path_to_save
        )

        # Update local data
        self.user_data["username"] = new_username
        self.user_data["display_name"] = new_name
        self.user_data["bio"] = new_bio
        self.user_data["avatar_color"] = self.selected_color

        self.status.show_success("Profile updated!")
        QTimer.singleShot(500, lambda: self.profileUpdated.emit(self.user_data))
        QTimer.singleShot(600, self.accept)

    def _resize_image(self, image_bytes, max_size):
        """Resize image to max dimensions while keeping aspect ratio."""
        try:
            img = QImage()
            img.loadFromData(image_bytes)

            if img.width() > max_size or img.height() > max_size:
                img = img.scaled(
                    max_size, max_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

            from PySide6.QtCore import QBuffer, QIODevice
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            img.save(buffer, "PNG", 85)
            return buffer.data().data()

        except Exception:
            return image_bytes

    # Allow dragging the frameless dialog
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()