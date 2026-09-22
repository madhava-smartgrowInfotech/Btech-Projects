"""Check SignalScout's configuration: ports, secrets, datasets and every external service in .env.

Usage:
    python scripts/check_env.py                    # check everything that is configured
    python scripts/check_env.py --telegram-chat-id # list chat IDs that recently messaged your bot
    python scripts/check_env.py --send-test        # also send a real Telegram message and test email

Each line prints OK, WARN, FAIL or SKIP (not configured). Exit code is 1 if anything FAILs.
"""
from __future__ import annotations

import argparse
import json
import os
import smtplib
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS: list[tuple[str, str, str]] = []


def report(status: str, name: str, detail: str = "") -> None:
    RESULTS.append((status, name, detail))
    print(f"[{status:<4}] {name}{': ' + detail if detail else ''}")


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def http_json(url: str, data: dict | None = None, timeout: int = 15) -> dict:
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": "SignalScout-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": f"HTTP {exc.code}"}


def lan_ips() -> list[str]:
    ips = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.add(ip)
    except OSError:
        pass
    return sorted(ips)


def check_ports(env: dict[str, str]) -> None:
    for key, default in (("BACKEND_PORT", "8202"), ("FRONTEND_PORT", "5202")):
        port = int(env.get(key, default))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            in_use = s.connect_ex(("127.0.0.1", port)) == 0
        report("WARN" if in_use else "OK", f"Port {port} ({key})", "already in use (SignalScout running?)" if in_use else "free")
    ips = lan_ips()
    report("OK" if ips else "WARN", "LAN IP for phones / ESP32", ", ".join(ips) if ips else "no network adapter found")
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule", "name=SignalScout API 8202"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            if "8202" in out:
                report("OK", "Windows Firewall rule", "inbound TCP 8202 allowed")
            else:
                report("WARN", "Windows Firewall rule", "missing - phones on Wi-Fi cannot reach the API (see docs/03_HOW_TO_RUN.md)")
        except Exception as exc:
            report("WARN", "Windows Firewall rule", f"could not check ({exc})")


def check_secret(env: dict[str, str]) -> None:
    secret = env.get("JWT_SECRET", "")
    if not secret or secret.startswith("replace-with"):
        report("FAIL", "JWT_SECRET", "not set - run setup.bat or put a long random string in .env")
    elif len(secret) < 32:
        report("WARN", "JWT_SECRET", "shorter than 32 characters")
    else:
        report("OK", "JWT_SECRET", f"{len(secret)} characters")


def check_datasets() -> None:
    script = ROOT / "scripts" / "download_data.py"
    proc = subprocess.run([sys.executable, str(script), "--verify"], capture_output=True, text=True)
    detail = " | ".join(line.strip() for line in proc.stdout.splitlines() if line.strip())
    report("OK" if proc.returncode == 0 else "FAIL", "Datasets (data/raw)", detail or proc.stderr.strip())


def check_telegram(env: dict[str, str], send: bool) -> None:
    token, chat = env.get("TELEGRAM_BOT_TOKEN", ""), env.get("TELEGRAM_CHAT_ID", "")
    if not token:
        report("SKIP", "Telegram", "TELEGRAM_BOT_TOKEN not set")
        return
    me = http_json(f"https://api.telegram.org/bot{token}/getMe")
    if not me.get("ok"):
        report("FAIL", "Telegram bot token", me.get("description", "rejected"))
        return
    report("OK", "Telegram bot token", f"@{me['result']['username']}")
    if not chat:
        report("WARN", "Telegram chat ID", "not set - message your bot, then run with --telegram-chat-id")
        return
    info = http_json(f"https://api.telegram.org/bot{token}/getChat", {"chat_id": chat})
    if not info.get("ok"):
        report("FAIL", "Telegram chat ID", info.get("description", "bot cannot reach this chat"))
        return
    title = info["result"].get("title") or info["result"].get("first_name") or chat
    report("OK", "Telegram chat ID", f"reachable ({title})")
    if send:
        sent = http_json(
            f"https://api.telegram.org/bot{token}/sendMessage",
            {"chat_id": chat, "text": "SignalScout test: complaint notifications will arrive in this chat."},
        )
        report("OK" if sent.get("ok") else "FAIL", "Telegram test message", "sent" if sent.get("ok") else sent.get("description", ""))


