import sqlite3
import hashlib
import os
import time
import json
import base64
from datetime import datetime


DB_FILE = "sgcc_users.db"


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users Table (with avatar_image BLOB) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            avatar_color TEXT DEFAULT '#2563eb',
            avatar_image BLOB DEFAULT NULL,
            avatar_path TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            last_login TEXT,
            total_gestures INTEGER DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            total_usage_minutes REAL DEFAULT 0.0,
            preferred_mode TEXT DEFAULT 'DESKTOP',
            is_active INTEGER DEFAULT 1
        )
    """)

    # ── Sessions Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_valid INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Activity Log Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── User Settings Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            settings_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Migration: Add avatar columns if missing ──
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_image BLOB DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_path TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


def hash_password(password, salt=None):
    """Hash password with SHA-256 + salt."""
    if salt is None:
        salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password, stored_hash):
    """Verify password against stored hash."""
    try:
        salt, hashed = stored_hash.split(":")
        check = hashlib.sha256((salt + password).encode()).hexdigest()
        return check == hashed
    except Exception:
        return False


def register_user(username, email, password, display_name=None):
    """Register a new user."""
    if len(username) < 3:
        return False, "Username must be at least 3 characters.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None
    if "@" not in email or "." not in email:
        return False, "Please enter a valid email address.", None

    username = username.strip().lower()
    email = email.strip().lower()
    display_name = display_name or username.title()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already taken.", None

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already registered.", None

        password_hash = hash_password(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        import random
        colors = [
            "#2563eb", "#7c3aed", "#059669", "#d97706",
            "#dc2626", "#0891b2", "#4f46e5", "#be185d"
        ]
        avatar_color = random.choice(colors)

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, display_name,
                             avatar_color, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, password_hash, display_name, avatar_color, now))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        log_activity(user_id, "REGISTER", "Account created")
        return True, "Account created successfully!", user_id

    except Exception as e:
        conn.close()
        return False, f"Registration failed: {str(e)}", None


def login_user(username_or_email, password):
    """Login user with username or email."""
    username_or_email = username_or_email.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM users
            WHERE (username = ? OR email = ?) AND is_active = 1
        """, (username_or_email, username_or_email))

        user = cursor.fetchone()

        if not user:
            conn.close()
            return False, "User not found.", None

        if not verify_password(password, user["password_hash"]):
            conn.close()
            return False, "Incorrect password.", None

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE users SET last_login = ?, total_sessions = total_sessions + 1
            WHERE id = ?
        """, (now, user["id"]))

        session_token = os.urandom(32).hex()
        cursor.execute("""
            INSERT INTO sessions (user_id, session_token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user["id"], session_token, now, now))

        conn.commit()

        # Convert avatar image to base64 for transport
        avatar_b64 = None
        if user["avatar_image"]:
            avatar_b64 = base64.b64encode(user["avatar_image"]).decode('utf-8')

        user_data = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
            "avatar_color": user["avatar_color"],
            "avatar_image_b64": avatar_b64,
            "avatar_path": user["avatar_path"] or "",
            "bio": user["bio"],
            "created_at": user["created_at"],
            "last_login": now,
            "total_gestures": user["total_gestures"],
            "total_sessions": user["total_sessions"] + 1,
            "total_usage_minutes": user["total_usage_minutes"],
            "preferred_mode": user["preferred_mode"],
            "session_token": session_token,
        }

        conn.close()
        log_activity(user["id"], "LOGIN", "User logged in")
        return True, "Login successful!", user_data

    except Exception as e:
        conn.close()
        return False, f"Login failed: {str(e)}", None


