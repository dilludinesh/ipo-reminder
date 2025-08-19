"""Configuration settings for the IPO Reminder Bot."""
import os
from typing import Optional

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("OUTLOOK_EMAIL")
SENDER_PASSWORD = os.getenv("OUTLOOK_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SENDER_EMAIL)

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
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        raise ValueError(
            "Missing required environment variables: "
            "OUTLOOK_EMAIL and OUTLOOK_APP_PASSWORD must be set"
        )

# Validate configuration on import
validate_config()
