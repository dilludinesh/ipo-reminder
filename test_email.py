"""Test script for email functionality using Microsoft Graph API."""
import logging
import os
import sys
from datetime import datetime, timedelta
from ipo_reminder.emailer import send_email, format_html_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_send_email():
    """Test sending an email with both plain text and HTML content."""
    try:
        # Test data
        subject = "📈 Test Email from IPO Reminder Bot (Outlook)"
        plain_text = """
        This is a test email from the IPO Reminder Bot using Outlook SMTP.
        
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
        
        logger.info("Testing Outlook SMTP configuration...")
        logger.info(f"From: {os.getenv('SENDER_EMAIL')}")
        logger.info(f"To: {os.getenv('RECIPIENT_EMAIL')}")
        
        logger.info("Sending test email via Outlook SMTP...")
        
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
        logger.error("Please check the following:")
        logger.error("1. Your internet connection")
        logger.error("2. Outlook account settings (2FA must be enabled)")
        logger.error("3. App Password is correctly generated from Microsoft Account")
        logger.error("4. Sender email and password in .env are correct")
        return False

if __name__ == "__main__":
    required_vars = ["SENDER_EMAIL", "SENDER_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("\nPlease create a .env file with the following variables:")
        logger.info("""
# Email Configuration
SENDER_EMAIL=your_outlook_email@example.com
SENDER_PASSWORD=your_outlook_app_password_here  # Generate from: https://account.microsoft.com/security

# Optional: If different from sender email
RECIPIENT_EMAIL=recipient@example.com

# Web Scraping Configuration (optional)
REQUEST_TIMEOUT=30
REQUEST_RETRIES=3
REQUEST_DELAY=1.0
        """)
        sys.exit(1)
    
    logger.info("Starting Microsoft Graph API email test...")
    success = test_send_email()
    
    if success:
        logger.info("✅ Email test completed successfully!")
    else:
        logger.error("❌ Email test failed. Please check the error messages above.")
        sys.exit(1)
