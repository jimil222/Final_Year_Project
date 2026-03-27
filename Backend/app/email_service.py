import asyncio
import logging
import os
from datetime import datetime, timedelta

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from dotenv import load_dotenv

from app.db import db

logger = logging.getLogger(__name__)

load_dotenv()


class EmailSendError(Exception):
    pass
REMINDER_POLL_INTERVAL_SECONDS = int(os.getenv("REMINDER_POLL_INTERVAL_SECONDS", "3600"))

_sent_due_reminder_cache = set()


def _smtp_settings() -> dict:
    mail_port_raw = os.getenv("MAIL_PORT", "587").strip() or "587"
    return {
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME", "").strip(),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD", "").strip(),
        "MAIL_FROM": os.getenv("MAIL_FROM", "").strip(),
        "MAIL_FROM_NAME": os.getenv("MAIL_FROM_NAME", "Library Team").strip(),
        "MAIL_SERVER": os.getenv("MAIL_SERVER", "").strip(),
        "MAIL_PORT": int(mail_port_raw),
        "MAIL_STARTTLS": os.getenv("MAIL_STARTTLS", "true").strip().lower() in {"1", "true", "yes", "on"},
        "MAIL_SSL_TLS": os.getenv("MAIL_SSL_TLS", "false").strip().lower() in {"1", "true", "yes", "on"},
        "MAIL_VALIDATE_CERTS": os.getenv("MAIL_VALIDATE_CERTS", "true").strip().lower() in {"1", "true", "yes", "on"},
    }


def get_missing_smtp_fields() -> list:
    settings = _smtp_settings()
    required = ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM", "MAIL_SERVER", "MAIL_PORT"]
    return [k for k in required if not settings.get(k)]


def _is_smtp_configured() -> bool:
    return len(get_missing_smtp_fields()) == 0


def _mail_config() -> ConnectionConfig:
    settings = _smtp_settings()
    return ConnectionConfig(
        MAIL_USERNAME=settings["MAIL_USERNAME"],
        MAIL_PASSWORD=settings["MAIL_PASSWORD"],
        MAIL_FROM=settings["MAIL_FROM"],
        MAIL_FROM_NAME=settings["MAIL_FROM_NAME"],
        MAIL_PORT=settings["MAIL_PORT"],
        MAIL_SERVER=settings["MAIL_SERVER"],
        MAIL_STARTTLS=settings["MAIL_STARTTLS"],
        MAIL_SSL_TLS=settings["MAIL_SSL_TLS"],
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=settings["MAIL_VALIDATE_CERTS"],
    )


def _format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


async def send_email(to_email: str, subject: str, html: str, text: str, raise_on_error: bool = False) -> bool:
    if not _is_smtp_configured():
        missing = ", ".join(get_missing_smtp_fields())
        message = f"SMTP email is not configured. Missing: {missing}"
        logger.warning(message)
        if raise_on_error:
            raise EmailSendError(message)
        return False

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html,
        subtype=MessageType.html,
    )

    try:
        fm = FastMail(_mail_config())
        await fm.send_message(message)
        return True
    except Exception as exc:
        logger.exception("Unexpected email send failure: %s", exc)
        if raise_on_error:
            raise EmailSendError(str(exc))
        return False


async def send_book_approval_email(
    *,
    to_email: str,
    user_name: str,
    book_name: str,
    author: str,
    issue_datetime: datetime,
    return_datetime: datetime,
) -> bool:
    subject = f"Book Request Approved: {book_name}"
    issue_text = _format_dt(issue_datetime)
    return_text = _format_dt(return_datetime)

    html = f"""
    <div style=\"font-family: Arial, sans-serif; line-height: 1.6;\">
      <h2>Your book request has been approved</h2>
      <p>Hello {user_name},</p>
      <p>Your request has been approved. Here are your book details:</p>
      <ul>
        <li><strong>Book:</strong> {book_name}</li>
        <li><strong>Author:</strong> {author or 'N/A'}</li>
        <li><strong>Issue Date & Time:</strong> {issue_text}</li>
        <li><strong>Return Due Date & Time:</strong> {return_text}</li>
      </ul>
      <p>Please return or renew the book on or before the due date.</p>
      <p>Thanks,<br/>Library Team</p>
    </div>
    """
    text = (
        f"Hello {user_name},\n\n"
        f"Your request for '{book_name}' has been approved.\n"
        f"Author: {author or 'N/A'}\n"
        f"Issue Date & Time: {issue_text}\n"
        f"Return Due Date & Time: {return_text}\n\n"
        "Please return or renew the book on or before the due date.\n"
        "Library Team"
    )
    return await send_email(to_email, subject, html, text)


async def send_due_soon_email(
    *,
    to_email: str,
    user_name: str,
    book_name: str,
    due_datetime: datetime,
) -> bool:
    subject = f"Reminder: Return or Renew '{book_name}' in 1 day"
    due_text = _format_dt(due_datetime)
    html = f"""
    <div style=\"font-family: Arial, sans-serif; line-height: 1.6;\">
      <h2>Return/Renew Reminder</h2>
      <p>Hello {user_name},</p>
      <p>This is a reminder that your borrowed book is due in about 1 day.</p>
      <ul>
        <li><strong>Book:</strong> {book_name}</li>
        <li><strong>Due Date & Time:</strong> {due_text}</li>
      </ul>
      <p>Please return or renew the book before the due date to avoid overdue status.</p>
      <p>Thanks,<br/>Library Team</p>
    </div>
    """
    text = (
        f"Hello {user_name},\n\n"
        f"Reminder: '{book_name}' is due in about 1 day.\n"
        f"Due Date & Time: {due_text}\n\n"
        "Please return or renew the book before the due date.\n"
        "Library Team"
    )
    return await send_email(to_email, subject, html, text)


async def send_due_soon_reminders() -> int:
    """Send reminder for borrowed books due in ~1 day. Returns sent count."""
    now = datetime.now()
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=24)

    transactions = await db.transaction.find_many(
        where={
            "status": "BORROWED",
            "return_time": None,
            "due_date": {
                "gte": window_start,
                "lt": window_end,
            },
        },
        include={
            "user": True,
            "book": True,
        },
    )

    sent_count = 0
    for tx in transactions:
        cache_key = f"{tx.transaction_id}:{tx.due_date.strftime('%Y-%m-%d-%H')}"
        if cache_key in _sent_due_reminder_cache:
            continue

        ok = await send_due_soon_email(
            to_email=tx.user.email,
            user_name=tx.user.name,
            book_name=tx.book.book_name,
            due_datetime=tx.due_date,
        )
        if ok:
            sent_count += 1
            _sent_due_reminder_cache.add(cache_key)

    return sent_count


async def run_due_reminder_loop() -> None:
    """Background loop to periodically send due-soon reminders."""
    logger.info("Due reminder loop started. Interval=%ss", REMINDER_POLL_INTERVAL_SECONDS)
    while True:
        try:
            sent = await send_due_soon_reminders()
            if sent:
                logger.info("Sent %s due-soon reminder email(s)", sent)
        except asyncio.CancelledError:
            logger.info("Due reminder loop cancelled")
            raise
        except Exception as exc:
            logger.exception("Due reminder loop error: %s", exc)

        await asyncio.sleep(max(60, REMINDER_POLL_INTERVAL_SECONDS))
