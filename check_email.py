"""Test script to verify email functionality."""
import asyncio
import os
import logging
from ipo_reminder.emailer import Emailer
from ipo_reminder.config import check_email_config

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_email():
    """Test sending an email with the current configuration."""
    # Check email configuration first
    try:
        check_email_config()
        logger.info("✅ Email configuration is valid")
    except Exception as e:
        logger.error(f"❌ Email configuration error: {e}")
        return False

    # Initialize emailer
    emailer = Emailer()
    
    # Test email content
    subject = "📈 IPO Reminder - Test Email"
    html_content = """
    <h2>IPO Reminder Test</h2>
    <p>This is a test email from the IPO Reminder system.</p>
    <p>If you're seeing this, the email configuration is working correctly!</p>
    """
    
    try:
        logger.info("Sending test email...")
        result = await emailer.send_email(
            subject=subject,
            html_content=html_content,
            recipient_email=os.getenv("RECIPIENT_EMAIL"),
            sender_name="IPO Reminder Test"
        )
        if result:
            logger.info("✅ Test email sent successfully!")
            # Check the email log
            if os.path.exists("logs/email.log"):
                with open("logs/email.log", "r") as f:
                    last_entry = f.readlines()[-1] if f.readlines() else "No entries"
                logger.info(f"📧 Last email log entry: {last_entry}")
            return True
        else:
            logger.error("❌ Failed to send test email (no exception raised, but send_email returned False)")
            return False
    except Exception as e:
        logger.error(f"❌ Error sending test email: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("📧 Testing email configuration...")
    print(f"Sender: {os.getenv('SENDER_EMAIL')}")
    print(f"Recipient: {os.getenv('RECIPIENT_EMAIL')}")
    print("-" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the test
    asyncio.run(test_email())
