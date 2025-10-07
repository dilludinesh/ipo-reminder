"""Test email sending functionality."""
import os
import asyncio
from ipo_reminder.emailer import Emailer

async def test_email():
    """Test sending an email with the current configuration."""
    print("📧 Testing email configuration...")
    
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
        print(f"Sending test email to: {os.getenv('RECIPIENT_EMAIL')}")
        result = await emailer.send_email(
            subject=subject,
            body=html_content,  # Plain text version
            html_body=html_content,  # HTML version
            recipients=[os.getenv('RECIPIENT_EMAIL')]
        )
        if result:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email")
    except Exception as e:
        print(f"❌ Error sending test email: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())
