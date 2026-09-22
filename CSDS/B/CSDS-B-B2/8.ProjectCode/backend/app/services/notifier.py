"""Complaint notifications by Telegram and email. Messages wait in a retry queue, so outages only delay them."""
from __future__ import annotations

import html
import json
import logging
import smtplib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import utcnow
from ..core.logging import log_event
from ..models import Complaint, Notification, User
from . import settings_service

log = logging.getLogger("signalscout.notify")
BACKOFF_MIN = [1, 5, 15, 60, 180, 360, 720]
MAX_ATTEMPTS = 8
UNDELIVERABLE_SUFFIXES = (".demo", ".invalid", ".local", ".test")

EVENT_TEXT = {
    "registered": ("New complaint", "A zone has stayed Weak/Dead beyond the threshold and has been registered."),
    "reopened": ("Complaint reopened", "New readings after the fix still show Weak/Dead service."),
    "verified": ("Fix verified", "New readings after the fix show Strong service - the complaint is closed."),
    "acknowledged": ("Complaint acknowledged", "An engineer has acknowledged the complaint."),
    "in_progress": ("Work in progress", "An engineer has started work on the complaint."),
    "resolved": ("Marked resolved", "An engineer marked the complaint resolved. New readings will verify the fix."),
    "dismissed": ("Complaint dismissed", "The complaint was dismissed."),
}
DESK_EVENTS = {"registered", "reopened", "verified"}


def telegram_ready(db: Session) -> tuple[bool, str]:
    cfg = settings_service.get_all(db)
    return bool(settings.telegram_bot_token and cfg["telegram_chat_id"] and cfg["notify_telegram"]), cfg["telegram_chat_id"]


def email_ready(db: Session) -> bool:
    return bool(settings.smtp_user and settings.smtp_password and settings_service.get_all(db)["notify_email"])


def _link(c: Complaint) -> str:
    return f"{settings.dashboard_url.rstrip('/')}/app/complaints/{c.id}"


def _body(c: Complaint, event: str) -> tuple[str, str, str]:
    title, lead = EVENT_TEXT.get(event, ("Complaint update", ""))
    ev = c.evidence or {}
    classes = ev.get("classes", {})
    subject = f"[SignalScout] {title}: {c.ref_code} - {c.operator}"
    lines = [lead, "", f"Reference: {c.ref_code}", f"Operator: {c.operator}", f"Status: {c.status.replace('_', ' ')}",
             f"Severity: {c.severity}", f"Location: {c.lat:.5f}, {c.lon:.5f} (zone {c.h3_cell})",
             f"Readings: {ev.get('readings', 0)} - Dead {classes.get('Dead', 0)}, Weak {classes.get('Weak', 0)}, Strong {classes.get('Strong', 0)}"]
    if c.summary:
        lines += ["", c.summary]
    lines += ["", f"Open in SignalScout: {_link(c)}"]
    text = "\n".join(lines)
    tg = (f"<b>{html.escape(title)}</b> - {html.escape(c.ref_code)}\n{html.escape(lead)}\n\n"
          f"<b>Operator:</b> {html.escape(c.operator)}\n<b>Status:</b> {html.escape(c.status.replace('_', ' '))} · <b>Severity:</b> {c.severity}\n"
          f"<b>Readings:</b> {ev.get('readings', 0)} (Dead {classes.get('Dead', 0)}, Weak {classes.get('Weak', 0)})\n"
          f"<a href=\"https://www.openstreetmap.org/?mlat={c.lat:.5f}&mlon={c.lon:.5f}#map=17/{c.lat:.5f}/{c.lon:.5f}\">Map location</a>")
    return subject, text, tg


def queue_for_complaint(db: Session, c: Complaint, event: str) -> int:
    """Queue desk notifications (registered / reopened / verified) and reporter emails (every status change)."""
    if c.source == "sample_dataset":
        return 0
    subject, text, tg = _body(c, event)
    rows = []
    if event in DESK_EVENTS:
        ok, chat = telegram_ready(db)
        if ok:
            rows.append(Notification(complaint_id=c.id, channel="telegram", recipient=chat, subject=subject, body=tg))
        if email_ready(db) and settings.desk_email:
            rows.append(Notification(complaint_id=c.id, channel="email", recipient=settings.desk_email, subject=subject, body=text))
    if c.reporter_user_id and email_ready(db):
        reporter = db.get(User, c.reporter_user_id)
        if reporter and reporter.notify_email and not reporter.email.endswith(UNDELIVERABLE_SUFFIXES):
            rows.append(Notification(complaint_id=c.id, channel="email", recipient=reporter.email, subject=subject, body=text))
    db.add_all(rows)
    return len(rows)


