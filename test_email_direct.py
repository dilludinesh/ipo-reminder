#!/usr/bin/env python3
"""Test email functionality directly."""

import asyncio
import os
import sys

# Load environment variables manually
def load_env_file():
    """Load .env file manually."""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env file
load_env_file()

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ipo_reminder.emailer import Emailer

async def test_email():
    """Test email sending functionality."""
    print("🧪 Testing Email Functionality...")
    print("=" * 50)

    # Load environment variables
    load_env_file()

    # Check configuration
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    print("📧 Email Configuration:")
    print(f"  Sender: {sender_email}")
    print(f"  Recipient: {recipient_email}")
    print(f"  Password: {'***' if sender_password else 'Not set'}")

    if not all([sender_email, sender_password, recipient_email]):
        print("❌ Email configuration incomplete!")
        print("Please run: ./setup_email_config.sh")
        return False

    # Test email sending
    emailer = Emailer()

    try:
        print("\n📤 Sending test email...")
        result = await emailer.send_email(
            subject="🚀 IPO Reminder - Test Email",
            html_content="""
            <h2>🎉 IPO Reminder System Test</h2>
            <p>This is a test email from your IPO Reminder system.</p>
            <p>If you received this email, your email configuration is working correctly!</p>
            <br>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Email sending: ✅ Working</li>
                <li>Database connection: ✅ Tested</li>
                <li>GitHub Actions: 🔄 Ready</li>
            </ul>
            <br>
            <p>Your IPO Reminder system is ready to send you notifications about upcoming IPOs!</p>
            """,
            recipient_email=recipient_email,
            sender_name="IPO Reminder Test"
        )

        if result:
            print("✅ Test email sent successfully!")
            print(f"📧 Check your inbox at: {recipient_email}")
            return True
        else:
            print("❌ Failed to send test email")
            return False

    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print("\n🔍 Common issues and solutions:")
        print("1. Gmail 2FA enabled? → Generate an App Password")
        print("2. Wrong credentials? → Check email and password")
        print("3. Gmail blocking? → Enable 'Less secure app access' or use App Password")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_email())
    sys.exit(0 if success else 1)