def get_user_by_id(user_id):
    """Fetch user data by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        avatar_b64 = None
        if user["avatar_image"]:
            avatar_b64 = base64.b64encode(user["avatar_image"]).decode('utf-8')

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
            "avatar_color": user["avatar_color"],
            "avatar_image_b64": avatar_b64,
            "avatar_path": user["avatar_path"] or "",
            "bio": user["bio"],
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "total_gestures": user["total_gestures"],
            "total_sessions": user["total_sessions"],
            "total_usage_minutes": user["total_usage_minutes"],
            "preferred_mode": user["preferred_mode"],
        }
    return None


# ⚡⚡⚡ NEW FUNCTION: Check if username exists (excluding current user)
def check_username_exists(username, exclude_user_id=None):
    """
    Check if username already exists in database.
    
    Args:
        username: Username to check
        exclude_user_id: Optional user ID to exclude from check (for editing own username)
    
    Returns:
        bool: True if username exists, False otherwise
    """
    username = username.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    
    if exclude_user_id:
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND id != ? COLLATE NOCASE",
            (username, exclude_user_id)
        )
    else:
        cursor.execute(
            "SELECT id FROM users WHERE username = ? COLLATE NOCASE",
            (username,)
        )
    
    result = cursor.fetchone()
    conn.close()
    return result is not None


# ⚡⚡⚡ UPDATED FUNCTION: Now supports username editing
def update_user_profile(user_id, username=None, display_name=None, bio=None,
                        avatar_color=None, avatar_image_bytes=None,
                        avatar_path=None):
    """
    Update user profile fields including avatar image and username.
    
    Args:
        user_id: User ID
        username: New username (optional)
        display_name: New display name (optional)
        bio: New bio text (optional)
        avatar_color: New avatar color (optional)
        avatar_image_bytes: New avatar image as bytes (optional)
        avatar_path: New avatar file path (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    values = []

    # ⚡ NEW: Support username updates
    if username is not None:
        username = username.strip().lower()
        # Check if new username is already taken by another user
        if check_username_exists(username, exclude_user_id=user_id):
            conn.close()
            return False
        updates.append("username = ?")
        values.append(username)
    
    if display_name is not None:
        updates.append("display_name = ?")
        values.append(display_name)
    
    if bio is not None:
        updates.append("bio = ?")
        values.append(bio)
    
    if avatar_color is not None:
        updates.append("avatar_color = ?")
        values.append(avatar_color)
    
    if avatar_image_bytes is not None:
        updates.append("avatar_image = ?")
        values.append(avatar_image_bytes)
    
    if avatar_path is not None:
        updates.append("avatar_path = ?")
        values.append(avatar_path)

    if updates:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        
        # Log the profile update
        if username:
            log_activity(user_id, "PROFILE_UPDATE", f"Username changed to {username}")
        else:
            log_activity(user_id, "PROFILE_UPDATE", "Profile information updated")

    conn.close()
    return True


def update_user_stats(user_id, gestures=0, minutes=0.0):
    """Increment user statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET
            total_gestures = total_gestures + ?,
            total_usage_minutes = total_usage_minutes + ?
        WHERE id = ?
    """, (gestures, minutes, user_id))
    conn.commit()
    conn.close()


def change_password(user_id, old_password, new_password):
    """Change user password."""
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, "User not found."

    if not verify_password(old_password, user["password_hash"]):
        conn.close()
        return False, "Current password is incorrect."

    new_hash = hash_password(new_password)
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_hash, user_id)
    )
    conn.commit()
    conn.close()

    log_activity(user_id, "PASSWORD_CHANGE", "Password updated")
    return True, "Password changed successfully!"


def delete_account(user_id, password):
    """Soft-delete user account."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user_id,)
    )
    user = cursor.fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        conn.close()
        return False, "Incorrect password."

    cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    cursor.execute(
        "UPDATE sessions SET is_valid = 0 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()

    return True, "Account deleted."


def log_activity(user_id, action, details=""):
    """Log user activity."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, action, details, now))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_activity_log(user_id, limit=20):
    """Get recent activity for user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, details, timestamp FROM activity_log
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_remember_me(user_id):
    """Save user ID for auto-login."""
    try:
        with open(".sgcc_session", "w") as f:
            json.dump({"user_id": user_id, "timestamp": time.time()}, f)
    except Exception:
        pass


def load_remember_me():
    """Load saved session for auto-login."""
    try:
        if os.path.exists(".sgcc_session"):
            with open(".sgcc_session", "r") as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < 30 * 24 * 3600:
                return data.get("user_id")
    except Exception:
        pass
    return None


def clear_remember_me():
    """Clear saved session."""
    try:
        if os.path.exists(".sgcc_session"):
            os.remove(".sgcc_session")
    except Exception:
        pass



def sync_oauth_user(email, username, display_name, avatar_color="#2563eb"):
    """Ensure an OAuth user has a local database entry and return local user record."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,))
        user = cursor.fetchone()
        if user:
            cursor.execute("UPDATE users SET display_name = ? WHERE id = ?", (display_name, user["id"]))
            conn.commit()
            user_id = user["id"]
        else:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, display_name, avatar_color, created_at)
                VALUES (?, ?, 'OAUTH_GOOGLE', ?, ?, ?)
            """, (username, email, display_name, avatar_color, now))
            user_id = cursor.lastrowid
            cursor.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))
            conn.commit()
        conn.close()
        return user_id
    except Exception as e:
        print(f"[DB] Error syncing oauth user: {e}")
        return 1

# Auto-initialize
init_database()