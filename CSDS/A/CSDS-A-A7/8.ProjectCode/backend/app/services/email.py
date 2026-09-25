import smtplib
from email.mime.text import MIMEText

from .. import config


def send_email(to_address: str, subject: str, body: str) -> bool:
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD or not to_address:
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_ADDRESS
    msg["To"] = to_address
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.sendmail(config.GMAIL_ADDRESS, [to_address], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError):
        return False
