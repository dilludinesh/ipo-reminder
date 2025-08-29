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
    """Custom exception for email sending errors."""
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
    msg['From'] = f"IPO Reminder 📈 <{sender}>"
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


def format_html_email(ipos: list, now_date: str) -> str:
    """Format IPO information as a simple HTML email."""
    
    # Create simple preheader text based on content
    if not ipos:
        preheader = "No IPOs closing today - All clear!"
    else:
        apply_count = sum(1 for ipo in ipos if hasattr(ipo, 'recommendation') and 'APPLY' in str(getattr(ipo, 'recommendation', '') or ''))
        if apply_count > 0:
            preheader = f"{apply_count} IPO recommendation(s) closing today!"
        else:
            preheader = f"{len(ipos)} IPO(s) closing today - Check details"

    # Start HTML content
    html_parts = [
        f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IPO Reminder - {now_date}</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
        /* Reset styles */
        body, table, td, p, a, span {{ margin: 0; padding: 0; border: 0; font-size: 100%; font: inherit; vertical-align: baseline; }}
        table {{ border-collapse: collapse; border-spacing: 0; }}
        
        /* Base styles */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .date {{
            font-size: 16px;
            opacity: 0.9;
            margin-top: 8px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .no-ipos {{
            text-align: center;
            padding: 40px 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .no-ipos-icon {{
            font-size: 48px;
            margin-bottom: 20px;
        }}
        
        .no-ipos h2 {{
            color: #28a745;
            margin: 0 0 15px 0;
            font-size: 24px;
            font-weight: 600;
        }}
        
        .no-ipos p {{
            color: #6c757d;
            font-size: 16px;
            margin: 0;
        }}
        
        .ipo-card {{
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .ipo-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .ipo-header {{
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .ipo-title {{
            font-size: 20px;
            font-weight: 700;
            color: #2c3e50;
            margin: 0 0 8px 0;
        }}
        
        .ipo-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 14px;
            color: #6c757d;
        }}
        
        .ipo-body {{
            padding: 20px;
        }}
        
        .price-band {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }}
        
        .price-band strong {{
            color: #495057;
        }}
        
        .recommendation {{
            padding: 12px 18px;
            border-radius: 25px;
            font-weight: 600;
            text-align: center;
            margin: 15px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .rec-apply {{
            background-color: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }}
        
        .rec-avoid {{
            background-color: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
        }}
        
        .rec-neutral {{
            background-color: #fff3cd;
            color: #856404;
            border: 2px solid #ffeaa7;
        }}
        
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e9ecef;
            font-size: 12px;
            color: #6c757d;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        /* Responsive design */
        @media only screen and (max-width: 600px) {{
            .email-container {{ width: 100% !important; margin: 0 !important; }}
            .header {{ padding: 20px 15px !important; }}
            .header h1 {{ font-size: 24px !important; }}
            .content {{ padding: 20px 15px !important; }}
            .ipo-meta {{ flex-direction: column; gap: 8px; }}
        }}
    </style>
</head>
<body>
    <div style="display: none; font-size: 1px; color: #ffffff; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
        {preheader}
    </div>
    
    <div class="email-container">
        <div class="header">
            <h1>🏦 IPO Reminder</h1>
            <div class="date">{now_date}</div>
        </div>
        
        <div class="content">'''
    ]

    if not ipos:
        html_parts.append('''
            <div class="no-ipos">
                <div class="no-ipos-icon">✅</div>
                <h2>All Clear!</h2>
                <p>No IPOs are closing today. Enjoy your day! 😊</p>
            </div>''')
    else:
        html_parts.append(f'''
            <h2 style="color: #2c3e50; margin: 0 0 25px 0; font-size: 22px; font-weight: 600;">
                📊 {len(ipos)} IPO{"s" if len(ipos) != 1 else ""} Closing Today
            </h2>''')
        
        for ipo in ipos:
            # Safely get attributes
            name = getattr(ipo, 'name', 'Unknown IPO')
            price_band = getattr(ipo, 'price_band', 'Price not available')
            lot_size = getattr(ipo, 'lot_size', 'Not specified')
            listing_date = getattr(ipo, 'listing_date', 'TBA')
            recommendation = getattr(ipo, 'recommendation', None)
            
            # Format recommendation
            if recommendation:
                rec_text = str(recommendation).upper()
                if 'APPLY' in rec_text:
                    rec_class = 'rec-apply'
                    rec_icon = '✅'
                elif 'AVOID' in rec_text:
                    rec_class = 'rec-avoid'
                    rec_icon = '❌'
                else:
                    rec_class = 'rec-neutral'
                    rec_icon = '⚠️'
                rec_html = f'<div class="recommendation {rec_class}">{rec_icon} {recommendation}</div>'
            else:
                rec_html = ''
            
            html_parts.append(f'''
            <div class="ipo-card">
                <div class="ipo-header">
                    <div class="ipo-title">{name}</div>
                    <div class="ipo-meta">
                        <span>💰 Price: {price_band}</span>
                        <span>📦 Lot: {lot_size}</span>
                        <span>📅 Listing: {listing_date}</span>
                    </div>
                </div>
                <div class="ipo-body">
                    <div class="price-band">
                        <strong>Price Band:</strong> {price_band}
                    </div>
                    {rec_html}
                </div>
            </div>''')
    
    html_parts.append('''
        </div>
        
        <div class="footer">
            <p>💡 <strong>IPO Reminder</strong> • Automated daily notifications</p>
            <p style="margin-top: 10px;">
                Get timely updates on IPO closing dates • 
                <a href="#">Manage preferences</a>
            </p>
        </div>
    </div>
</body>
</html>''')
    
    return ''.join(html_parts)
