import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587

def send_email(subject: str, body: str):
    sender = os.environ.get("OUTLOOK_EMAIL")
    password = os.environ.get("OUTLOOK_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)

    if not sender or not password:
        raise RuntimeError("Missing OUTLOOK_EMAIL or OUTLOOK_APP_PASSWORD environment variables.")
    if not recipient:
        raise RuntimeError("Missing RECIPIENT_EMAIL environment variable.")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, [recipient], msg.as_string())
        server.quit()
