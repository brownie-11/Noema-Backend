import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

def _cfg():
    return {
        "host":  os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port":  int(os.getenv("SMTP_PORT", "587")),
        "user":  os.getenv("SMTP_USER", ""),
        "pass":  os.getenv("SMTP_PASS", ""),
        "admin": os.getenv("ADMIN_EMAIL", ""),
    }

def _ready():
    c = _cfg()
    if not c["user"] or not c["pass"] or not c["admin"]:
        logger.warning("EMAIL: SMTP not configured — skipping")
        return False
    return True

def _send(msg):
    c = _cfg()
    try:
        with smtplib.SMTP(c["host"], c["port"], timeout=15) as s:
            s.ehlo(); s.starttls()
            s.login(c["user"], c["pass"])
            s.sendmail(c["user"], msg["To"], msg.as_string())
        logger.info("EMAIL: Sent to %s", msg["To"])
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("EMAIL: Auth failed — use a Gmail App Password")
        return False
    except Exception as e:
        logger.error("EMAIL: Failed — %s", e)
        return False

def send_submission_notification(username, user_email, content,
                                  submission_id, title=None,
                                  category=None, timestamp=None):
    if not _ready(): return False
    c  = _cfg()
    ts = timestamp or datetime.utcnow()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New Fragment #{submission_id} from {username}"
    msg["From"]    = c["user"]
    msg["To"]      = c["admin"]
    plain = f"From: {username} ({user_email})\nCategory: {category}\n\n{content}"
    html  = f"<html><body style='font-family:Georgia;background:#03040a;color:#e8e4dc;padding:2rem'><h2 style='color:#c8a97e;font-weight:300'>N◦ema · New Fragment</h2><p><b>From:</b> {username} &lt;{user_email}&gt;<br/><b>Category:</b> {category or 'other'}<br/><b>Time:</b> {ts.strftime('%Y-%m-%d %H:%M UTC')}</p><hr style='border-color:#1a1f2e'/><p style='font-size:1.05rem;line-height:1.8;white-space:pre-wrap'>{content}</p></body></html>"
    msg.attach(MIMEText(plain,"plain")); msg.attach(MIMEText(html,"html"))
    return _send(msg)

def send_signup_notification(username, user_email, timestamp):
    if not _ready(): return False
    c   = _cfg()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Noema] New mind — @{username}"
    msg["From"]    = c["user"]
    msg["To"]      = c["admin"]
    msg.attach(MIMEText(
        f"New signup: @{username} ({user_email}) at {timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
        "plain"
    ))
    return _send(msg)

def send_password_reset_email(user_email, username, reset_token, frontend_url):
    if not _ready(): return False
    c   = _cfg()
    url = f"{frontend_url}?reset_token={reset_token}&email={user_email}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your Noema password"
    msg["From"]    = c["user"]
    msg["To"]      = user_email
    plain = f"Hello @{username},\n\nReset your password here:\n{url}\n\nExpires in 1 hour."
    html  = f"<html><body style='font-family:Georgia;background:#03040a;color:#e8e4dc;padding:2rem'><h2 style='color:#c8a97e;font-weight:300'>N◦ema · Password Reset</h2><p>Hello <b>@{username}</b>,</p><p style='margin:1.5rem 0'><a href='{url}' style='padding:.9rem 2rem;background:rgba(200,169,126,.2);border:1px solid rgba(200,169,126,.4);color:#e8e4dc;text-decoration:none;border-radius:2px'>Reset my password →</a></p><p style='color:#7a7672;font-size:.85rem'>Expires in 1 hour.</p></body></html>"
    msg.attach(MIMEText(plain,"plain")); msg.attach(MIMEText(html,"html"))
    return _send(msg)