def _send_telegram(chat_id: str, body: str) -> None:
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": body, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            reply = json.loads(r.read())
    except urllib.error.HTTPError as e:
        reply = json.loads(e.read() or b"{}")
    if not reply.get("ok"):
        raise RuntimeError(reply.get("description", "Telegram rejected the message"))


def _send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def send_pending(db: Session, limit: int = 20) -> int:
    now = utcnow()
    due = (db.query(Notification).filter(Notification.status == "pending", Notification.next_attempt_at <= now)
           .order_by(Notification.created_at).limit(limit).all())
    sent = 0
    for n in due:
        try:
            if n.channel == "telegram":
                _send_telegram(n.recipient, n.body)
            else:
                _send_email(n.recipient, n.subject, n.body)
            n.status, n.sent_at, n.last_error = "sent", utcnow(), None
            sent += 1
        except Exception as exc:   # network down, bad token... keep it queued with backoff
            n.attempts += 1
            n.last_error = str(exc)[:500]
            if n.attempts >= MAX_ATTEMPTS:
                n.status = "failed"
            else:
                n.next_attempt_at = utcnow() + timedelta(minutes=BACKOFF_MIN[min(n.attempts - 1, len(BACKOFF_MIN) - 1)])
            log_event(log, "notification failed", logging.WARNING, channel=n.channel, attempt=n.attempts, error=n.last_error[:120])
        db.commit()
    if sent:
        log_event(log, "notifications sent", count=sent)
    return sent


def send_test(db: Session) -> list[dict]:
    """Send a real test message on every configured channel, immediately."""
    results = []
    ok, chat = telegram_ready(db)
    if settings.telegram_bot_token and chat:
        try:
            _send_telegram(chat, "<b>SignalScout test</b>\nComplaint notifications will arrive in this chat.")
            results.append({"channel": "telegram", "ok": True, "detail": "Sent"})
        except Exception as exc:
            results.append({"channel": "telegram", "ok": False, "detail": str(exc)})
    else:
        results.append({"channel": "telegram", "ok": False, "detail": "Not configured - add the bot token and link a chat"})
    if settings.smtp_user and settings.smtp_password and (settings.desk_email or settings.smtp_user):
        try:
            _send_email(settings.desk_email or settings.smtp_user, "[SignalScout] Test notification", "Complaint notifications will arrive at this address.")
            results.append({"channel": "email", "ok": True, "detail": f"Sent to {settings.desk_email or settings.smtp_user}"})
        except Exception as exc:
            results.append({"channel": "email", "ok": False, "detail": str(exc)})
    else:
        results.append({"channel": "email", "ok": False, "detail": "Not configured - add SMTP_USER and SMTP_PASSWORD to .env"})
    return results


def link_telegram_chat(db: Session, user_id: int | None) -> dict:
    """Find the chat that most recently messaged the bot and use it for desk notifications."""
    if not settings.telegram_bot_token:
        return {"ok": False, "detail": "TELEGRAM_BOT_TOKEN is not set in .env"}
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates", timeout=15) as r:
            updates = json.loads(r.read()).get("result", [])
    except Exception as exc:
        return {"ok": False, "detail": f"Could not reach Telegram: {exc}"}
    chats = []
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or u.get("my_chat_member") or {}
        if msg.get("chat"):
            chats.append(msg["chat"])
    if not chats:
        return {"ok": False, "detail": "No messages found. Open your bot in Telegram, tap Start and send any message, then try again."}
    chat = chats[-1]
    settings_service.update(db, {"telegram_chat_id": str(chat["id"])}, user_id)
    name = chat.get("title") or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")])) or str(chat["id"])
    try:
        _send_telegram(str(chat["id"]), "<b>SignalScout</b> is linked to this chat. Complaint updates will appear here.")
    except Exception as exc:
        return {"ok": False, "detail": f"Chat found ({name}) but sending failed: {exc}"}
    return {"ok": True, "detail": f"Linked to {name}", "chat_id": str(chat["id"])}
