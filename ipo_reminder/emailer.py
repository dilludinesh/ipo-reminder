"""Email sending functionality using Microsoft Graph API with OAuth2 authentication."""
import logging
import json
import time
import requests
from typing import List, Optional
from msal import ConfidentialClientApplication
from .config import (
    SENDER_EMAIL, 
    CLIENT_ID,
    CLIENT_SECRET,
    TENANT_ID,
    RECIPIENT_EMAIL
)

logger = logging.getLogger(__name__)

# Microsoft Graph API endpoints
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPE = ['https://graph.microsoft.com/.default']
GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'

class EmailError(Exception):
    """Custom exception for email sending errors."""
    pass

def get_access_token() -> str:
    """Get an access token using client credentials flow."""
    try:
        app = ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY
        )
        
        result = app.acquire_token_for_client(scopes=SCOPE)
        
        if 'access_token' in result:
            return result['access_token']
        else:
            error_msg = f"Failed to get access token: {result.get('error')} - {result.get('error_description')}"
            logger.error(error_msg)
            raise EmailError(error_msg)
            
    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(error_msg)
        raise EmailError(error_msg)

def send_email(
    subject: str,
    body: str,
    recipients: Optional[List[str]] = None,
    html_body: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 5.0
) -> None:
    """
    Send an email using Microsoft Graph API with retry logic.

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
    
    # Prepare email message
    email_msg = {
        'message': {
            'subject': subject,
            'body': {
                'contentType': 'HTML' if html_body else 'Text',
                'content': html_body if html_body else body
            },
            'toRecipients': [{'emailAddress': {'address': recipient}} for recipient in recipients]
        },
        'saveToSentItems': 'true'
    }

    # Setup API request with retry logic
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            # Get access token
            access_token = get_access_token()
            
            # Send email using Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{GRAPH_ENDPOINT}/users/{SENDER_EMAIL}/sendMail',
                headers=headers,
                json=email_msg
            )
            
            if response.status_code == 202:  # 202 Accepted
                logger.info(f"Email sent successfully to {', '.join(recipients)}")
                return
            else:
                error_msg = f"Failed to send email. Status code: {response.status_code}, Response: {response.text}"
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {error_msg}")
                
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt}/{max_retries} failed to send email: {str(e)}")
        
        if attempt < max_retries:
            time.sleep(retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
    
    # If we get here, all attempts failed
    error_msg = f"Failed to send email after {max_retries} attempts"
    if last_exception:
        error_msg += f": {str(last_exception)}"
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
