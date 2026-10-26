import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QCheckBox,
    QStackedWidget, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont

import database


class AnimatedInput(QLineEdit):
    """Custom input field with floating label effect and optional password toggle."""

    def __init__(self, placeholder="", is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(48)
        self.is_password_field = is_password

        if is_password:
            self.setEchoMode(QLineEdit.Password)
            self._add_show_password_button()

        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
                background: rgba(37, 99, 235, 0.05);
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)

    def _add_show_password_button(self):
        """Adds eye icon button to show/hide password."""
        self.toggle_btn = QPushButton("👁")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setFixedSize(24, 24)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 14px;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_password)
        self.setTextMargins(0, 0, 30, 0)  # space for button
        self.toggle_btn.setParent(self)
        self.toggle_btn.move(self.width() - 30, (self.height() - 24) // 2)
        self.toggle_btn.show()
        # Adjust position on resize
        self.resizeEvent = self._on_resize

    def _toggle_password(self):
        if self.toggle_btn.isChecked():
            self.setEchoMode(QLineEdit.Normal)
        else:
            self.setEchoMode(QLineEdit.Password)

    def _on_resize(self, event):
        if hasattr(self, "toggle_btn"):
            self.toggle_btn.move(self.width() - 30, (self.height() - 24) // 2)
        super().resizeEvent(event)
class AuthButton(QPushButton):
    """Styled authentication button."""

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
                    background: transparent;
                    color: #60a5fa;
                    border: 1px solid rgba(37, 99, 235, 0.3);
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: rgba(37, 99, 235, 0.1);
                    border: 1px solid rgba(37, 99, 235, 0.5);
                }
            """)


class GoogleAuthButton(QPushButton):
    """Modern Google OAuth button styled for Aurevix."""

    def __init__(self, parent=None):
        super().__init__("🌐  Continue with Google", parent)
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Inter", 12, QFont.Bold))
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 12px;
                font-weight: 700;
                font-size: 13px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(0, 212, 255, 0.6);
                color: #00d4ff;
            }
            QPushButton:pressed {
                background: rgba(0, 212, 255, 0.2);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.02);
                color: #64748b;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)

class StatusLabel(QLabel):
    """Animated status/error message label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(36)
        self.setStyleSheet("color: transparent; font-size: 12px; border-radius: 8px;")
        self.hide()

    def show_error(self, msg):
        self.setText(f"❌  {msg}")
        self.setStyleSheet("""
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
        """)
        self.show()
        QTimer.singleShot(5000, self.hide)

    def show_success(self, msg):
        self.setText(f"✅  {msg}")
        self.setStyleSheet("""
            color: #86efac;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
        """)
        self.show()
        QTimer.singleShot(3000, self.hide)


class LoginPage(QWidget):
    """Login form widget."""
    loginSuccess = Signal(dict)  # Emits user data on successful login
    switchToRegister = Signal()  # Switch to registration page
    googleLoginSuccess = Signal(dict)
    googleLoginError = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Card Container ──
        card = QFrame()
        card.setFixedSize(420, 610)
        card.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.95);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 40, 36, 36)
        card_layout.setSpacing(8)

        # ── Logo ──
        logo = QLabel("🖐")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        card_layout.addWidget(logo)

        # ── Title ──
        title = QLabel("Welcome To Aurevix")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px; font-weight: 800; color: #f1f5f9;
            background: transparent; border: none;
        """)
        card_layout.addWidget(title)

        subtitle = QLabel("Sign in to your Aurevix account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 13px; color: #64748b;
            background: transparent; border: none; margin-bottom: 16px;
        """)
        card_layout.addWidget(subtitle)

        # ── Status ──
        self.status = StatusLabel()
        card_layout.addWidget(self.status)

        # ── Username/Email ──
        self.username_input = AnimatedInput("Username or Email")
        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(4)

        # ── Password ──
        self.password_input = AnimatedInput("Password", is_password=True)
        card_layout.addWidget(self.password_input)

        # ── Remember Me ──
        remember_row = QHBoxLayout()
        self.remember_cb = QCheckBox("Remember me")
        self.remember_cb.setStyleSheet("""
            QCheckBox {
                color: #94a3b8; font-size: 12px; spacing: 6px;
                background: transparent; border: none;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid rgba(255,255,255,0.15);
                background: rgba(255,255,255,0.05);
            }
            QCheckBox::indicator:checked {
                background: #2563eb;
                border: 1px solid #3b82f6;
            }
        """)
        remember_row.addWidget(self.remember_cb)
        remember_row.addStretch()

        forgot = QPushButton("Forgot Password?")
        forgot.setCursor(Qt.PointingHandCursor)
        forgot.setStyleSheet("""
            QPushButton {
                color: #60a5fa; font-size: 12px;
                background: transparent; border: none;
            }
            QPushButton:hover { color: #93c5fd; }
        """)
        remember_row.addWidget(forgot)
        card_layout.addLayout(remember_row)
        card_layout.addSpacing(8)

        # ── Login Button ──
        self.login_btn = AuthButton("Sign In")
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(6)

        # ── Divider ──
        divider_row = QHBoxLayout()
        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet("background: rgba(255,255,255,0.06); border: none;")
        divider_row.addWidget(line1)

        or_label = QLabel("OR")
        or_label.setStyleSheet("""
            color: #475569; font-size: 11px; font-weight: 600;
            padding: 0 12px; background: transparent; border: none;
        """)
        divider_row.addWidget(or_label)

        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet("background: rgba(255,255,255,0.06); border: none;")
        divider_row.addWidget(line2)
        card_layout.addLayout(divider_row)
        card_layout.addSpacing(6)

        # ── Google OAuth Button ──
        self.google_btn = GoogleAuthButton()
        self.google_btn.clicked.connect(self._on_google_login)
        card_layout.addWidget(self.google_btn)
        card_layout.addSpacing(6)

        self.googleLoginSuccess.connect(self._handle_google_success)
        self.googleLoginError.connect(self._handle_google_error)

        # ── Register Link ──
        register_btn = AuthButton("Create New Account", primary=False)
        register_btn.clicked.connect(self.switchToRegister.emit)
        card_layout.addWidget(register_btn)

        card_layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignCenter)

        # Enter key triggers login
        self.password_input.returnPressed.connect(self._on_login)
        self.username_input.returnPressed.connect(
            lambda: self.password_input.setFocus()
        )

    def _on_google_login(self):
        self.status.show_success("Opening browser for Google sign-in...")
        self.google_btn.setEnabled(False)
        self.google_btn.setText("Connecting to Google...")

        try:
            import supabase_manager
            sm = supabase_manager.get_supabase()
            if not sm.is_connected:
                self.status.show_error("Cloud DB not connected. Check .env")
                self.google_btn.setEnabled(True)
                self.google_btn.setText("🌐  Continue with Google")
                return

            def _success(user_data):
                self.googleLoginSuccess.emit(user_data)

            def _error(err):
                self.googleLoginError.emit(err)

            sm.start_google_login(_success, _error)
        except Exception as e:
            self.status.show_error(f"Google auth error: {e}")
            self.google_btn.setEnabled(True)
            self.google_btn.setText("🌐  Continue with Google")

    def _handle_google_success(self, user_data):
        display_name = user_data.get("display_name") or user_data.get("username") or "User"
        email = user_data.get("email")
        self.status.show_success(f"Welcome {display_name}!")
        self.google_btn.setEnabled(True)
        self.google_btn.setText("🌐  Continue with Google")

        if email:
            try:
                import email_service
                email_service.send_login_alert_async(email, display_name=display_name, auth_method="Google Sign-In")
            except Exception as e:
                print(f"[Auth] Email alert error: {e}")

            try:
                local_id = database.sync_oauth_user(
                    email=email,
                    username=user_data.get("username", "user"),
                    display_name=display_name
                )
                user_data["local_id"] = local_id
            except Exception as e:
                print(f"[Auth] Local DB sync error: {e}")

        QTimer.singleShot(600, lambda: self.loginSuccess.emit(user_data))

    def _handle_google_error(self, err_msg):
        self.status.show_error(err_msg[:60])
        self.google_btn.setEnabled(True)
        self.google_btn.setText("🌐  Continue with Google")

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username:
            self.status.show_error("Please enter your username or email")
            self.username_input.setFocus()
            return
        if not password:
            self.status.show_error("Please enter your password")
            self.password_input.setFocus()
            return

        self.login_btn.setText("Signing in...")
        self.login_btn.setEnabled(False)

        success, message, user_data = database.login_user(username, password)

        if success:
            self.status.show_success(message)
            if self.remember_cb.isChecked():
                database.save_remember_me(user_data["id"])

            email = user_data.get("email")
            display_name = user_data.get("display_name") or user_data.get("username") or ""
            if email:
                try:
                    import email_service
                    email_service.send_login_alert_async(email, display_name=display_name, auth_method="Password Sign-In")
                except Exception as e:
                    print(f"[Auth] Email alert error: {e}")

            QTimer.singleShot(500, lambda: self.loginSuccess.emit(user_data))
        else:
            self.status.show_error(message)

        self.login_btn.setText("Sign In")
        self.login_btn.setEnabled(True)

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.status.hide()


