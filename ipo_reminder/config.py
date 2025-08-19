"""Configuration settings for the IPO Reminder Bot."""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Email Configuration
SENDER_EMAIL = os.getenv("OUTLOOK_EMAIL")
if not SENDER_EMAIL:
    raise ValueError("OUTLOOK_EMAIL environment variable is not set in .env file")

RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
if not RECIPIENT_EMAIL:
    RECIPIENT_EMAIL = SENDER_EMAIL
    logger.warning("RECIPIENT_EMAIL not set, defaulting to SENDER_EMAIL")

# Microsoft Graph API OAuth2 configuration
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

# Web Scraping Configuration
BASE_URL = "https://www.chittorgarh.com"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))  # seconds between requests

# User Agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"

# Validation
def validate_config() -> None:
    """Validate required configuration settings."""
    required_vars = {
        "OUTLOOK_EMAIL": SENDER_EMAIL,
        "OUTLOOK_APP_PASSWORD": SENDER_PASSWORD
    }
    
    missing_vars = [name for name, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(
            "Missing required environment variables: " + 
            ", ".join(missing_vars)
        )

# Validate configuration on import
validate_config()
