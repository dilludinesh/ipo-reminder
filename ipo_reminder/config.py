"""Configuration settings for the IPO Reminder Bot."""
import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Email Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or os.getenv("OUTLOOK_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or os.getenv("OUTLOOK_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SENDER_EMAIL)

# Log Level Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def check_email_config():
    """Check if email configuration is available and provide helpful error message if not."""
    # Check for SMTP credentials
    has_smtp = all([SENDER_EMAIL, SENDER_PASSWORD])
    
    if not has_smtp:
        print("❌ No email configuration found!")
        print("You need SMTP credentials to send emails.")
        print("\n📧 SMTP Configuration:")
        print("Set these environment variables in your .env file:")
        print("  SENDER_EMAIL=your-email@gmail.com")
        print("  SENDER_PASSWORD=your-app-password")
        print("  RECIPIENT_EMAIL=recipient@email.com")
        print("\n� For Gmail users:")
        print("  1. Enable 2-Factor Authentication")
        print("  2. Generate an App Password at: https://myaccount.google.com/apppasswords")
        print("  3. Use the App Password as SENDER_PASSWORD")
        return False
    
    print("✅ SMTP configuration found")
    return True

def validate_email_config() -> None:
    """Raise if required email config is missing. Call this at runtime when sending email."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        raise ValueError(
            "Missing required email configuration.\n"
            "Please set the following environment variables in your environment or .env file:\n"
            "1. SENDER_EMAIL: Your email address (Gmail, Outlook, etc.)\n"
            "2. SENDER_PASSWORD: Your App Password\n\n"
            "For Gmail users:\n"
            "1. Enable 2-Factor Authentication\n"
            "2. Generate an App Password at: https://myaccount.google.com/apppasswords\n"
            "3. Use the App Password as SENDER_PASSWORD"
        )

# Web Scraping Configuration
BASE_URL = "https://www.chittorgarh.com"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))  # seconds between requests

# User Agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"
