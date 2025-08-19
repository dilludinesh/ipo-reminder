"""Test script for email functionality using SMTP."""
import logging
import os
from datetime import datetime
from ipo_reminder.emailer import send_email, format_html_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_send_email():
    """Test sending an email with both plain text and HTML content."""
    try:
        # Test data
        subject = "Test Email from IPO Reminder Bot (SMTP)"
        plain_text = "This is a test email sent from the IPO Reminder Bot using SMTP with App Password."
        
        # Create a simple HTML email
        test_ipos = [
            type('IPOTest', (), {
                'name': 'Test IPO 1',
                'open_date': '2023-01-01',
                'close_date': '2023-01-10',
                'price_band': '₹100 - ₹110',
                'lot_size': '100 shares',
                'issue_size': '₹1000 Cr',
                'recommendation': 'APPLY',
                'recommendation_reason': 'Strong fundamentals and positive market sentiment'
            })
        ]
        
        html_content = format_html_email(test_ipos, datetime.now().strftime('%Y-%m-%d'))
        
        # Send the email
        send_email(
            subject=subject,
            body=plain_text,
            html_body=html_content
        )
        
        logger.info("Test email sent successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return False

if __name__ == "__main__":
    if not all([os.getenv("OUTLOOK_EMAIL"), os.getenv("OUTLOOK_APP_PASSWORD")]):
        logger.error("Please set OUTLOOK_EMAIL and OUTLOOK_APP_PASSWORD environment variables")
    else:
        test_send_email()
