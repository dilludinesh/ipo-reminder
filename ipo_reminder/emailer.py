"""Email sending functionality for IPO Reminder Bot."""
import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from .config import SMTP_HOST, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL

# Configure logging
logger = logging.getLogger(__name__)

class EmailError(Exception):
    """Custom exception for email-related errors."""
    pass

def send_email(
    subject: str,
    body: str,
    recipients: Optional[List[str]] = None,
    html_body: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 5.0
) -> None:
    """
    Send an email with the given subject and body.

    Args:
        subject: Email subject
        body: Plain text email body
        recipients: List of recipient email addresses (defaults to RECIPIENT_EMAIL from config)
        html_body: Optional HTML version of the email
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Raises:
        EmailError: If email sending fails after all retries
    """
    if not recipients:
        recipients = [RECIPIENT_EMAIL]

    # Create message container
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(recipients)

    # Attach parts
    part1 = MIMEText(body, 'plain')
    msg.attach(part1)

    if html_body:
        part2 = MIMEText(html_body, 'html')
        msg.attach(part2)

    # Attempt to send email with retries
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {', '.join(recipients)}")
                return
                
        except (smtplib.SMTPException, OSError) as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed to send email: {str(e)}"
            )
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    # If we get here, all retries failed
    error_msg = f"Failed to send email after {max_retries} attempts: {str(last_exception)}"
    logger.error(error_msg)
    raise EmailError(error_msg)

def format_html_email(ipos: list, now_date: str) -> str:
    """Format IPO information as an HTML email."""
    # This is a simplified version - you can enhance it further
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            .ipo-card {{ 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 15px; 
                margin-bottom: 15px;
                background-color: #f9f9f9;
            }}
            .ipo-name {{ font-size: 1.2em; font-weight: bold; color: #2980b9; }}
            .label {{ font-weight: bold; }}
            .recommendation {{ 
                font-weight: bold; 
                color: #27ae60; 
                margin-top: 10px;
                padding: 5px;
                background-color: #eafaf1;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>IPO Reminder for {now_date}</h1>
    """
    
    for ipo in ipos:
        html += f"""
        <div class="ipo-card">
            <div class="ipo-name">{ipo.name}</div>
            <div><span class="label">Open:</span> {ipo.open_date or 'N/A'}</div>
            <div><span class="label">Close:</span> {ipo.close_date or 'N/A'}</div>
            <div><span class="label">Price Band:</span> {ipo.price_band or 'N/A'}</div>
            <div><span class="label">Lot Size:</span> {ipo.lot_size or 'N/A'}</div>
            <div><span class="label">Issue Size:</span> {ipo.issue_size or 'N/A'}</div>
        """
        
        if hasattr(ipo, 'recommendation'):
            html += f"""
            <div class="recommendation">
                {ipo.recommendation} - {ipo.recommendation_reason}
            </div>
            """
            
        html += "</div>"  # Close ipo-card
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html
