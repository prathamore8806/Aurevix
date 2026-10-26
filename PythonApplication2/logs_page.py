
import csv
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QFrame, QComboBox,
    QFileDialog, QGraphicsDropShadowEffect,
    QAbstractItemView, QSizePolicy, QSpacerItem,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

import database


# ─── STATUS PILL WIDGET ─────────────────────────────────────────────
class StatusPill(QLabel):
    """Colored status badge for log entries."""

    STYLES = {
        "Success": {
            "bg": "rgba(34, 197, 94, 0.12)",
            "color": "#4ade80",
            "border": "rgba(34, 197, 94, 0.25)",
            "icon": "✅"
        },
        "Warning": {
            "bg": "rgba(234, 179, 8, 0.12)",
            "color": "#facc15",
            "border": "rgba(234, 179, 8, 0.25)",
            "icon": "⚠️"
        },
        "Error": {
            "bg": "rgba(239, 68, 68, 0.12)",
            "color": "#f87171",
            "border": "rgba(239, 68, 68, 0.25)",
            "icon": "❌"
        },
        "Info": {
            "bg": "rgba(37, 99, 235, 0.12)",
            "color": "#60a5fa",
            "border": "rgba(37, 99, 235, 0.25)",
            "icon": "ℹ️"
        },
    }

    def __init__(self, status, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(28)
        self.setFixedWidth(100)

        style = self.STYLES.get(status, self.STYLES["Info"])
        self.setText(f"{style['icon']} {status}")
        self.setStyleSheet(f"""
            QLabel {{
                background: {style['bg']};
                color: {style['color']};
                border: 1px solid {style['border']};
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 8px;
            }}
        """)


# ─── TYPE BADGE WIDGET ──────────────────────────────────────────────
class TypeBadge(QLabel):
    """Colored badge for log type."""

    TYPE_COLORS = {
        "LOGIN": ("#2563eb", "rgba(37, 99, 235, 0.1)"),
        "LOGOUT": ("#8b5cf6", "rgba(139, 92, 246, 0.1)"),
        "REGISTER": ("#059669", "rgba(5, 150, 105, 0.1)"),
        "GESTURE": ("#d97706", "rgba(217, 119, 6, 0.1)"),
        "MODE": ("#0891b2", "rgba(8, 145, 178, 0.1)"),
        "SETTING": ("#6366f1", "rgba(99, 102, 241, 0.1)"),
        "ERROR": ("#dc2626", "rgba(220, 38, 38, 0.1)"),
        "SYSTEM": ("#64748b", "rgba(100, 116, 139, 0.1)"),
        "APP_START": ("#22c55e", "rgba(34, 197, 94, 0.1)"),
        "APP_CLOSE": ("#ef4444", "rgba(239, 68, 68, 0.1)"),
        "PASSWORD_CHANGE": ("#f59e0b", "rgba(245, 158, 11, 0.1)"),
    }

    def __init__(self, log_type, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(26)
        self.setFixedWidth(110)

        color, bg = self.TYPE_COLORS.get(
            log_type.upper(), ("#94a3b8", "rgba(148, 163, 184, 0.1)")
        )

        display = log_type.replace("_", " ").title()
        self.setText(display)
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {color};
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 8px;
                letter-spacing: 0.5px;
            }}
        """)


# ─── STAT CARD ───────────────────────────────────────────────────────
class StatCard(QFrame):
    """Small stats card for top row."""

    def __init__(self, icon, label, value, color="#2563eb", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Top row: icon + label
        top = QHBoxLayout()
        top.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            "font-size: 16px; background: transparent; border: none;"
        )
        top.addWidget(icon_label)

        name = QLabel(label)
        name.setStyleSheet(
            "font-size: 11px; color: #64748b; font-weight: 500;"
            "background: transparent; border: none;"
        )
        top.addWidget(name)
        top.addStretch()
        layout.addLayout(top)

        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            font-size: 22px; font-weight: 800; color: {color};
            background: transparent; border: none;
        """)
        layout.addWidget(self.value_label)

        self.setStyleSheet(f"""
            #statCard {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }}
            #statCard:hover {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid {color}40;
            }}
        """)

    def set_value(self, val):
        self.value_label.setText(str(val))


