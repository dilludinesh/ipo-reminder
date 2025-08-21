
import logging
import datetime as dt
from .sources.chittorgarh import today_ipos_closing, format_email
from .emailer import send_email, format_html_email


def handler():
    logger = logging.getLogger(__name__)
    logger.info("IPO Reminder Bot started.")
    # Use IST calendar date for "today"
    now_utc = dt.datetime.utcnow()
    # IST = UTC+5:30
    ist = now_utc + dt.timedelta(hours=5, minutes=30)
    today = ist.date()

    ipos = today_ipos_closing(today)
    logger.info(f"Found {len(ipos)} IPO(s) closing today.")
    subject, body = format_email(today, ipos)
    html_body = format_html_email(ipos, today.strftime('%d %b %Y'))

    send_email(subject, body, html_body=html_body)
    logger.info("IPO Reminder Bot finished sending email.")

if __name__ == "__main__":
    handler()
