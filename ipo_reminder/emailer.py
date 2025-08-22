"""Email sending functionality for Outlook using Microsoft Graph API with OAuth2."""
import logging
import os
import json
import time
from typing import List, Optional

import requests
import msal
import smtplib
from email.message import EmailMessage

from .config import SENDER_EMAIL, RECIPIENT_EMAIL, validate_email_config

# Microsoft Graph API Configuration
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID', 'common')
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]
GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Custom exception for email sending errors."""
    pass


def get_access_token() -> str:
    """Get an access token using client credentials flow."""
    try:
        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY,
        )

        result = app.acquire_token_silent(SCOPES, account=None)
        if not result:
            logger.info("No suitable token exists in cache. Getting a new one.")
            result = app.acquire_token_for_client(scopes=SCOPES)

        if result and "access_token" in result:
            return result["access_token"]

        error_msg = f"Could not acquire token: {result.get('error')} - {result.get('error_description')}"
        logger.error(error_msg)
        raise EmailError(error_msg)

    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(error_msg)
        raise EmailError(error_msg)


def _send_via_smtp(subject: str, body: str, html_body: Optional[str], recipients: List[str]) -> bool:
    """Send email using SMTP (Outlook/Office365) as fallback."""
    smtp_server = os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender = os.getenv('SENDER_EMAIL')
    password = os.getenv('SENDER_PASSWORD')

    if not sender or not password:
        logger.error("SMTP fallback configured but SENDER_EMAIL or SENDER_PASSWORD is missing")
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    # Set friendly display name for the sender
    msg['From'] = f"IPO Reminder Bot 🤖 <{sender}>"
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
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return False


def send_email(
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    recipients: Optional[List[str]] = None,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> bool:
    """Send an email using Microsoft Graph API with OAuth2. Falls back to SMTP if Graph credentials are missing."""
    if not recipients:
        recipients = [RECIPIENT_EMAIL]

    # Check if sender email is a personal account
    sender_domain = SENDER_EMAIL.split('@')[1] if '@' in SENDER_EMAIL else ''
    is_personal_account = sender_domain.lower() in ['live.com', 'hotmail.com', 'outlook.com', 'gmail.com']
    
    # For personal accounts, try SMTP first since Graph API application permissions don't work well
    if is_personal_account:
        logger.info("Personal account detected, trying SMTP first")
        if _send_via_smtp(subject, body, html_body, recipients):
            return True
        logger.warning("SMTP failed for personal account, trying Graph API anyway")

    email_msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if (html_body and html_body.strip()) else "Text",
                "content": html_body if (html_body and html_body.strip()) else body,
            },
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in recipients],
            "from": {
                "emailAddress": {
                    "address": SENDER_EMAIL,
                    "name": "IPO Reminder Bot 🤖"
                }
            }
        },
        "saveToSentItems": "true",
    }

    if CLIENT_ID and CLIENT_SECRET:
        for attempt in range(1, max_retries + 1):
            try:
                access_token = get_access_token()
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                }

                response = requests.post(
                    f"{GRAPH_ENDPOINT}/users/{SENDER_EMAIL}/sendMail",
                    headers=headers,
                    json=email_msg,
                    timeout=30,
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                if response.status_code == 401:
                    logger.warning("Authentication expired. Refreshing token...")
                    continue

                response.raise_for_status()
                logger.info(f"Email sent successfully to {', '.join(recipients)} via Microsoft Graph")
                return True

            except requests.exceptions.RequestException as e:
                error_msg = f"Error sending email (attempt {attempt}/{max_retries}): {str(e)}"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_details = e.response.json()
                        error_msg += f"\nResponse: {json.dumps(error_details, indent=2)}"
                    except Exception:
                        error_msg += f"\nResponse: {e.response.text}"

                logger.warning(error_msg)

                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to send email after {max_retries} attempts using Graph API")
                    # Try SMTP fallback as final attempt
                    logger.info("Trying SMTP fallback after Graph API failure")
                    return _send_via_smtp(subject, body, html_body, recipients)

        return False

    logger.info("Graph credentials not found; using SMTP fallback")
    return _send_via_smtp(subject, body, html_body, recipients)


def format_html_email(ipos: list, now_date: str) -> str:
    """Format IPO information as a simple HTML email."""
    
    # Create simple preheader text based on content
    if not ipos:
        preheader = "No IPOs closing today - All clear!"
    else:
        apply_count = sum(1 for ipo in ipos if hasattr(ipo, 'recommendation') and 'APPLY' in str(getattr(ipo, 'recommendation', '') or ''))
        if apply_count > 0:
            company_names = [ipo.name for ipo in ipos if hasattr(ipo, 'recommendation') and 'APPLY' in str(getattr(ipo, 'recommendation', '') or '')][:1]
            if company_names:
                preheader = f"HOT: {company_names[0]} - Don't miss out!"
            else:
                preheader = f"{apply_count} hot IPOs closing today"
        else:
            company_names = [ipo.name for ipo in ipos[:1]]
            if len(ipos) == 1:
                preheader = f"{company_names[0]} closes today"
            else:
                preheader = f"{len(ipos)} IPOs closing today"
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IPO Reminder - {now_date}</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px;
                background: white;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .header h1 {{ 
                margin: 0;
                color: #333;
                font-size: 1.5em;
            }}
            .ipo-item {{ 
                border: 1px solid #ddd;
                border-radius: 5px; 
                padding: 15px; 
                margin-bottom: 15px;
                background-color: #fafafa;
            }}
            .ipo-name {{ 
                font-size: 1.1em; 
                font-weight: bold; 
                color: #333;
                margin-bottom: 10px;
            }}
            .detail {{ 
                margin-bottom: 5px;
            }}
            .label {{ 
                font-weight: bold;
                color: #666;
            }}
            .recommendation {{ 
                font-weight: bold; 
                margin-top: 10px;
                padding: 10px;
                background-color: #e9ecef;
                border-radius: 3px;
            }}
            .no-ipos {{
                text-align: center;
                padding: 30px;
                color: #666;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
                color: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <!-- Preheader text for email clients -->
        <div style="display: none; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #ffffff; mso-hide: all;">
            {preheader}
        </div>
        
        <div class="container">
            <div class="header">
                <h1>IPO Reminder for {now_date}</h1>
            </div>
    """
    
    if not ipos:
        html += """
            <div class="no-ipos">
                <div><strong>All Clear Today!</strong></div>
                <div>No IPOs are closing today.</div>
            </div>
        """
    else:
        html += f"<p>Hello Dinesh,</p><p>{len(ipos)} IPO{'s' if len(ipos) > 1 else ''} closing today:</p>"
        
        for ipo in ipos:
            # Get recommendation
            rec_text = ""
            if hasattr(ipo, 'recommendation') and ipo.recommendation:
                rec_text = f"{ipo.recommendation}"
                if hasattr(ipo, 'recommendation_reason'):
                    rec_text += f" - {ipo.recommendation_reason}"
            
            html += f"""
            <div class="ipo-item">
                <div class="ipo-name">{ipo.name}</div>
                
                <div class="detail">
                    <span class="label">Price Band:</span> {getattr(ipo, 'price_band', None) or 'Not specified'}
                </div>
                
                <div class="detail">
                    <span class="label">Lot Size:</span> {getattr(ipo, 'lot_size', None) or 'N/A'}
                </div>
                
                <div class="detail">
                    <span class="label">Issue Size:</span> {getattr(ipo, 'issue_size', None) or 'N/A'}
                </div>
                
                <div class="detail">
                    <span class="label">Close Date:</span> {getattr(ipo, 'close_date', None) or 'N/A'}
                </div>
            """
            
            if hasattr(ipo, 'gmp_latest') and ipo.gmp_latest:
                html += f"""
                <div class="detail">
                    <span class="label">GMP:</span> {ipo.gmp_latest} ({getattr(ipo, 'gmp_trend', 'unknown')})
                </div>
                """
            
            if hasattr(ipo, 'expert_recommendation') and ipo.expert_recommendation:
                html += f"""
                <div class="detail">
                    <span class="label">Expert View:</span> {ipo.expert_recommendation}
                </div>
                """
            
            if rec_text:
                html += f"""
                <div class="recommendation">
                    Recommendation: {rec_text}
                </div>
                """
            
            # Add links if available
            if hasattr(ipo, 'detail_url') and ipo.detail_url:
                html += f"""
                <div style="margin-top: 10px;">
                    <a href="{ipo.detail_url}" style="color: #007bff; text-decoration: none;">View Details</a>
                </div>
                """

            html += "</div>"

    html += """
            <div class="footer">
                <div><strong>Disclaimer:</strong> Suggestions are informational, not financial advice.</div>
                <div style="margin-top: 5px;"><strong>IPO Reminder Bot</strong></div>
            </div>
        </div>
    </body>
    </html>
    """

    return html