# ─── MAIN LOGS PAGE ─────────────────────────────────────────────────
class LogsPage(QWidget):
    """Complete activity logs viewer with search, filter, and export."""

    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._all_logs = []
        self._build_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def set_user(self, user_id):
        """Set active user and reload logs."""
        self.user_id = user_id
        self.refresh_logs()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 20, 25, 20)
        self.main_layout.setSpacing(16)

        # ── HEADER ───────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Activity Logs")
        title.setStyleSheet("""
            font-size: 26px; font-weight: 700; color: #f1f5f9;
            letter-spacing: -0.5px;
        """)
        title_col.addWidget(title)

        subtitle = QLabel("Track all system events and user actions")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b;")
        title_col.addWidget(subtitle)

        header_row.addLayout(title_col)
        header_row.addStretch()

        # Refresh button
        refresh_btn = QPushButton("  🔄  Refresh")
        refresh_btn.setObjectName("actionBtn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.refresh_logs)
        header_row.addWidget(refresh_btn)

        self.main_layout.addLayout(header_row)

        # ── STATS ROW ────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.total_card = StatCard("📊", "Total Logs", "0", "#60a5fa")
        self.today_card = StatCard("📅", "Today", "0", "#4ade80")
        self.errors_card = StatCard("❌", "Errors", "0", "#f87171")
        self.sessions_card = StatCard("🔑", "Sessions", "0", "#a78bfa")

        stats_row.addWidget(self.total_card)
        stats_row.addWidget(self.today_card)
        stats_row.addWidget(self.errors_card)
        stats_row.addWidget(self.sessions_card)

        self.main_layout.addLayout(stats_row)

        # ── FILTER BAR ───────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setObjectName("filterBar")
        filter_frame.setFixedHeight(52)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        filter_layout.setSpacing(10)

        # Search
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(
            "font-size: 14px; background: transparent; border: none;"
        )
        filter_layout.addWidget(search_icon)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search logs by action, details, time...")
        self.search_bar.setObjectName("searchInput")
        self.search_bar.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_bar)

        # Type filter
        type_label = QLabel("Type:")
        type_label.setStyleSheet(
            "color: #64748b; font-size: 12px; font-weight: 600;"
            "background: transparent; border: none;"
        )
        filter_layout.addWidget(type_label)

        self.type_filter = QComboBox()
        self.type_filter.setObjectName("filterCombo")
        self.type_filter.setFixedWidth(140)
        self.type_filter.addItems([
            "All Types", "Login", "Logout", "Register",
            "App Start", "App Close", "Gesture",
            "Mode", "Setting", "Error", "System",
            "Password Change"
        ])
        self.type_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.type_filter)

        # Separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(
            "background: rgba(255,255,255,0.08); border: none;"
        )
        filter_layout.addWidget(sep)

        # Export button
        self.export_btn = QPushButton("  📥  Export CSV")
        self.export_btn.setObjectName("actionBtn")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setFixedHeight(34)
        self.export_btn.clicked.connect(self.export_logs)
        filter_layout.addWidget(self.export_btn)

        # Clear button
        self.clear_btn = QPushButton("  🗑  Clear")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(self.clear_btn)

        self.main_layout.addWidget(filter_frame)

        # ── TABLE ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "  Timestamp", "  Type", "  Description", "  Details", "  Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setObjectName("logsTable")

        self.main_layout.addWidget(self.table)

        # ── FOOTER ───────────────────────────────────────────────
        footer = QHBoxLayout()

        self.row_count_label = QLabel("Showing 0 entries")
        self.row_count_label.setStyleSheet(
            "color: #64748b; font-size: 11px;"
        )
        footer.addWidget(self.row_count_label)

        footer.addStretch()

        self.last_refresh_label = QLabel("Last refresh: --")
        self.last_refresh_label.setStyleSheet(
            "color: #475569; font-size: 11px;"
        )
        footer.addWidget(self.last_refresh_label)

        self.main_layout.addLayout(footer)

        # ── APPLY STYLES ─────────────────────────────────────────
        self._apply_styles()

    # ─── DATA LOADING ────────────────────────────────────────────
    def refresh_logs(self):
        """Reload logs from database."""
        if not self.user_id:
            self._show_empty_state()
            return

        try:
            self._all_logs = database.get_activity_log(
                self.user_id, limit=500
            )
        except Exception as e:
            self._all_logs = []
            print(f"⚠️ Failed to load logs: {e}")

        self._apply_filters()
        self._update_stats()
        self.last_refresh_label.setText(
            f"Last refresh: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _show_empty_state(self):
        """Show empty state when no user is logged in."""
        self.table.setRowCount(0)
        self.row_count_label.setText("No user logged in")
        self.total_card.set_value("--")
        self.today_card.set_value("--")
        self.errors_card.set_value("--")
        self.sessions_card.set_value("--")

    def _update_stats(self):
        """Update stat cards."""
        total = len(self._all_logs)
        self.total_card.set_value(str(total))

        today = datetime.now().strftime("%Y-%m-%d")
        today_count = sum(
            1 for log in self._all_logs
            if log.get("timestamp", "").startswith(today)
        )
        self.today_card.set_value(str(today_count))

        error_count = sum(
            1 for log in self._all_logs
            if "error" in log.get("action", "").lower()
            or "fail" in log.get("details", "").lower()
        )
        self.errors_card.set_value(str(error_count))

        session_count = sum(
            1 for log in self._all_logs
            if log.get("action", "").upper() in ("LOGIN", "APP_START")
        )
        self.sessions_card.set_value(str(session_count))

    # ─── FILTERING ───────────────────────────────────────────────
    def _apply_filters(self):
        """Apply search and type filters to table."""
        search_text = self.search_bar.text().lower().strip()
        type_filter = self.type_filter.currentText()

        # Map display names to action keys
        type_map = {
            "All Types": None,
            "Login": "LOGIN",
            "Logout": "LOGOUT",
            "Register": "REGISTER",
            "App Start": "APP_START",
            "App Close": "APP_CLOSE",
            "Gesture": "GESTURE",
            "Mode": "MODE",
            "Setting": "SETTING",
            "Error": "ERROR",
            "System": "SYSTEM",
            "Password Change": "PASSWORD_CHANGE",
        }
        filter_action = type_map.get(type_filter)

        # Filter logs
        filtered = []
        for log in self._all_logs:
            action = log.get("action", "")
            details = log.get("details", "")
            timestamp = log.get("timestamp", "")

            # Type filter
            if filter_action and action.upper() != filter_action:
                continue

            # Search filter
            if search_text:
                searchable = (
                    f"{action} {details} {timestamp}"
                ).lower()
                if search_text not in searchable:
                    continue

            filtered.append(log)

        self._populate_table(filtered)
        self.row_count_label.setText(
            f"Showing {len(filtered)} of {len(self._all_logs)} entries"
        )

    def _populate_table(self, logs):
        """Fill table with log entries."""
        self.table.setRowCount(0)

        for log in logs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            action = log.get("action", "UNKNOWN")
            details = log.get("details", "")
            timestamp = log.get("timestamp", "")

            # Determine status and description
            status = self._get_status(action, details)
            description = self._get_description(action)

            # ── Timestamp Column ──
            time_item = QTableWidgetItem(f"  {timestamp}")
            time_item.setForeground(QColor("#94a3b8"))
            time_item.setFont(QFont("Consolas", 10))
            self.table.setItem(row, 0, time_item)

            # ── Type Column (Badge) ──
            type_badge = TypeBadge(action)
            self.table.setCellWidget(row, 1, type_badge)

            # ── Description Column ──
            desc_item = QTableWidgetItem(f"  {description}")
            desc_item.setForeground(QColor("#e2e8f0"))
            self.table.setItem(row, 2, desc_item)

            # ── Details Column ──
            detail_item = QTableWidgetItem(f"  {details}")
            detail_item.setForeground(QColor("#94a3b8"))
            self.table.setItem(row, 3, detail_item)

            # ── Status Column (Pill) ──
            pill = StatusPill(status)
            self.table.setCellWidget(row, 4, pill)

    def _get_status(self, action, details):
        """Determine status from action type."""
        action_upper = action.upper()
        details_lower = details.lower()

        if "error" in details_lower or "fail" in details_lower:
            return "Error"
        if action_upper in ("LOGIN", "REGISTER", "APP_START"):
            return "Success"
        if action_upper in ("LOGOUT", "APP_CLOSE"):
            return "Info"
        if action_upper == "PASSWORD_CHANGE":
            return "Warning"
        return "Success"

    def _get_description(self, action):
        """Human-readable description for action type."""
        descriptions = {
            "LOGIN": "User signed in",
            "LOGOUT": "User signed out",
            "REGISTER": "New account created",
            "APP_START": "Application launched",
            "APP_CLOSE": "Application closed",
            "GESTURE": "Gesture recorded",
            "MODE": "Mode switched",
            "SETTING": "Settings changed",
            "ERROR": "Error occurred",
            "SYSTEM": "System event",
            "PASSWORD_CHANGE": "Password updated",
        }
        return descriptions.get(
            action.upper(), action.replace("_", " ").title()
        )

    # ─── MANUAL LOG ENTRY ────────────────────────────────────────
    def add_log_entry(self, action, details="", status="Success"):
        """
        Add a log entry both to database and UI.
        Called from other parts of the app.
        """
        if self.user_id:
            database.log_activity(self.user_id, action, details)

        # Add to local cache
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._all_logs.insert(0, {
            "action": action,
            "details": details,
            "timestamp": now
        })

        # Update table
        self._apply_filters()
        self._update_stats()

    # ─── EXPORT ──────────────────────────────────────────────────
    def export_logs(self):
        """Export current view to CSV file."""
        if self.table.rowCount() == 0:
            QMessageBox.information(
                self, "No Data", "No logs to export."
            )
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", 
            f"sgcc_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Type", "Description",
                    "Details", "Status"
                ])

                for log in self._all_logs:
                    action = log.get("action", "")
                    details = log.get("details", "")
                    timestamp = log.get("timestamp", "")
                    status = self._get_status(action, details)
                    description = self._get_description(action)

                    writer.writerow([
                        timestamp, action, description,
                        details, status
                    ])

            QMessageBox.information(
                self, "Export Complete",
                f"✅ Logs exported to:\n{filepath}"
            )

            # Log the export action
            if self.user_id:
                database.log_activity(
                    self.user_id, "SYSTEM",
                    f"Exported {len(self._all_logs)} logs to CSV"
                )

        except Exception as e:
            QMessageBox.warning(
                self, "Export Failed",
                f"❌ Failed to export: {str(e)}"
            )

    # ─── CLEAR ───────────────────────────────────────────────────
    def clear_logs(self):
        """Clear all displayed logs (not from database)."""
        reply = QMessageBox.question(
            self, "Clear Logs",
            "Are you sure you want to clear the logs view?\n"
            "This only clears the display, not the database.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.table.setRowCount(0)
            self._all_logs.clear()
            self._update_stats()
            self.row_count_label.setText("Showing 0 entries")

            if self.user_id:
                database.log_activity(
                    self.user_id, "SYSTEM", "Logs view cleared"
                )

    # ─── CLEANUP ─────────────────────────────────────────────────
    def cleanup(self):
        """Stop timers on shutdown."""
        self.refresh_timer.stop()

    # ─── STYLES ──────────────────────────────────────────────────
    def _apply_styles(self):
        self.setStyleSheet("""
            LogsPage {
                background: transparent;
            }

            #filterBar {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }

            #searchInput {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
            #searchInput:focus {
                border: 1px solid #2563eb;
                background: rgba(37, 99, 235, 0.05);
            }
            #searchInput::placeholder {
                color: #475569;
            }

            #filterCombo {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 5px 10px;
                color: #e2e8f0;
                font-size: 12px;
            }
            #filterCombo:hover {
                border: 1px solid rgba(37, 99, 235, 0.4);
            }
            #filterCombo::drop-down {
                border: none;
                width: 20px;
            }
            #filterCombo::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #60a5fa;
                margin-right: 8px;
            }
            #filterCombo QAbstractItemView {
                background: #1e1e2e;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e2e8f0;
                selection-background-color: #2563eb;
                padding: 4px;
            }

            #actionBtn {
                background: rgba(37, 99, 235, 0.1);
                border: 1px solid rgba(37, 99, 235, 0.2);
                border-radius: 8px;
                color: #60a5fa;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 14px;
            }
            #actionBtn:hover {
                background: rgba(37, 99, 235, 0.2);
                border: 1px solid rgba(37, 99, 235, 0.4);
            }

            #dangerBtn {
                background: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.15);
                border-radius: 8px;
                color: #f87171;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 14px;
            }
            #dangerBtn:hover {
                background: rgba(239, 68, 68, 0.18);
                border: 1px solid rgba(239, 68, 68, 0.35);
            }

            /* ── Table ── */
            #logsTable {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 14px;
                gridline-color: transparent;
                color: #e2e8f0;
                font-size: 12px;
            }
            #logsTable::item {
                padding: 8px 4px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            }
            #logsTable::item:selected {
                background: rgba(37, 99, 235, 0.12);
                color: #e2e8f0;
            }
            #logsTable::item:hover {
                background: rgba(255, 255, 255, 0.03);
            }

            QHeaderView::section {
                background: rgba(255, 255, 255, 0.03);
                color: #64748b;
                padding: 10px 4px;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            /* Alternating row colors */
            #logsTable QTableWidget::item:alternate {
                background: rgba(255, 255, 255, 0.01);
            }
        """)