def list_telegram_chats(env: dict[str, str]) -> None:
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN in .env first.")
        return
    updates = http_json(f"https://api.telegram.org/bot{token}/getUpdates")
    chats = {}
    for upd in updates.get("result", []):
        msg = upd.get("message") or upd.get("channel_post") or upd.get("my_chat_member") or {}
        chat = msg.get("chat")
        if chat:
            chats[chat["id"]] = chat.get("title") or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
    if not chats:
        print("No messages found. Open Telegram, send any message to your bot (or add it to a group and post there), then run this again.")
        return
    print("Chats that messaged your bot (put one ID in TELEGRAM_CHAT_ID):")
    for cid, name in chats.items():
        print(f"  {cid}  {name}")


def check_smtp(env: dict[str, str], send: bool) -> None:
    user, password = env.get("SMTP_USER", ""), env.get("SMTP_PASSWORD", "")
    if not user or not password:
        report("SKIP", "Email (SMTP)", "SMTP_USER / SMTP_PASSWORD not set")
        return
    host, port = env.get("SMTP_HOST", "smtp.gmail.com"), int(env.get("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user, password.replace(" ", ""))
            report("OK", "Email (SMTP) login", f"{user} via {host}:{port}")
            if send:
                to = env.get("DESK_EMAIL") or user
                msg = EmailMessage()
                msg["Subject"] = "SignalScout test email"
                msg["From"] = env.get("SMTP_FROM") or user
                msg["To"] = to
                msg.set_content("Complaint notifications from SignalScout will arrive at this address.")
                smtp.send_message(msg)
                report("OK", "Email test message", f"sent to {to}")
    except smtplib.SMTPAuthenticationError:
        report("FAIL", "Email (SMTP) login", "rejected - use a 16-character Gmail app password, not your normal password")
    except Exception as exc:
        report("FAIL", "Email (SMTP)", str(exc))


def check_opencellid(env: dict[str, str]) -> None:
    key = env.get("OPENCELLID_API_KEY", "")
    if not key:
        report("SKIP", "OpenCelliD", "OPENCELLID_API_KEY not set")
        return
    # A real public cell (Airtel, Patna area); any valid key gets a position or a "not found" reply.
    params = urllib.parse.urlencode({"key": key, "mcc": 404, "mnc": 10, "lac": 1025, "cellid": 11002, "format": "json"})
    try:
        data = http_json(f"https://opencellid.org/cell/get?{params}")
    except Exception as exc:
        report("FAIL", "OpenCelliD", str(exc))
        return
    err = str(data.get("error", "")).lower()
    if "token" in err or "key" in err or "invalid" in err:
        report("FAIL", "OpenCelliD", data.get("error"))
    elif "limit" in err:
        report("WARN", "OpenCelliD", "key valid but daily limit reached")
    else:
        report("OK", "OpenCelliD", "key accepted" + (" (test cell found)" if "lat" in data else ""))


def check_gemini(env: dict[str, str]) -> None:
    key, model = env.get("GEMINI_API_KEY", ""), env.get("GEMINI_MODEL", "gemini-3.8-flash")
    if not key:
        report("SKIP", "Gemini", "GEMINI_API_KEY not set - complaint summaries use the built-in template")
        return
    try:
        from google import genai

        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model=model, contents="Reply with the single word: ready")
        report("OK", "Gemini", f"{model} replied '{(resp.text or '').strip()[:40]}'")
    except ImportError:
        report("WARN", "Gemini", "google-genai not installed - run setup.bat")
    except Exception as exc:
        report("FAIL", "Gemini", str(exc)[:200])


def check_api(env: dict[str, str]) -> None:
    url = env.get("PUBLIC_API_URL", "").rstrip("/")
    if not url:
        return
    try:
        with urllib.request.urlopen(f"{url}/api/health", timeout=5) as resp:
            report("OK", "Backend reachable", f"{url} -> HTTP {resp.status}")
    except Exception:
        report("SKIP", "Backend reachable", f"{url} not answering (start run.bat to test)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--telegram-chat-id", action="store_true", help="list chat IDs that messaged the bot")
    parser.add_argument("--send-test", action="store_true", help="send a real Telegram message and test email")
    args = parser.parse_args()

    if not (ROOT / ".env").exists():
        print("No .env found - copy .env.example to .env (setup.bat does this).")
        return 1
    env = load_env()
    if args.telegram_chat_id:
        list_telegram_chats(env)
        return 0

    print("SignalScout configuration check\n")
    check_secret(env)
    check_ports(env)
    check_datasets()
    check_telegram(env, args.send_test)
    check_smtp(env, args.send_test)
    check_opencellid(env)
    check_gemini(env)
    check_api(env)
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    print(f"\n{len(failed)} problem(s) found." if failed else "\nAll configured checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
