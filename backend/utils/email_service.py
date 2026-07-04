"""
Noema Email Service
Handles all outgoing emails — submission notifications, signups, password resets.
Uses Gmail SMTP with App Password.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from backend.config import settings

logger = logging.getLogger(__name__)


def _check_config() -> bool:
    """Return True if SMTP is configured. Log clearly if not."""
    if not settings.SMTP_USER:
        logger.warning("EMAIL: SMTP_USER not set — emails disabled")
        return False
    if not settings.SMTP_PASS:
        logger.warning("EMAIL: SMTP_PASS not set — emails disabled")
        return False
    if not settings.ADMIN_EMAIL:
        logger.warning("EMAIL: ADMIN_EMAIL not set — emails disabled")
        return False
    return True


def _send(msg: MIMEMultipart) -> bool:
    """Send a MIME message. Returns True on success, logs error on failure."""
    try:
        logger.info("EMAIL: Connecting to %s:%s", settings.SMTP_HOST, settings.SMTP_PORT)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, msg["To"], msg.as_string())
        logger.info("EMAIL: Sent to %s ✓", msg["To"])
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "EMAIL: Authentication failed. "
            "Make sure you are using a Gmail App Password, not your regular Gmail password. "
            "Go to myaccount.google.com → Security → App Passwords to generate one."
        )
        return False
    except smtplib.SMTPException as exc:
        logger.error("EMAIL: SMTP error — %s", exc)
        return False
    except Exception as exc:
        logger.error("EMAIL: Unexpected error — %s", exc)
        return False


def send_submission_notification(
    username: str,
    user_email: str,
    content: str,
    submission_id: int,
    title: str | None = None,
    category: str | None = None,
    timestamp: datetime | None = None,
) -> bool:
    """Notify admin when someone submits a thought fragment."""
    if not _check_config():
        return False

    ts = timestamp or datetime.utcnow()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New Fragment #{submission_id} — from {username}"
    msg["From"]    = settings.SMTP_USER
    msg["To"]      = settings.ADMIN_EMAIL

    plain = f"""
── NOEMA · NEW FRAGMENT ────────────────────────────────

ID        : #{submission_id}
From      : {username}
Email     : {user_email}
Category  : {category or 'other'}
Title     : {title or '(untitled)'}
Time      : {ts.strftime('%Y-%m-%d %H:%M UTC')}

─────────────────────────────────────────────────────────

{content}

─────────────────────────────────────────────────────────
""".strip()

    html = f"""
<html>
<body style="font-family:Georgia,serif;background:#03040a;color:#e8e4dc;padding:2rem;max-width:600px;margin:0 auto">
  <div style="border-bottom:1px solid rgba(200,169,126,.2);padding-bottom:1rem;margin-bottom:1.5rem">
    <h2 style="font-weight:300;color:#c8a97e;margin:0;font-size:1.4rem">N◦ema · New Fragment</h2>
  </div>
  <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem">
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem;white-space:nowrap">SUBMISSION</td><td style="font-family:monospace;font-size:.8rem">#{submission_id}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem;white-space:nowrap">FROM</td><td style="font-family:monospace;font-size:.8rem">{username}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem;white-space:nowrap">EMAIL</td><td style="font-family:monospace;font-size:.8rem">{user_email}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem;white-space:nowrap">CATEGORY</td><td style="font-family:monospace;font-size:.8rem">{category or 'other'}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem;white-space:nowrap">TIME</td><td style="font-family:monospace;font-size:.8rem">{ts.strftime('%Y-%m-%d %H:%M UTC')}</td></tr>
  </table>
  <div style="border:1px solid rgba(200,169,126,.15);border-radius:4px;padding:1.5rem;background:rgba(255,255,255,.02)">
    <p style="font-size:1.05rem;line-height:1.85;margin:0;white-space:pre-wrap;color:rgba(232,228,220,.85)">{content}</p>
  </div>
  <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.06);font-family:monospace;font-size:.7rem;color:#7a7672">
    Noema · A living universe of thought
  </div>
