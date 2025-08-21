import logging
import datetime as dt
import sys
import os
from .sources.chittorgarh import today_ipos_closing, format_email
from .sources.fallback import get_fallback_ipos
from .emailer import send_email, format_html_email


def check_email_config():
    """Check if email configuration is available and provide helpful error message if not."""
    # Check for Microsoft Graph credentials
    has_graph = all([
        os.getenv('CLIENT_ID'),
        os.getenv('CLIENT_SECRET'), 
        os.getenv('TENANT_ID')
    ])
    
    # Check for SMTP credentials
    has_smtp = all([
        os.getenv('SENDER_EMAIL') or os.getenv('OUTLOOK_EMAIL'),
        os.getenv('SENDER_PASSWORD') or os.getenv('OUTLOOK_APP_PASSWORD')
    ])
    
    if not has_graph and not has_smtp:
        print("\n❌ No email configuration found!")
        print("\nTo make this work, you need either:")
        print("\n1. SMTP (Outlook) credentials:")
        print("   SENDER_EMAIL=your_outlook_email@example.com")
        print("   SENDER_PASSWORD=your_outlook_app_password")
        print("   RECIPIENT_EMAIL=recipient@example.com")
        print("\n2. OR Microsoft Graph API credentials:")
        print("   CLIENT_ID=your_azure_app_client_id")
        print("   CLIENT_SECRET=your_azure_app_client_secret") 
        print("   TENANT_ID=your_azure_tenant_id")
        print("   SENDER_EMAIL=your_outlook_email@example.com")
        print("   RECIPIENT_EMAIL=recipient@example.com")
        print("\n💡 Create a .env file in the repo root with these variables.")
        print("   See README.md for detailed setup instructions.")
        return False
    
    return True


def handler(dry_run=False):
    logger = logging.getLogger(__name__)
    logger.info("IPO Reminder Bot started.")
    
    if not check_email_config():
        sys.exit(1)
    
    # Use IST calendar date for "today"
    now_utc = dt.datetime.utcnow()
    # IST = UTC+5:30
    ist = now_utc + dt.timedelta(hours=5, minutes=30)
    today = ist.date()

    # Try primary source first
    ipos = today_ipos_closing(today)
    logger.info(f"Found {len(ipos)} IPO(s) closing today from primary source.")
    
    # If no IPOs found, try fallback sources
    if not ipos:
        logger.info("No IPOs found from primary source, trying fallback sources...")
        ipos = get_fallback_ipos(today)
        logger.info(f"Found {len(ipos)} IPO(s) closing today from fallback sources.")
    
    subject, body = format_email(today, ipos)
    html_body = format_html_email(ipos, today.strftime('%d %b %Y'))

    if dry_run:
        print(f"\n📧 DRY RUN - Would send email:")
        print(f"Subject: {subject}")
        print(f"Recipients: {os.getenv('RECIPIENT_EMAIL', 'Not configured')}")
        print(f"Body preview: {body[:200]}...")
        logger.info("DRY RUN completed - no email sent.")
    else:
        send_email(subject, body, html_body=html_body)
        logger.info("IPO Reminder Bot finished sending email.")

if __name__ == "__main__":
    # Support --dry-run flag for testing
    dry_run = "--dry-run" in sys.argv
    handler(dry_run=dry_run)
    handler()
