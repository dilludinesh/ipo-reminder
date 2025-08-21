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

# Microsoft Graph API Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

# Email Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or os.getenv("OUTLOOK_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or os.getenv("OUTLOOK_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SENDER_EMAIL)

# Log Level Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Email configuration dict for easy access
EMAIL_CONFIG = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'tenant_id': TENANT_ID,
    'sender_email': SENDER_EMAIL,
    'sender_password': SENDER_PASSWORD,
    'recipient_email': RECIPIENT_EMAIL
}

def check_email_config():
    """Check if email configuration is available and provide helpful error message if not."""
    # Check for Microsoft Graph credentials
    has_graph = all([CLIENT_ID, CLIENT_SECRET, TENANT_ID])
    
    # Check for SMTP credentials
    has_smtp = all([SENDER_EMAIL, SENDER_PASSWORD])
    
    if not has_graph and not has_smtp:
        print("❌ No email configuration found!")
        print("You need either Microsoft Graph API credentials OR SMTP credentials.")
        print("\n📧 Option 1: Microsoft Graph API (recommended)")
        print("Set these environment variables in your .env file:")
        print("  CLIENT_ID=your-azure-app-client-id")
        print("  CLIENT_SECRET=your-azure-app-client-secret")
        print("  TENANT_ID=your-azure-tenant-id")
        print("  SENDER_EMAIL=your-email@outlook.com")
        print("  RECIPIENT_EMAIL=recipient@email.com")
        print("\n📧 Option 2: SMTP (basic)")
        print("Set these environment variables in your .env file:")
        print("  SENDER_EMAIL=your-email@outlook.com")
        print("  SENDER_PASSWORD=your-app-password")
        print("  RECIPIENT_EMAIL=recipient@email.com")
        return False
    
    if has_graph:
        print("✅ Microsoft Graph API configuration found")
    elif has_smtp:
        print("✅ SMTP configuration found")
        
    return True

def validate_email_config() -> None:
    """Raise if required email config is missing. Call this at runtime when sending email."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        raise ValueError(
            "Missing required email configuration.\n"
            "Please set the following environment variables in your environment or .env file:\n"
            "1. SENDER_EMAIL: Your Outlook email address\n"
            "2. SENDER_PASSWORD: Your Outlook App Password\n\n"
            "Note: If you're using 2FA, you'll need to create an App Password at:\n"
            "https://account.microsoft.com/security\n"
            "(Go to Security > More security options > Create a new app password)"
        )

# Web Scraping Configuration
BASE_URL = "https://www.chittorgarh.com"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))  # seconds between requests

# User Agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"