</body>
</html>
""".strip()

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    return _send(msg)


def send_signup_notification(username: str, user_email: str, timestamp: datetime) -> bool:
    """Notify admin when a new user signs up."""
    if not _check_config():
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New mind joined — @{username}"
    msg["From"]    = settings.SMTP_USER
    msg["To"]      = settings.ADMIN_EMAIL

    plain = f"""
── NOEMA · NEW MIND ─────────────────────────────────────

Username : @{username}
Email    : {user_email}
Joined   : {timestamp.strftime('%Y-%m-%d %H:%M UTC')}

─────────────────────────────────────────────────────────
""".strip()

    html = f"""
<html>
<body style="font-family:Georgia,serif;background:#03040a;color:#e8e4dc;padding:2rem;max-width:600px;margin:0 auto">
  <div style="border-bottom:1px solid rgba(200,169,126,.2);padding-bottom:1rem;margin-bottom:1.5rem">
    <h2 style="font-weight:300;color:#c8a97e;margin:0;font-size:1.4rem">N◦ema · New Mind Joined</h2>
  </div>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem">USERNAME</td><td style="font-family:monospace;font-size:.8rem">@{username}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem">EMAIL</td><td style="font-family:monospace;font-size:.8rem">{user_email}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1.5rem .3rem 0;font-family:monospace;font-size:.8rem">JOINED</td><td style="font-family:monospace;font-size:.8rem">{timestamp.strftime('%Y-%m-%d %H:%M UTC')}</td></tr>
  </table>
</body>
</html>
""".strip()

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    return _send(msg)


def send_password_reset_email(
    user_email: str,
    username: str,
    reset_token: str,
    frontend_url: str,
) -> bool:
    """
    Send a password reset link to the user.
    The reset link points to the frontend with the token as a query param.
    """
    if not _check_config():
        return False

    reset_url = f"{frontend_url}?reset_token={reset_token}&email={user_email}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your Noema password"
    msg["From"]    = settings.SMTP_USER
    msg["To"]      = user_email

    plain = f"""
── NOEMA · PASSWORD RESET ───────────────────────────────

Hello {username},

You requested a password reset for your Noema account.

Click the link below to set a new password:
{reset_url}

This link expires in 1 hour.

If you did not request this, ignore this email.

─────────────────────────────────────────────────────────
Noema · A living universe of thought
""".strip()

    html = f"""
<html>
<body style="font-family:Georgia,serif;background:#03040a;color:#e8e4dc;padding:2rem;max-width:600px;margin:0 auto">
  <div style="border-bottom:1px solid rgba(200,169,126,.2);padding-bottom:1rem;margin-bottom:1.5rem">
    <h2 style="font-weight:300;color:#c8a97e;margin:0;font-size:1.4rem">N◦ema · Password Reset</h2>
  </div>
  <p style="color:rgba(232,228,220,.7);line-height:1.8">Hello <strong style="color:#e8e4dc">@{username}</strong>,</p>
  <p style="color:rgba(232,228,220,.7);line-height:1.8">You requested a password reset for your Noema account. Click below to set a new password.</p>
  <div style="text-align:center;margin:2rem 0">
    <a href="{reset_url}" style="display:inline-block;padding:.9rem 2.2rem;background:linear-gradient(135deg,rgba(200,169,126,.2),rgba(139,181,200,.15));border:1px solid rgba(200,169,126,.4);color:#e8e4dc;text-decoration:none;font-family:monospace;font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;border-radius:2px">
      Reset my password →
    </a>
  </div>
  <p style="color:#7a7672;font-family:monospace;font-size:.75rem;line-height:1.6">This link expires in 1 hour.<br/>If you did not request this, ignore this email.</p>
  <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.06);font-family:monospace;font-size:.7rem;color:#7a7672">
    Noema · A living universe of thought
  </div>
</body>
</html>
""".strip()

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    return _send(msg)
