"""
backend/email_service.py  —  Gmail SMTP reminder email sender

Uses Python's built-in smtplib + ssl (no extra packages required).

Required environment variables:
    GMAIL_USER          — the Gmail address used to send (e.g. you@gmail.com)
    GMAIL_APP_PASSWORD  — 16-char App Password from Google Account → Security
    NOTIFICATION_EMAIL  — recipient address (can be same as GMAIL_USER)
"""

import os
import ssl
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465   # SSL port

def get_credentials():
    """Retrieve and sanitize Gmail credentials from environment."""
    user = os.environ.get("GMAIL_USER", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    recipient = (os.environ.get("NOTIFICATION_EMAIL", "") or user).strip()
    return user, password, recipient


# ── HTML email template ───────────────────────────────────────────────────────

def _build_html(
    title: str,
    description: str | None,
    due_date: str | None,
    reminder_time: str | None,
    is_overdue: bool = False,
) -> str:
    sent_at  = datetime.now().strftime("%d %b %Y, %I:%M %p")
    date_str = due_date      or "Today"
    time_str = reminder_time or ""

    if is_overdue:
        # ── URGENT: missed deadline ─────────────────────────────────────────
        header_gradient = "linear-gradient(135deg, #dc2626, #f97316)"
        header_emoji    = "&#x1F6A8;"   # 🚨
        header_title    = "OVERDUE &mdash; Action Required!"
        header_sub      = "This task has passed its due date"
        urgency_banner  = """
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;
                    padding:12px 16px;margin:16px 0;color:#c2410c;font-size:14px;font-weight:600;">
          &#9200;&nbsp; This to-do item is <strong>PENDING</strong>.
          Please complete it <strong>as soon as possible!</strong>
        </div>"""
        date_chip_color  = "#dc2626"
        date_chip_bg     = "rgba(220,38,38,0.10)"
        date_chip_border = "rgba(220,38,38,0.35)"
        date_label       = "&#9888; Overdue: " + date_str
        body_text        = ("This task is <strong>past its due date</strong> and still "
                            "pending. Please take action immediately!")
        footer_note      = "&#9889; Sent automatically because this task is past its due date."
    else:
        # ── Regular: reminder at scheduled time ─────────────────────────────
        header_gradient = "linear-gradient(135deg,#6C63FF,#48B2E8)"
        header_emoji    = "&#x1F514;"   # 🔔
        header_title    = "Reminder Alert"
        header_sub      = "Your Todo Reminder App"
        urgency_banner  = ""
        date_chip_color  = "#6C63FF"
        date_chip_bg     = "rgba(108,99,255,0.10)"
        date_chip_border = "rgba(108,99,255,0.30)"
        date_label       = "&#x1F4C5; Due: " + date_str
        body_text        = "This task is due and hasn't been completed yet. Don't forget to mark it done!"
        footer_note      = f"Sent automatically at {sent_at} &middot; Todo Reminder App"

    desc_block = (
        f"<p style='color:#555;margin:8px 0 0;font-size:14px;line-height:1.5'>{description}</p>"
        if description else ""
    )
    time_chip = (
        f"<span style='background:rgba(94,234,212,0.12);border:1px solid rgba(94,234,212,0.3);"
        f"color:#0d9488;border-radius:20px;padding:4px 14px;font-size:13px;font-weight:500;"
        f"display:inline-block'>&#x23F0; {time_str}</span>"
        if time_str else ""
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body{{font-family:'Segoe UI',Arial,sans-serif;background:#f4f6fb;margin:0;padding:0}}
    .wrapper{{max-width:520px;margin:32px auto;background:#fff;border-radius:12px;
              overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.12)}}
    .header{{background:{header_gradient};padding:28px 32px;color:#fff}}
    .header h1{{margin:0;font-size:22px;font-weight:700}}
    .header p{{margin:6px 0 0;opacity:.85;font-size:13px}}
    .body{{padding:28px 32px}}
    .task-title{{font-size:20px;font-weight:700;color:#1a1a2e;margin:0 0 4px}}
    .chips{{display:flex;gap:10px;margin:14px 0;flex-wrap:wrap;align-items:center}}
    .chip{{border-radius:20px;padding:4px 14px;font-size:13px;font-weight:500;
           display:inline-block;border:1px solid {date_chip_border};
           background:{date_chip_bg};color:{date_chip_color}}}
    .footer{{background:#f9f9fc;padding:14px 32px;font-size:12px;
             color:#999;border-top:1px solid #eee;line-height:1.5}}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>{header_emoji} {header_title}</h1>
      <p>{header_sub}</p>
    </div>
    <div class="body">
      <p class="task-title">{title}</p>
      {desc_block}
      {urgency_banner}
      <div class="chips">
        <span class="chip">{date_label}</span>
        {time_chip}
      </div>
      <p style="color:#555;font-size:14px;line-height:1.7;margin-top:10px">
        {body_text}
      </p>
    </div>
    <div class="footer">{footer_note}</div>
  </div>
</body>
</html>"""


def _build_plain(
    title: str,
    description: str | None,
    due_date: str | None,
    reminder_time: str | None,
    is_overdue: bool = False,
) -> str:
    if is_overdue:
        lines = [
            "🚨 OVERDUE — ACTION REQUIRED!",
            "=" * 45,
            f"Task    : {title}",
        ]
        if description:
            lines.append(f"Note    : {description}")
        if due_date:
            lines.append(f"Was due : {due_date}  (DEADLINE MISSED)")
        lines += [
            "",
            "⚠  This to-do item is PENDING.",
            "   Please complete it AS SOON AS POSSIBLE!",
            "",
            f"Sent at {datetime.now().strftime('%d %b %Y, %I:%M %p')} · Todo Reminder App",
        ]
    else:
        lines = [
            "🔔 REMINDER — Todo Reminder App",
            "=" * 45,
            f"Task : {title}",
        ]
        if description:
            lines.append(f"Note : {description}")
        if due_date:
            lines.append(f"Due  : {due_date}")
        if reminder_time:
            lines.append(f"Time : {reminder_time}")
        lines += [
            "",
            "This task is due and hasn't been completed yet.",
            "",
            f"Sent at {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        ]
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def send_reminder_email(
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    reminder_time: str | None = None,
    is_overdue: bool = False,
) -> bool:
    """
    Send a Gmail reminder email for a todo item.

    Args:
        title:         Task title.
        description:   Optional task description.
        due_date:      Due date string (YYYY-MM-DD).
        reminder_time: Reminder time string (HH:MM).
        is_overdue:    True  → urgent red "ASAP" email (missed deadline).
                       False → normal blue reminder email.

    Returns True on success.
    Raises ValueError if credentials are missing, or smtplib errors on send failure.
    """
    user, password, recipient = get_credentials()
    if not user or not password:
        raise ValueError(
            "GMAIL_USER and GMAIL_APP_PASSWORD environment variables must be set."
        )

    subject = (
        f"\U0001F6A8 OVERDUE: {title} \u2014 Please complete ASAP!"
        if is_overdue
        else f"\U0001F514 Reminder: {title}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Todo Reminder <{user}>"
    msg["To"]      = recipient

    msg.attach(MIMEText(
        _build_plain(title, description, due_date, reminder_time, is_overdue), "plain"
    ))
    msg.attach(MIMEText(
        _build_html(title, description, due_date, reminder_time, is_overdue),  "html"
    ))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(user, password)
            server.sendmail(user, recipient, msg.as_string())
        logger.info(
            "[%s] Reminder email sent for: '%s' → %s",
            "OVERDUE" if is_overdue else "ON-TIME",
            title,
            recipient,
        )
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.")
        raise
    except Exception as exc:
        logger.error("Failed to send reminder email: %s", exc)
        raise


def email_configured() -> bool:
    """Returns True if Gmail credentials are present in environment."""
    user, password, _ = get_credentials()
    return bool(user and password)
