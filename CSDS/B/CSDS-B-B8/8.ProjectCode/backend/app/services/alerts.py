"""Emergency alert delivery: Telegram (photo + caption) and Gmail SMTP (with snapshot attached)."""
import smtplib
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import requests

from .. import config
from ..db import Alert, Contact, SessionLocal
from .settings import get_settings


def telegram_configured():
    return bool(config.TELEGRAM_BOT_TOKEN)


def email_configured():
    return bool(config.SMTP_USER and config.SMTP_PASSWORD)


def send_telegram(chat_id, text, photo=None):
    t0 = time.perf_counter()
    base = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
    try:
        if photo and Path(photo).exists():
            with open(photo, "rb") as f:
                r = requests.post(f"{base}/sendPhoto", data={"chat_id": chat_id, "caption": text},
                                  files={"photo": f}, timeout=20)
        else:
            r = requests.post(f"{base}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=20)
        ok = r.ok and r.json().get("ok", False)
        err = "" if ok else r.json().get("description", r.text[:200])
    except Exception as e:  # network errors are reported per contact, never raised
        ok, err = False, str(e)[:200]
    return {"ok": ok, "ms": round((time.perf_counter() - t0) * 1000), "error": err}


def send_email(to, subject, body, photo=None):
    t0 = time.perf_counter()
    try:
        msg = EmailMessage()
        msg["From"] = config.SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        if photo and Path(photo).exists():
            msg.add_attachment(Path(photo).read_bytes(), maintype="image", subtype="jpeg",
                               filename=Path(photo).name)
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
            s.starttls()
            s.login(config.SMTP_USER, config.SMTP_PASSWORD)
            s.send_message(msg)
        ok, err = True, ""
    except Exception as e:
        ok, err = False, str(e)[:200]
    return {"ok": ok, "ms": round((time.perf_counter() - t0) * 1000), "error": err}


def message_for(alert, room):
    when = alert.detected_at.strftime("%d %b %Y, %H:%M:%S")
    if alert.kind == "test":
        return ("CareWatch test alert",
                f"This is a test alert from CareWatch ({room}) sent at {when}. Alerts are working.")
    return ("CareWatch EMERGENCY: possible fall detected",
            f"CareWatch detected a possible fall in the {room} at {when}.\n"
            f"Nobody pressed 'I'm OK' within the countdown. Please check on them now.")


def dispatch(alert_id):
    """Send one alert to every active contact; store per-channel results and latency."""
    t0 = time.perf_counter()
    with SessionLocal() as db:
        alert = db.get(Alert, alert_id)
        contacts = db.query(Contact).filter(Contact.active.is_(True)).all()
        room = get_settings()["room_name"]
        subject, text = message_for(alert, room)
        photo = str(config.SNAPSHOT_DIR / alert.snapshot) if alert.snapshot else None
        results = {"telegram": [], "email": []}
        tg, em = telegram_configured(), email_configured()
        for c in contacts:
            if c.telegram_chat_id:
                r = send_telegram(c.telegram_chat_id, f"{subject}\n\n{text}", photo) if tg else \
                    {"ok": False, "ms": 0, "error": "Telegram bot token not configured"}
                results["telegram"].append({"to": c.name, **r})
            if c.email:
                r = send_email(c.email, subject, text, photo) if em else \
                    {"ok": False, "ms": 0, "error": "Gmail SMTP not configured"}
                results["email"].append({"to": c.name, **r})
        delivered = sum(r["ok"] for ch in results.values() for r in ch)
        if not contacts:
            results["note"] = "No active contacts"
        alert.channels = results
        alert.dispatch_ms = round((time.perf_counter() - t0) * 1000, 1)
        alert.sent_at = datetime.now()
        alert.status = "sent" if delivered else "undelivered"
        db.commit()
        return alert.status


def dispatch_async(alert_id):
    threading.Thread(target=dispatch, args=(alert_id,), daemon=True).start()


def telegram_chats():
    """Chats that have messaged the bot recently - used to find contacts' chat IDs."""
    if not telegram_configured():
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in .env first")
    r = requests.get(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates", timeout=15)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram error"))
    chats = {}
    for u in data.get("result", []):
        m = u.get("message") or u.get("edited_message") or {}
        ch = m.get("chat")
        if ch:
            name = ch.get("title") or " ".join(x for x in (ch.get("first_name"), ch.get("last_name")) if x)
            chats[ch["id"]] = {"chat_id": str(ch["id"]), "name": name or ch.get("username", ""),
                               "username": ch.get("username", "")}
    return list(chats.values())


class AlertWatchdog:
    """Sends pending alerts whose 'I'm OK' countdown has run out."""

    def __init__(self):
        self.stop_flag = False
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while not self.stop_flag:
            try:
                now = datetime.now()
                with SessionLocal() as db:
                    due = db.query(Alert).filter(Alert.status == "pending", Alert.deadline <= now).all()
                    for a in due:
                        a.status = "sending"
                    db.commit()
                    ids = [a.id for a in due]
                for i in ids:
                    dispatch_async(i)
            except Exception as e:
                print("alert watchdog:", e)
            time.sleep(0.25)
