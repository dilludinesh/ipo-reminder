"""Test script for email functionality using SMTP with App Password."""
import logging
import os
import time
from datetime import datetime, timedelta
from ipo_reminder.emailer import send_email, format_html_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_send_email():
    """Test sending an email with both plain text and HTML content."""
    try:
        # Test data
        subject = "📈 Test Email from IPO Reminder Bot"
        plain_text = """
        This is a test email from the IPO Reminder Bot.
        
        If you can read this, the email sending functionality is working correctly!
        """
        
        # Create a simple HTML email
        test_ipos = [
            type('IPOTest', (), {
                'name': 'Example IPO',
                'open_date': (datetime.now().strftime('%Y-%m-%d')),
                'close_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'price_band': '₹100 - ₹120',
                'lot_size': '50 shares',
                'issue_size': '₹500 Cr',
                'recommendation': 'APPLY',
                'recommendation_reason': 'Strong fundamentals and positive market sentiment'
            })
        ]
        
        html_content = format_html_email(test_ipos, datetime.now().strftime('%Y-%m-%d'))
        
        logger.info("Sending test email...")
        
        # Send the email
        send_email(
            subject=subject,
            body=plain_text,
            html_body=html_content
        )
        
        logger.info("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send test email: {str(e)}")
        return False

if __name__ == "__main__":
    required_vars = ["OUTLOOK_EMAIL", "OUTLOOK_APP_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("\nPlease create a .env file with the following variables:")
        logger.info("""
OUTLOOK_EMAIL=your_email@example.com
OUTLOOK_APP_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@example.com  # Optional, defaults to OUTLOOK_EMAIL
SMTP_SERVER=smtp.office365.com  # Default for Outlook
SMTP_PORT=587  # Default for STARTTLS
        """)
    else:
        test_send_email()
