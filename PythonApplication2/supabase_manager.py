"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          AUREVIX SUPABASE MANAGER                            ║
║                Cloud Authentication & PostgreSQL Database Client             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import threading
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable
from dotenv import load_dotenv

# Load environment variables (.env search in script dir or parent)
_script_dir = Path(__file__).resolve().parent
_env_path = _script_dir / ".env"
if not _env_path.exists():
    _env_path = _script_dir.parent / ".env"

if _env_path.exists():
    load_dotenv(_env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


class SupabaseManager:
    """
    Singleton Cloud Database & Authentication Service for Aurevix.
    Provides robust, thread-safe access to Supabase Auth & PostgreSQL.
    """

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        """Initialize the Supabase client safely."""
        self.is_connected = False
        self.client = None

        if not self.is_configured():
            print("[Supabase] Credentials not configured in .env file.")
            return

        try:
            from supabase import create_client, Client
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.is_connected = True
            print("[Supabase] Cloud client initialized successfully.")
        except Exception as e:
            print(f"[Supabase] Connection error: {e}")
            self.is_connected = False

    def is_configured(self) -> bool:
        """Check if valid Supabase credentials exist."""
        return bool(
            SUPABASE_URL 
            and SUPABASE_KEY 
            and "your-project-id" not in SUPABASE_URL
            and "your-anon-public-key" not in SUPABASE_KEY
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # 🔐 AUTHENTICATION
    # ═══════════════════════════════════════════════════════════════════════════

    def sign_up(self, email: str, password: str, username: str, display_name: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user in Supabase Auth.
        Triggers automatic profile creation in PostgreSQL public.profiles.
        """
        if not self.is_connected:
            return False, "Cloud database is not connected. Check .env configuration.", None

        if len(password) < 6:
            return False, "Password must be at least 6 characters.", None

        try:
            metadata = {
                "username": username.strip().lower(),
                "display_name": display_name or username.strip().title()
            }
            res = self.client.auth.sign_up({
                "email": email.strip().lower(),
                "password": password,
                "options": {
                    "data": metadata
                }
            })

            if res.user:
                return True, "Registration successful!", {
                    "id": res.user.id,
                    "email": res.user.email,
                    "metadata": res.user.user_metadata
                }
            return False, "Registration failed: No user returned.", None

        except Exception as e:
            return False, f"Registration error: {str(e)}", None

    def sign_in(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate an existing user.
        Returns user data and stores session token.
        """
        if not self.is_connected:
            return False, "Cloud database is not connected. Check .env configuration.", None

        try:
            res = self.client.auth.sign_in_with_password({
                "email": email.strip().lower(),
                "password": password
            })

            if res.user and res.session:
                user_info = {
                    "id": res.user.id,
                    "email": res.user.email,
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token
                }
                # Fetch profile details
                profile = self.get_profile(res.user.id)
                if profile:
                    user_info.update(profile)

                self.log_activity(res.user.id, "LOGIN", "User logged in via cloud auth")
                return True, "Login successful!", user_info

            return False, "Invalid credentials.", None

        except Exception as e:
            return False, f"Login error: {str(e)}", None

    def sign_out(self) -> Tuple[bool, str]:
        """Sign out current user session."""
        if not self.is_connected:
            return True, "Signed out locally."

        try:
            self.client.auth.sign_out()
            return True, "Signed out successfully."
        except Exception as e:
            return False, f"Sign out error: {str(e)}"

    def get_current_user(self) -> Optional[Any]:
        """Get currently active Supabase user."""
        if not self.is_connected:
            return None
        try:
            return self.client.auth.get_user()
        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # 👤 PROFILES & STATS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile from public.profiles table."""
        if not self.is_connected:
            return None
        try:
            res = self.client.table("profiles").select("*").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"⚠️ Error fetching profile: {e}")
            return None

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile fields."""
        if not self.is_connected:
            return False
        try:
            self.client.table("profiles").update(updates).eq("id", user_id).execute()
            return True
        except Exception as e:
            print(f"⚠️ Error updating profile: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # ✋ CUSTOM GESTURES SYNC
    # ═══════════════════════════════════════════════════════════════════════════

    def get_gestures(self, user_id: str, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """Download custom gestures for the user from Supabase."""
        if not self.is_connected:
            return []
        try:
            query = self.client.table("custom_gestures").select("*").eq("user_id", user_id)
            if mode:
                query = query.eq("mode", mode.upper())
            res = query.execute()
            return res.data or []
        except Exception as e:
            print(f"⚠️ Error fetching gestures: {e}")
            return []

    def save_gesture(self, user_id: str, gesture_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Upload or update a custom gesture signature to Supabase."""
        if not self.is_connected:
            return False, "Not connected to cloud database.", None
        try:
            payload = {
                "user_id": user_id,
                "name": gesture_data.get("name"),
                "mode": gesture_data.get("mode", "DESKTOP").upper(),
                "action_type": gesture_data.get("action", {}).get("type", "HOTKEY"),
                "action_target": gesture_data.get("action", {}).get("target", ""),
                "signature": gesture_data.get("signature", []),
                "threshold": gesture_data.get("threshold", 75),
                "is_enabled": gesture_data.get("enabled", True)
            }
            res = self.client.table("custom_gestures").insert(payload).execute()
            if res.data and len(res.data) > 0:
                return True, "Gesture saved to cloud!", res.data[0]["id"]
            return False, "Failed to save gesture.", None
        except Exception as e:
            return False, f"Cloud save error: {str(e)}", None

    def delete_gesture(self, gesture_id: int) -> bool:
        """Delete a gesture from cloud database."""
        if not self.is_connected:
            return False
        try:
            self.client.table("custom_gestures").delete().eq("id", gesture_id).execute()
            return True
        except Exception as e:
            print(f"⚠️ Error deleting gesture: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # ⚙️ USER SETTINGS SYNC
    # ═══════════════════════════════════════════════════════════════════════════

    def get_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user settings from cloud."""
        if not self.is_connected:
            return None
        try:
            res = self.client.table("user_settings").select("*").eq("user_id", user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"⚠️ Error fetching settings: {e}")
            return None

    def save_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Sync user settings to cloud."""
        if not self.is_connected:
            return False
        try:
            self.client.table("user_settings").upsert({
                "user_id": user_id,
                **settings
            }).execute()
            return True
        except Exception as e:
            print(f"⚠️ Error saving settings: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # 📝 ACTIVITY & STATS
    # ═══════════════════════════════════════════════════════════════════════════

    def log_activity(self, user_id: str, action: str, details: str = ""):
        """Log user activity into public.activity_logs."""
        if not self.is_connected:
            return
        try:
            self.client.table("activity_logs").insert({
                "user_id": user_id,
                "action_type": action,
                "details": details
            }).execute()
        except Exception:
            pass

    def record_training_stat(self, user_id: str, mode_name: str, score: int, accuracy: float, duration: int):
        """Record game / training session performance."""
        if not self.is_connected:
            return
        try:
            self.client.table("training_stats").insert({
                "user_id": user_id,
                "mode_name": mode_name,
                "score": score,
                "accuracy_pct": accuracy,
                "duration_seconds": duration
            }).execute()
        except Exception as e:
            print(f"⚠️ Error recording training stat: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # 🌐 GOOGLE OAUTH LOGIN (BROWSER POPUP + LOCAL REDIRECT)
    # ═══════════════════════════════════════════════════════════════════════════

    def start_google_login(self, on_success: Callable[[Dict], None], on_error: Callable[[str], None]):
        """
        Start OAuth flow with Google via Supabase in the default web browser.
        Runs a temporary local callback server on port 54321.
        """
        if not self.is_connected:
            on_error("Cloud database is not connected. Check .env configuration.")
            return

        def _worker():
            import time
            import webbrowser
            import urllib.parse
            from http.server import HTTPServer, BaseHTTPRequestHandler

            class _OAuthCallbackHandler(BaseHTTPRequestHandler):
                def log_message(self, format, *args):
                    pass  # Suppress HTTP console logs

                def do_GET(self):
                    parsed = urllib.parse.urlparse(self.path)
                    query = urllib.parse.parse_qs(parsed.query)

                    if parsed.path == "/callback":
                        code = query.get("code", [None])[0]
                        if code:
                            self.server.oauth_code = code
                            self._send_success_html("Authentication complete! You can close this window.")
                        else:
                            self._send_hash_forward_html()
                    elif parsed.path == "/token":
                        self.server.access_token = query.get("access_token", [None])[0]
                        self.server.refresh_token = query.get("refresh_token", [None])[0]
                        self._send_success_html("Authentication complete! You can close this window.")
                    else:
                        self.send_response(404)
                        self.end_headers()

                def _send_success_html(self, message):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Aurevix - Signed In</title>
                        <style>
                            body {{ background: #0b0f19; color: #00d4ff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                            .box {{ background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.6); max-width: 400px; }}
                            h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
                            p {{ color: #94a3b8; font-size: 15px; line-height: 1.5; }}
                        </style>
                    </head>
                    <body>
                        <div class="box">
                            <h1>🖐️ Aurevix</h1>
                            <p>{message}</p>
                            <p style="color: #22c55e; font-weight: bold;">Return to the Aurevix desktop application.</p>
                        </div>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode("utf-8"))

                def _send_hash_forward_html(self):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    html = """
                    <!DOCTYPE html>
                    <html>
                    <body>
                        <script>
                            if (window.location.hash) {
                                window.location.href = "/token?" + window.location.hash.substring(1);
                            } else {
                                document.body.innerHTML = "<p>Processing login...</p>";
                            }
                        </script>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode("utf-8"))

            server = None
            try:
                port = 54321
                server = HTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)
                server.timeout = 120
                server.oauth_code = None
                server.access_token = None
                server.refresh_token = None

                res = self.client.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {
                        "redirect_to": f"http://localhost:{port}/callback"
                    }
                })

                if not res.url:
                    on_error("Failed to generate Google login URL.")
                    return

                webbrowser.open(res.url)

                start_time = time.time()
                while time.time() - start_time < 120:
                    server.handle_request()
                    if server.oauth_code or (server.access_token and server.refresh_token):
                        break

                user = None
                session = None
                if server.oauth_code:
                    auth_res = self.client.auth.exchange_code_for_session({"auth_code": server.oauth_code})
                    session = auth_res.session
                    user = auth_res.user
                elif server.access_token and server.refresh_token:
                    auth_res = self.client.auth.set_session(server.access_token, server.refresh_token)
                    session = auth_res.session
                    user = auth_res.user
                else:
                    on_error("Google sign-in timed out or was cancelled.")
                    return

                if user and session:
                    meta = user.user_metadata or {}
                    raw_name = (
                        meta.get("full_name")
                        or meta.get("name")
                        or f"{meta.get('given_name', '')} {meta.get('family_name', '')}".strip()
                    )
                    if not raw_name:
                        raw_name = user.email.split("@")[0]

                    # Strip all numbers as requested
                    clean_name = re.sub(r'\d+', '', raw_name).strip()
                    clean_name = re.sub(r'[_.-]+', ' ', clean_name).strip()
                    if not clean_name:
                        clean_name = "User"
                    elif clean_name.lower() == "prathamore":
                        clean_name = "Pratha More"
                    else:
                        clean_name = clean_name.title()

                    raw_uname = meta.get("user_name") or user.email.split("@")[0]
                    clean_uname = re.sub(r'\d+', '', raw_uname).strip()
                    clean_uname = re.sub(r'[^a-zA-Z_]', '', clean_uname).lower() or "user"

                    user_info = {
                        "id": user.id,
                        "email": user.email,
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                        "display_name": clean_name,
                        "avatar_url": meta.get("avatar_url") or "",
                        "username": clean_uname
                    }
                    profile = self.get_profile(user.id)
                    if profile:
                        prof_display = profile.get("display_name", "")
                        prof_uname = profile.get("username", "")
                        # If profile has digits or was email handle, clean in cloud database too
                        if any(c.isdigit() for c in str(prof_display)) or prof_display.lower() == user.email.split("@")[0].lower():
                            self.update_profile(user.id, {"display_name": clean_name, "username": clean_uname})
                            profile["display_name"] = clean_name
                            profile["username"] = clean_uname
                        user_info.update(profile)

                    # Ensure display_name and username never retain trailing numbers
                    user_info["display_name"] = clean_name
                    user_info["username"] = clean_uname

                    self.log_activity(user.id, "GOOGLE_LOGIN", "Signed in with Google")
                    on_success(user_info)
                else:
                    on_error("Could not obtain user details from Google.")

            except Exception as e:
                on_error(f"Google sign-in error: {str(e)}")
            finally:
                if server:
                    server.server_close()

        threading.Thread(target=_worker, daemon=True, name="GoogleOAuthWorker").start()


# Global Singleton Accessor
def get_supabase() -> SupabaseManager:
    return SupabaseManager()
