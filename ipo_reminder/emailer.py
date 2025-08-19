"""Email sending functionality for Outlook using Microsoft Graph API with OAuth2."""
import logging
import os
import json
import time
import requests
import msal
from typing import List, Optional
from .config import SENDER_EMAIL, RECIPIENT_EMAIL

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

def get_access_token():
    """Get an access token using client credentials flow."""
    try:
        # Create a confidential client application
        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY
        )

        # Try to get a token from cache
        result = app.acquire_token_silent(SCOPES, account=None)
        
        if not result:
            logger.info("No suitable token exists in cache. Getting a new one.")
            result = app.acquire_token_for_client(scopes=SCOPES)

        if "access_token" in result:
            return result["access_token"]
        else:
            error_msg = f"Could not acquire token: {result.get('error')} - {result.get('error_description')}"
            logger.error(error_msg)
            raise EmailError(error_msg)
            
    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(error_msg)
        raise EmailError(error_msg)

def send_email(
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    recipients: Optional[List[str]] = None,
    max_retries: int = 3,
    retry_delay: int = 5
) -> bool:
    """
    Send an email using Microsoft Graph API with OAuth2.
    
    Args:
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body (if not provided, plain text will be used)
        recipients: List of recipient email addresses (defaults to RECIPIENT_EMAIL from config)
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds (will be doubled after each retry)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not recipients:
        recipients = [RECIPIENT_EMAIL]
    
    # Prepare the email message
    email_msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if (html_body and html_body.strip()) else "Text",
                "content": html_body if (html_body and html_body.strip()) else body
            },
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in recipients],
            "from": {
                "emailAddress": {
                    "address": SENDER_EMAIL
                }
            }
        },
        "saveToSentItems": "true"
    }
    
    access_token = None
    for attempt in range(1, max_retries + 1):
        try:
            # Get a fresh access token for each attempt
            access_token = get_access_token()
            
            # Send the email using Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{GRAPH_ENDPOINT}/users/{SENDER_EMAIL}/sendMail",
                headers=headers,
                json=email_msg,
                timeout=30
            )
            
            # Check for rate limiting (HTTP 429)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', retry_delay))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue
                
            # Check for authentication errors
            if response.status_code == 401:
                logger.warning("Authentication expired. Refreshing token...")
                access_token = get_access_token()
                continue
                
            response.raise_for_status()
            logger.info(f"Email sent successfully to {', '.join(recipients)}")
            return True
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error sending email (attempt {attempt}/{max_retries}): {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f"\nResponse: {json.dumps(error_details, indent=2)}"
                except:
                    error_msg += f"\nResponse: {e.response.text}"
            
            logger.warning(error_msg)
            
            if attempt < max_retries:
                # Exponential backoff
                wait_time = retry_delay * (2 ** (attempt - 1))
                logger.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to send email after {max_retries} attempts")
                return False
    
    return False

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
