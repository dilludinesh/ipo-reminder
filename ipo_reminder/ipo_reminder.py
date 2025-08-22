import logging
import datetime as dt
import sys
import os
from .config import check_email_config
from .sources.chittorgarh import today_ipos_closing, format_email
from .sources.fallback import get_fallback_ipos
from .emailer import send_email, format_html_email


def handler(dry_run=False):
    logger = logging.getLogger(__name__)
    logger.info("IPO Reminder Bot started.")
    
    if not check_email_config():
        sys.exit(1)
    
    # Use IST calendar date for "today"
    now_utc = dt.datetime.now(dt.timezone.utc)
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
