"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          AUREVIX EMAIL SERVICE                               ║
║           Automated Login Alerts & Notification Dispatcher                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import smtplib
import threading
import datetime
import platform
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

# Load .env config
_script_dir = Path(__file__).resolve().parent
_env_path = _script_dir / ".env"
if not _env_path.exists():
    _env_path = _script_dir.parent / ".env"

if _env_path.exists():
    load_dotenv(_env_path)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "Aurevix AI")


def send_login_alert_async(recipient_email: str, display_name: str = "", auth_method: str = "Google"):
    """
    Sends a security login notification to the user's email asynchronously
    without blocking the UI thread.
    """
    if not recipient_email or "@" not in recipient_email:
        print("[EmailService] No valid recipient email provided.")
        return

    threading.Thread(
        target=_send_login_email_worker,
        args=(recipient_email, display_name, auth_method),
        daemon=True,
        name="EmailAlertWorker"
    ).start()


def _send_login_email_worker(recipient_email: str, display_name: str, auth_method: str):
    """Worker function executed in background thread."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EmailService] Notice: SMTP_USER or SMTP_PASSWORD not set in .env. Email to {recipient_email} skipped.")
        return

    now_str = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    device_name = f"{platform.system()} {platform.release()} ({platform.node()})"
    name = display_name if display_name else recipient_email.split("@")[0].title()

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔐 Aurevix Login Alert: New sign-in detected"
    msg["From"] = f"{SMTP_SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = recipient_email

    text_body = f"""Hello {name},

A new login to your Aurevix account was just detected:
- Method: {auth_method}
- Date & Time: {now_str}
- Device: {device_name}

If this was you, you can safely ignore this email.
If you did not initiate this login, please secure your account immediately.

Best regards,
Team Aurevix
"""

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #080c14;
                margin: 0;
                padding: 30px 15px;
                color: #e2e8f0;
            }}
            .card {{
                max-width: 520px;
                margin: 0 auto;
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}
            .header {{
                background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
                padding: 30px 25px;
                text-align: center;
                border-bottom: 1px solid #1e293b;
            }}
            .header h1 {{
                margin: 0;
                font-size: 26px;
                color: #00d4ff;
                letter-spacing: 1px;
            }}
            .header p {{
                margin: 8px 0 0;
                color: #94a3b8;
                font-size: 14px;
            }}
            .content {{
                padding: 30px 25px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #f8fafc;
                margin-bottom: 15px;
            }}
            .details-box {{
                background: #1e293b;
                border-radius: 10px;
                padding: 18px;
                margin: 20px 0;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.06);
                font-size: 14px;
            }}
            .detail-row:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                color: #94a3b8;
            }}
            .detail-value {{
                color: #38bdf8;
                font-weight: 500;
            }}
            .footer {{
                background: #090d16;
                padding: 20px 25px;
                text-align: center;
                font-size: 12px;
                color: #64748b;
                border-top: 1px solid #1e293b;
            }}
            .badge {{
                display: inline-block;
                background: rgba(34, 197, 94, 0.15);
                color: #22c55e;
                padding: 4px 12px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h1>🖐️ Aurevix</h1>
                <p>Security & Activity Notification</p>
            </div>
            <div class="content">
                <div class="greeting">Hello {name},</div>
                <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6;">
                    A new sign-in was detected on your Aurevix account.
                </p>

                <div class="details-box">
                    <div class="detail-row">
                        <span class="detail-label">Sign-in Method</span>
                        <span class="detail-value">{auth_method}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date & Time</span>
                        <span class="detail-value">{now_str}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Device</span>
                        <span class="detail-value">{device_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status</span>
                        <span class="badge">Authenticated</span>
                    </div>
                </div>

                <p style="color: #94a3b8; font-size: 13px; line-height: 1.5; margin-top: 20px;">
                    If this was you, you can safely ignore this email. If you did not log in, please check your account security immediately.
                </p>
            </div>
            <div class="footer">
                &copy; {datetime.datetime.now().year} Aurevix Gesture & Voice Control System. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipient_email, msg.as_string())
        print(f"[EmailService] Login alert successfully sent to {recipient_email}")
    except Exception as e:
        print(f"[EmailService] Failed to send login alert to {recipient_email}: {e}")
