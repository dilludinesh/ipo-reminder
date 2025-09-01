"""Simple email sending functionality using SMTP."""
import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import List, Optional

from .config import SENDER_EMAIL, RECIPIENT_EMAIL, validate_email_config

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Custom exception for email-related errors."""
    pass


def _append_email_log(status: str, recipient: str, subject: str, detail: str = "") -> None:
    """Append email attempt to log file with timestamp."""
    try:
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = f"{timestamp}\t{status}\t{recipient}\t{subject}\t{detail}\n"
        with open("logs/email.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        logger.warning(f"Failed to write email log: {e}")


def send_email(
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    recipients: Optional[List[str]] = None,
) -> bool:
    """Send an email using SMTP."""
    if not recipients:
        recipients = [RECIPIENT_EMAIL]

    sender = os.getenv('SENDER_EMAIL') or SENDER_EMAIL
    password = os.getenv('SENDER_PASSWORD')

    if not sender or not password:
        logger.error("SMTP configured but SENDER_EMAIL or SENDER_PASSWORD is missing")
        return False

    # Provider-specific SMTP settings
    sender_domain = sender.split('@')[1].lower() if '@' in sender else ''
    
    if sender_domain in ['gmail.com', 'googlemail.com']:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        logger.info("Using Gmail SMTP settings")
    elif sender_domain in ['outlook.com', 'hotmail.com', 'live.com']:
        smtp_server = 'smtp-mail.outlook.com'
        smtp_port = 587
        logger.info("Using Outlook SMTP settings")
    elif sender_domain in ['yahoo.com', 'ymail.com']:
        smtp_server = 'smtp.mail.yahoo.com'
        smtp_port = 587
        logger.info("Using Yahoo SMTP settings")
    else:
        # Use custom settings or defaults
        smtp_server = os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        logger.info(f"Using custom SMTP settings: {smtp_server}:{smtp_port}")

    msg = EmailMessage()
    msg['Subject'] = subject
    # Set friendly display name for the sender
    msg['From'] = f"IPO Reminder <{sender}>"
    msg['To'] = ', '.join(recipients)
    if html_body and html_body.strip():
        msg.set_content(body)
        msg.add_alternative(html_body, subtype='html')
    else:
        msg.set_content(body)

    try:
        validate_email_config()
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(sender, password)
            s.send_message(msg)
        logger.info(f"Email sent via SMTP to {', '.join(recipients)}")
        _append_email_log("SMTP_SENT", recipients[0], subject)
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        _append_email_log("SMTP_FAILED", recipients[0], subject, str(e))
        return False
