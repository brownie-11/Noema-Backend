import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from backend.config import settings

logger = logging.getLogger(__name__)


def _build_submission_email(
    username: str,
    user_email: str,
    content: str,
    submission_id: int,
    title: str | None,
    category: str | None,
    timestamp: datetime,
) -> MIMEMultipart:
    """Build the MIME email for a new submission notification."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New Fragment — #{submission_id} from {username}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.ADMIN_EMAIL

    plain = f"""
── NOEMA FRAGMENT ─────────────────────────────────────────

Submission ID : #{submission_id}
From          : {username}
Email         : {user_email}
Category      : {category or 'other'}
Title         : {title or '(untitled)'}
Timestamp     : {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Fragment:
{content}

──────────────────────────────────────────────────────────
Review at: http://localhost:8000/admin/submissions
    """.strip()

    html = f"""
<html><body style="font-family:monospace;background:#03040a;color:#e8e4dc;padding:2rem;">
  <h2 style="color:#c8a97e;font-weight:300;">Noema · New Fragment</h2>
  <table style="border-collapse:collapse;width:100%;max-width:600px;">
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;">ID</td><td>#{submission_id}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;">From</td><td>{username}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;">Email</td><td>{user_email}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;">Category</td><td>{category or 'other'}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;">Title</td><td>{title or '(untitled)'}</td></tr>
    <tr><td style="color:#7a7672;padding:.3rem 1rem .3rem 0;">Time</td><td>{timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
  </table>
  <hr style="border-color:#0d1018;margin:1.5rem 0;">
  <p style="font-family:'Georgia',serif;font-size:1.1rem;line-height:1.8;color:#e8e4dc;">{content}</p>
  <hr style="border-color:#0d1018;margin:1.5rem 0;">
  <a href="http://localhost:8000/admin/submissions" style="color:#c8a97e;">Review submission →</a>
</body></html>
    """.strip()

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_submission_notification(
    username: str,
    user_email: str,
    content: str,
    submission_id: int,
    title: str | None = None,
    category: str | None = None,
    timestamp: datetime | None = None,
) -> bool:
    """
    Send a new-submission notification email to the admin.
    Returns True on success, False on failure (never raises — email is non-critical).
    """
    if not settings.ADMIN_EMAIL or not settings.SMTP_USER:
        logger.info("Email not configured — skipping notification for submission #%s", submission_id)
        return False

    try:
        msg = _build_submission_email(
            username=username,
            user_email=user_email,
            content=content,
            submission_id=submission_id,
            title=title,
            category=category,
            timestamp=timestamp or datetime.utcnow(),
        )
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, settings.ADMIN_EMAIL, msg.as_string())
        logger.info("Submission notification sent for #%s", submission_id)
        return True
    except Exception as exc:
        logger.warning("Failed to send submission email for #%s: %s", submission_id, exc)
        return False
