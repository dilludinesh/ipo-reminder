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
    msg['From'] = sender
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
    """Format IPO information as an HTML email."""
    
    # Determine email theme based on content
    if not ipos:
        theme_color = "#27ae60"  # Green for all clear
        theme_emoji = "🌟"
        status_message = "All Clear Today!"
    else:
        apply_count = sum(1 for ipo in ipos if hasattr(ipo, 'recommendation') and 'APPLY' in str(getattr(ipo, 'recommendation', '') or ''))
        if apply_count > 0:
            theme_color = "#e74c3c"  # Red for urgent
            theme_emoji = "🚨"
            status_message = f"{apply_count} Hot IPO{'s' if apply_count > 1 else ''} Closing!"
        else:
            theme_color = "#3498db"  # Blue for informational
            theme_emoji = "📊"
            status_message = f"{len(ipos)} IPO{'s' if len(ipos) > 1 else ''} Closing Today"
    
    # Create engaging preheader text based on content
    if not ipos:
        preheader = "🏖️ No IPOs closing today - Enjoy your relaxed day!"
    else:
        apply_count = sum(1 for ipo in ipos if hasattr(ipo, 'recommendation') and 'APPLY' in str(getattr(ipo, 'recommendation', '') or ''))
        if apply_count > 0:
            company_names = [ipo.name for ipo in ipos if hasattr(ipo, 'recommendation') and 'APPLY' in str(getattr(ipo, 'recommendation', '') or '')][:2]
            if len(company_names) == 1:
                preheader = f"🔥 HOT: {company_names[0]} - Don't miss out!"
            else:
                preheader = f"🔥 {apply_count} HOT IPOs including {company_names[0]} - Act fast!"
        else:
            company_names = [ipo.name for ipo in ipos[:2]]
            if len(ipos) == 1:
                preheader = f"📊 {company_names[0]} closes today - Check details inside"
            else:
                preheader = f"📊 {len(ipos)} IPOs including {company_names[0]} close today"
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{theme_emoji} IPO Reminder - {now_date}</title>
        <!--[if !mso]><!-->
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <!--<![endif]-->
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                line-height: 1.6; 
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, {theme_color} 0%, {theme_color}aa 100%);
                color: white;
                padding: 30px;
                border-radius: 15px 15px 0 0;
                margin: -20px -20px 25px -20px;
            }}
            .header h1 {{ 
                margin: 0;
                font-size: 2.2em;
                font-weight: bold;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .header .subtitle {{
                font-size: 1.2em;
                margin-top: 10px;
                opacity: 0.9;
            }}
            .status-badge {{
                display: inline-block;
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                margin-top: 15px;
                font-weight: bold;
            }}
            .ipo-card {{ 
                border: 2px solid #f0f0f0;
                border-radius: 12px; 
                padding: 25px; 
                margin-bottom: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .ipo-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }}
            .ipo-name {{ 
                font-size: 1.5em; 
                font-weight: bold; 
                color: #2c3e50;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
            }}
            .ipo-emoji {{
                font-size: 1.2em;
                margin-right: 10px;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                padding: 8px 0;
                border-bottom: 1px solid #f0f0f0;
            }}
            .label {{ 
                font-weight: bold;
                color: #34495e;
                display: flex;
                align-items: center;
            }}
            .value {{
                color: #2c3e50;
                font-weight: 500;
            }}
            .recommendation {{ 
                font-weight: bold; 
                margin-top: 15px;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                font-size: 1.1em;
            }}
            .apply {{ background: linear-gradient(135deg, #27ae60, #2ecc71); color: white; }}
            .avoid {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }}
            .neutral {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; }}
            .no-ipos {{
                text-align: center;
                padding: 40px;
                color: #7f8c8d;
                font-size: 1.2em;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                color: #7f8c8d;
                font-size: 0.9em;
            }}
            .emoji {{ font-size: 1.2em; }}
        </style>
    </head>
    <body>
        <!-- Preheader text for email clients -->
        <div style="display: none; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #ffffff; mso-hide: all;">
            {preheader}
        </div>
        
        <div class="container">
            <div class="header">
                <h1>{theme_emoji} IPO REMINDER</h1>
                <div class="subtitle">{now_date}</div>
                <div class="status-badge">{status_message}</div>
            </div>
    """
    
    if not ipos:
        html += """
            <div class="no-ipos">
                <div style="font-size: 3em; margin-bottom: 20px;">🏖️</div>
                <div><strong>All Clear Today!</strong></div>
                <div>No IPOs are closing today. Time to relax or research upcoming opportunities!</div>
            </div>
        """
    else:
        for ipo in ipos:
            # Determine IPO emoji and recommendation class
            rec_text = ""
            rec_class = "neutral"
            ipo_emoji = "📈"
            
            if hasattr(ipo, 'recommendation') and ipo.recommendation:
                rec_text = f"{ipo.recommendation}"
                if hasattr(ipo, 'recommendation_reason'):
                    rec_text += f" - {ipo.recommendation_reason}"
                    
                if 'APPLY' in str(ipo.recommendation):
                    rec_class = "apply"
                    ipo_emoji = "🔥"
                elif 'AVOID' in str(ipo.recommendation):
                    rec_class = "avoid"
                    ipo_emoji = "⚠️"
            
            html += f"""
            <div class="ipo-card">
                <div class="ipo-name">
                    <span class="ipo-emoji">{ipo_emoji}</span>
                    {ipo.name}
                </div>
                
                <div class="detail-row">
                    <span class="label"><span class="emoji">💰</span> Price Band:</span>
                    <span class="value">{getattr(ipo, 'price_band', None) or 'Not specified'}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label"><span class="emoji">📦</span> Lot Size:</span>
                    <span class="value">{getattr(ipo, 'lot_size', None) or 'N/A'}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label"><span class="emoji">💼</span> Issue Size:</span>
                    <span class="value">{getattr(ipo, 'issue_size', None) or 'N/A'}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label"><span class="emoji">📅</span> Open Date:</span>
                    <span class="value">{getattr(ipo, 'open_date', None) or 'N/A'}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label"><span class="emoji">⏰</span> Close Date:</span>
                    <span class="value">{getattr(ipo, 'close_date', None) or 'N/A'}</span>
                </div>
            """
            
            if hasattr(ipo, 'gmp_latest') and ipo.gmp_latest:
                html += f"""
                <div class="detail-row">
                    <span class="label"><span class="emoji">📊</span> GMP:</span>
                    <span class="value">{ipo.gmp_latest} ({getattr(ipo, 'gmp_trend', 'unknown')})</span>
                </div>
                """
            
            if hasattr(ipo, 'expert_recommendation') and ipo.expert_recommendation:
                html += f"""
                <div class="detail-row">
                    <span class="label"><span class="emoji">👨‍💼</span> Expert View:</span>
                    <span class="value">{ipo.expert_recommendation}</span>
                </div>
                """
            
            if rec_text:
                html += f"""
                <div class="recommendation {rec_class}">
                    🤖 Bot Suggestion: {rec_text}
                </div>
                """
            
            # Add links if available
            links_html = ""
            if hasattr(ipo, 'detail_url') and ipo.detail_url:
                links_html += f'<a href="{ipo.detail_url}" style="color: #3498db; text-decoration: none; margin-right: 15px;">📄 Details</a>'
            if hasattr(ipo, 'gmp_url') and ipo.gmp_url:
                links_html += f'<a href="{ipo.gmp_url}" style="color: #3498db; text-decoration: none;">📊 GMP Page</a>'
                
            if links_html:
                html += f"""
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ecf0f1; text-align: center;">
                    {links_html}
                </div>
                """

            html += "</div>"

    html += """
            <div class="footer">
                <div><strong>⚠️ DISCLAIMER:</strong> Suggestions are informational, not financial advice.</div>
                <div style="margin-top: 10px;">🤖 <strong>IPO Reminder Bot</strong> • Keeping you informed daily!</div>
            </div>
        </div>
    </body>
    </html>
    """

    return html
