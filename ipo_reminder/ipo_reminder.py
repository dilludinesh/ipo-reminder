import logging
import datetime as dt
import sys
import os
from .config import check_email_config
from .sources.chittorgarh import today_ipos_closing, format_email
from .sources.official import get_official_ipos
from .sources.moneycontrol import get_moneycontrol_ipos
from .sources.fallback import get_fallback_ipos
from .emailer import send_email, format_html_email


def handler(dry_run=False):
    logger = logging.getLogger(__name__)
    logger.info("IPO Reminder started.")
    
    if not check_email_config():
        sys.exit(1)
    
    # Use IST calendar date for "today"
    now_utc = dt.datetime.now(dt.timezone.utc)
    # IST = UTC+5:30
    ist = now_utc + dt.timedelta(hours=5, minutes=30)
    today = ist.date()

    # Try official sources first (SEBI, BSE, NSE) - most authoritative
    ipos = get_official_ipos(today)
    logger.info(f"Found {len(ipos)} IPO(s) closing today from official sources.")
    
    # If no IPOs found, try Moneycontrol (reliable financial portal)
    if not ipos:
        logger.info("No IPOs found from official sources, trying Moneycontrol...")
        ipos = get_moneycontrol_ipos(today)
        logger.info(f"Found {len(ipos)} IPO(s) closing today from Moneycontrol.")
    
    # If still no IPOs, try Chittorgarh as backup
    if not ipos:
        logger.info("No IPOs found from Moneycontrol, trying Chittorgarh...")
        ipos = today_ipos_closing(today)
        logger.info(f"Found {len(ipos)} IPO(s) closing today from Chittorgarh.")
    
    # If still no IPOs, try other fallback sources
    if not ipos:
        logger.info("No IPOs found from Chittorgarh, trying other fallback sources...")
        ipos = get_fallback_ipos(today)
        logger.info(f"Found {len(ipos)} IPO(s) closing today from fallback sources.")
    
    subject, body = format_email(today, ipos)
    # No HTML - just simple plain text email
    
    if dry_run:
        print(f"\n📧 DRY RUN - Would send email:")
        print(f"Subject: {subject}")
        print(f"Recipients: {os.getenv('RECIPIENT_EMAIL', 'Not configured')}")
        print(f"Body preview: {body[:200]}...")
        logger.info("DRY RUN completed - no email sent.")
    else:
        send_email(subject, body, html_body=None)  # No HTML
        logger.info("IPO Reminder finished sending email.")

if __name__ == "__main__":
    # Support --dry-run flag for testing
    dry_run = "--dry-run" in sys.argv
    handler(dry_run=dry_run)
