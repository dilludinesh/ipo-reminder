import datetime as dt
from .sources.chittorgarh import today_ipos_closing, format_email
from .emailer import send_email

def handler():
    # Use IST calendar date for "today"
    now_utc = dt.datetime.utcnow()
    # IST = UTC+5:30
    ist = now_utc + dt.timedelta(hours=5, minutes=30)
    today = ist.date()

    ipos = today_ipos_closing(today)
    subject, body = format_email(today, ipos)
    send_email(subject, body)

if __name__ == "__main__":
    handler()