class RegisterPage(QWidget):
    """Registration form widget."""
    registerSuccess = Signal(dict)  # Emits user data on successful registration
    switchToLogin = Signal()  # Switch back to login

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Card ──
        card = QFrame()
        card.setFixedSize(420, 620)
        card.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.95);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(6)

        # ── Header ──
        logo = QLabel("🖐")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        card_layout.addWidget(logo)

        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 22px; font-weight: 800; color: #f1f5f9;
            background: transparent; border: none;
        """)
        card_layout.addWidget(title)

        subtitle = QLabel("Join Aurevix gesture control")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 13px; color: #64748b;
            background: transparent; border: none; margin-bottom: 12px;
        """)
        card_layout.addWidget(subtitle)

        # ── Status ──
        self.status = StatusLabel()
        card_layout.addWidget(self.status)

        # ── Display Name ──
        self.name_input = AnimatedInput("Display Name")
        card_layout.addWidget(self.name_input)
        card_layout.addSpacing(3)

        # ── Username ──
        self.username_input = AnimatedInput("Username")
        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(3)

        # ── Email ──
        self.email_input = AnimatedInput("Email Address")
        card_layout.addWidget(self.email_input)
        card_layout.addSpacing(3)

        # ── Password ──
        self.password_input = AnimatedInput("Password (min 6 chars)", is_password=True)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(3)

        # ── Confirm Password ──
        self.confirm_input = AnimatedInput("Confirm Password", is_password=True)
        card_layout.addWidget(self.confirm_input)
        card_layout.addSpacing(6)

        # ── Password Strength Indicator ──
        self.strength_bar = QFrame()
        self.strength_bar.setFixedHeight(3)
        self.strength_bar.setStyleSheet("""
            background: rgba(255,255,255,0.06);
            border-radius: 2px; border: none;
        """)
        card_layout.addWidget(self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("""
            font-size: 10px; color: #64748b;
            background: transparent; border: none;
        """)
        card_layout.addWidget(self.strength_label)
        card_layout.addSpacing(4)

        self.password_input.textChanged.connect(self._update_strength)

        # ── Terms ──
        self.terms_cb = QCheckBox("I agree to the Terms of Service")
        self.terms_cb.setStyleSheet("""
            QCheckBox {
                color: #94a3b8; font-size: 11px; spacing: 6px;
                background: transparent; border: none;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid rgba(255,255,255,0.15);
                background: rgba(255,255,255,0.05);
            }
            QCheckBox::indicator:checked {
                background: #2563eb;
                border: 1px solid #3b82f6;
            }
        """)
        card_layout.addWidget(self.terms_cb)
        card_layout.addSpacing(8)

        # ── Register Button ──
        self.register_btn = AuthButton("Create Account")
        self.register_btn.clicked.connect(self._on_register)
        card_layout.addWidget(self.register_btn)
        card_layout.addSpacing(8)

        # ── Back to Login ──
        back_btn = AuthButton("Already have an account? Sign In", primary=False)
        back_btn.clicked.connect(self.switchToLogin.emit)
        card_layout.addWidget(back_btn)

        card_layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignCenter)

        # Enter key
        self.confirm_input.returnPressed.connect(self._on_register)

    def _update_strength(self, text):
        """Update password strength indicator."""
        score = 0
        if len(text) >= 6:
            score += 1
        if len(text) >= 10:
            score += 1
        if re.search(r'[A-Z]', text):
            score += 1
        if re.search(r'[0-9]', text):
            score += 1
        if re.search(r'[!@#$%^&*]', text):
            score += 1

        colors = {
            0: ("#475569", "Too short"),
            1: ("#ef4444", "Weak"),
            2: ("#f97316", "Fair"),
            3: ("#eab308", "Good"),
            4: ("#22c55e", "Strong"),
            5: ("#06b6d4", "Very Strong"),
        }

        color, label = colors.get(score, ("#475569", ""))
        width_pct = max(5, score * 20)

        self.strength_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {color}, stop:{width_pct/100} {color},
                stop:{width_pct/100 + 0.01} rgba(255,255,255,0.06),
                stop:1 rgba(255,255,255,0.06));
            border-radius: 2px; border: none;
        """)
        self.strength_label.setText(f"Password Strength: {label}")
        self.strength_label.setStyleSheet(f"""
            font-size: 10px; color: {color};
            background: transparent; border: none;
        """)

    def _on_register(self):
        name = self.name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        # Validation
        if not name:
            self.status.show_error("Please enter your display name")
            return
        if not username:
            self.status.show_error("Please choose a username")
            return
        if not email:
            self.status.show_error("Please enter your email")
            return
        if not password:
            self.status.show_error("Please create a password")
            return
        if password != confirm:
            self.status.show_error("Passwords do not match")
            return
        if not self.terms_cb.isChecked():
            self.status.show_error("Please accept the Terms of Service")
            return

        self.register_btn.setText("Creating Account...")
        self.register_btn.setEnabled(False)

        success, message, user_id = database.register_user(
            username, email, password, name
        )

        if success:
            self.status.show_success(message)
            # Auto-login after registration
            _, _, user_data = database.login_user(username, password)
            if user_data:
                QTimer.singleShot(800, lambda: self.registerSuccess.emit(user_data))
        else:
            self.status.show_error(message)

        self.register_btn.setText("Create Account")
        self.register_btn.setEnabled(True)

    def clear_fields(self):
        self.name_input.clear()
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self.terms_cb.setChecked(False)
        self.status.hide()


class AuthManager(QStackedWidget):
    """
    Manages login/register flow.
    Emits authenticated(user_data) when user is logged in.
    """
    authenticated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        # Login page
        self.login_page = LoginPage()
        self.login_page.loginSuccess.connect(self._on_auth_success)
        self.login_page.switchToRegister.connect(lambda: self.setCurrentIndex(1))
        self.addWidget(self.login_page)

        # Register page
        self.register_page = RegisterPage()
        self.register_page.registerSuccess.connect(self._on_auth_success)
        self.register_page.switchToLogin.connect(lambda: self.setCurrentIndex(0))
        self.addWidget(self.register_page)

        # Check for remembered session
        self._check_auto_login()

    def _check_auto_login(self):
        """Try auto-login from saved session."""
        user_id = database.load_remember_me()
        if user_id:
            user_data = database.get_user_by_id(user_id)
            if user_data:
                user_data["session_token"] = "auto_login"
                QTimer.singleShot(100, lambda: self._on_auth_success(user_data))

    def _on_auth_success(self, user_data):
        self.authenticated.emit(user_data)

    def show_login(self):
        self.login_page.clear_fields()
        self.setCurrentIndex(0)

    def show_register(self):
        self.register_page.clear_fields()
        self.setCurrentIndex(1)