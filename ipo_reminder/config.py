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

# Validate required configuration
if not all([SENDER_EMAIL, SENDER_PASSWORD]):
    raise ValueError(
        "Missing required email configuration.\n"
        "Please set the following environment variables in your .env file:\n"
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

# Configuration is validated at the top of the file
