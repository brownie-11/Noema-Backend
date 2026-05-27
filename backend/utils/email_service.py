import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from backend.config import settings

logger = logging.getLogger(__name__)


def _smtp_send(msg: MIMEMultipart) -> bool:
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            s.ehlo(); s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASS)
            s.sendmail(settings.SMTP_USER, settings.ADMIN_EMAIL, msg.as_string())
        return True
    except Exception as exc:
        logger.warning("SMTP send failed: %s", exc)
        return False


def send_submission_notification(
    username: str, user_email: str, content: str,
    submission_id: int, title=None, category=None, timestamp=None,
) -> bool:
    if not settings.ADMIN_EMAIL or not settings.SMTP_USER:
        return False
    ts = timestamp or datetime.utcnow()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New Fragment — #{submission_id} from {username}"
    msg["From"] = settings.SMTP_USER
    msg["To"]   = settings.ADMIN_EMAIL
    plain = f"""
── NOEMA FRAGMENT ──────────────────────────────────────
Submission ID : #{submission_id}
From          : {username}
Email         : {user_email}
Category      : {category or 'other'}
Title         : {title or '(untitled)'}
Timestamp     : {ts.strftime('%Y-%m-%d %H:%M:%S UTC')}

{content}
────────────────────────────────────────────────────────
""".strip()
    html = f"""
<html><body style="font-family:monospace;background:#03040a;color:#e8e4dc;padding:2rem;">
  <h2 style="color:#c8a97e;font-weight:300;">Noema · New Fragment</h2>
  <table style="border-collapse:collapse;width:100%;max-width:600px;">
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;width:120px">ID</td><td>#{submission_id}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0">From</td><td>{username}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0">Email</td><td>{user_email}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0">Category</td><td>{category or 'other'}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0">Title</td><td>{title or '(untitled)'}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0">Time</td><td>{ts.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
  </table>
  <hr style="border-color:#1a1f2e;margin:1.5rem 0;">
  <p style="font-family:Georgia,serif;font-size:1.05rem;line-height:1.8;white-space:pre-wrap;">{content}</p>
</body></html>""".strip()
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    result = _smtp_send(msg)
    if result:
        logger.info("Submission notification sent for #%s", submission_id)
    return result


def send_signup_notification(username: str, user_email: str, timestamp: datetime) -> bool:
    if not settings.ADMIN_EMAIL or not settings.SMTP_USER:
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New mind joined — @{username}"
    msg["From"] = settings.SMTP_USER
    msg["To"]   = settings.ADMIN_EMAIL
    plain = f"""
── NOEMA · NEW MIND ──────────────────────────
Username : @{username}
Email    : {user_email}
Joined   : {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
──────────────────────────────────────────────
""".strip()
    msg.attach(MIMEText(plain, "plain"))
    return _smtp_send(msg)
