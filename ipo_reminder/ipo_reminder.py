import logging
import datetime as dt
import sys
import os
from .config import check_email_config
from .sources.chittorgarh import today_ipos_closing
from .sources.official import get_official_ipos
from .sources.moneycontrol import get_moneycontrol_ipos
from .sources.fallback import get_fallback_ipos
from .sources.zerodha import get_zerodha_ipos_closing_today
from .ipo_categorizer import format_personal_guide_email
from .emailer import send_email


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
    logger.info(f"Checking for IPOs closing on {today} (IST)")

    # Try Zerodha first (most up-to-date and reliable for current IPOs)
    zerodha_ipos = get_zerodha_ipos_closing_today(today)
    logger.info(f"Found {len(zerodha_ipos)} IPO(s) closing today from Zerodha.")
    
    # Convert Zerodha IPOs to standard format
    ipos = []
    for z_ipo in zerodha_ipos:
        try:
            # Convert to IPOInfo format for email
            from .sources.chittorgarh import IPOInfo
            ipo = IPOInfo(
                name=z_ipo.name,
                detail_url=None,
                gmp_url=None,
                open_date=z_ipo.open_date,
                close_date=z_ipo.close_date,
                price_band=z_ipo.price_range,
                lot_size=None,
                recommendation=f"IPO closes today - Listing on {z_ipo.listing_date}"
            )
            ipos.append(ipo)
        except Exception as e:
            logger.warning(f"Error converting Zerodha IPO {z_ipo.name}: {e}")
            continue

    # If no IPOs found from Zerodha, try official sources (SEBI, BSE, NSE)
    if not ipos:
        logger.info("No IPOs found from Zerodha, trying official sources...")
        try:
            ipos = get_official_ipos(today)
            logger.info(f"Found {len(ipos)} IPO(s) closing today from official sources.")
        except Exception as e:
            logger.warning(f"Error fetching from official sources: {e}")
            ipos = []
    
    # If no IPOs found, try Moneycontrol (reliable financial portal)
    if not ipos:
        logger.info("No IPOs found from official sources, trying Moneycontrol...")
        try:
            ipos = get_moneycontrol_ipos(today)
            logger.info(f"Found {len(ipos)} IPO(s) closing today from Moneycontrol.")
        except Exception as e:
            logger.warning(f"Error fetching from Moneycontrol: {e}")
            ipos = []
    
    # If still no IPOs, try Chittorgarh as backup
    if not ipos:
        logger.info("No IPOs found from Moneycontrol, trying Chittorgarh...")
        try:
            ipos = today_ipos_closing(today)
            logger.info(f"Found {len(ipos)} IPO(s) closing today from Chittorgarh.")
        except Exception as e:
            logger.warning(f"Error fetching from Chittorgarh: {e}")
            ipos = []
    
    # If still no IPOs, try other fallback sources
    if not ipos:
        logger.info("No IPOs found from Chittorgarh, trying other fallback sources...")
        try:
            ipos = get_fallback_ipos(today)
            logger.info(f"Found {len(ipos)} IPO(s) closing today from fallback sources.")
        except Exception as e:
            logger.warning(f"Error fetching from fallback sources: {e}")
            ipos = []
    
    subject, body = format_personal_guide_email(today, ipos)
    # No HTML - just simple plain text email
    
    if dry_run:
        print(f"\n📧 DRY RUN - Would send email:")
        print(f"Subject: {subject}")
        print(f"Recipients: {os.getenv('RECIPIENT_EMAIL', 'Not configured')}")
        print(f"Body preview: {body[:200]}...")
        logger.info("DRY RUN completed - no email sent.")
    else:
        try:
            send_email(subject, body, html_body=None)  # No HTML
            logger.info("IPO Reminder finished sending email.")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            sys.exit(1)

if __name__ == "__main__":
    # Support --dry-run flag for testing
    dry_run = "--dry-run" in sys.argv
    handler(dry_run=dry_run)
