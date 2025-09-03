"""Simple email sending functionality using SMTP with enhanced security."""
import logging
import os
import smtplib
import html
import re
from datetime import datetime
from email.message import EmailMessage
from typing import List, Optional
from email.utils import formataddr

from ipo_reminder.config import SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL, validate_email_config

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Custom exception for email-related errors."""
    pass


def _sanitize_text(text: str) -> str:
    """Sanitize text input to prevent injection attacks."""
    if not text:
        return ""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>]', '', str(text))
    return html.escape(sanitized)


def _sanitize_html(html_content: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    if not html_content:
        return ""
    # Basic HTML sanitization - remove script tags and dangerous attributes
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<[^>]*on\w+[^>]*>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<[^>]*javascript:[^>]*>', '', html_content, flags=re.IGNORECASE)
    return html_content


def _validate_email_address(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def _append_email_log(status: str, recipient: str, subject: str, detail: str = "") -> None:
    """Append email attempt to log file with timestamp and sanitization."""
    try:
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.utcnow().isoformat() + "Z"
        # Sanitize log data
        safe_recipient = _sanitize_text(recipient)
        safe_subject = _sanitize_text(subject)
        safe_detail = _sanitize_text(detail)
        log_entry = f"{timestamp}\t{status}\t{safe_recipient}\t{safe_subject}\t{safe_detail}\n"
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
    """Send an email using SMTP with enhanced security validation."""
    # Validate and sanitize inputs
    if not subject or not body:
        logger.error("Subject and body are required")
        return False

    subject = _sanitize_text(subject)
    body = _sanitize_text(body)

    if html_body:
        html_body = _sanitize_html(html_body)

    if not recipients:
        recipients = [RECIPIENT_EMAIL]

    # Validate all recipients
    valid_recipients = []
    for recipient in recipients:
        if _validate_email_address(recipient):
            valid_recipients.append(recipient)
        else:
            logger.warning(f"Invalid email address: {recipient}")

    if not valid_recipients:
        logger.error("No valid recipients found")
        return False

    sender = os.getenv('SENDER_EMAIL') or SENDER_EMAIL
    password = os.getenv('SENDER_PASSWORD') or SENDER_PASSWORD

    if not sender or not password:
        logger.error("SMTP configured but SENDER_EMAIL or SENDER_PASSWORD is missing")
        return False

    if not _validate_email_address(sender):
        logger.error(f"Invalid sender email address: {sender}")
        return False

    # Provider-specific SMTP settings with validation
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
    # Set friendly display name for the sender with validation
    msg['From'] = formataddr(("IPO Reminder", sender))
    msg['To'] = ', '.join(valid_recipients)

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
        logger.info(f"Email sent via SMTP to {', '.join(valid_recipients)}")
        _append_email_log("SMTP_SENT", valid_recipients[0], subject)
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        _append_email_log("SMTP_AUTH_FAILED", valid_recipients[0], subject, str(e))
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection failed: {e}")
        _append_email_log("SMTP_CONNECT_FAILED", valid_recipients[0], subject, str(e))
        return False
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        _append_email_log("SMTP_FAILED", valid_recipients[0], subject, str(e))
        return False


class Emailer:
    """Email service class for sending IPO reminder emails."""

    def __init__(self):
        """Initialize the emailer."""
        pass

    async def send_email(
        self,
        subject: str,
        html_content: str,
        recipient_email: Optional[str] = None,
        sender_name: str = "IPO Reminder Service"
    ) -> bool:
        """
        Send an email asynchronously.

        Args:
            subject: Email subject
            html_content: HTML content of the email
            recipient_email: Recipient email address (optional, uses config default)
            sender_name: Sender name (default: IPO Reminder Service)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Call the existing send_email function
            return send_email(
                subject=subject,
                html_content=html_content,
                recipient_email=recipient_email,
                sender_name=sender_name
            )
        except Exception as e:
            logger.error(f"Emailer.send_email failed: {e}")
            return False
