"""Configuration settings for the Enterprise IPO Reminder."""
import os
import logging
from typing import Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Email Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or os.getenv("OUTLOOK_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or os.getenv("OUTLOOK_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SENDER_EMAIL)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ipo_reminder")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Redis Cache Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour default
CACHE_MAX_MEMORY = os.getenv("CACHE_MAX_MEMORY", "256mb")

# Official API Configuration
BSE_API_KEY = os.getenv("BSE_API_KEY")
BSE_API_BASE_URL = os.getenv("BSE_API_BASE_URL", "https://api.bseindia.com")
BSE_API_TIMEOUT = int(os.getenv("BSE_API_TIMEOUT", "30"))

NSE_API_KEY = os.getenv("NSE_API_KEY")
NSE_API_BASE_URL = os.getenv("NSE_API_BASE_URL", "https://www.nseindia.com/api")
NSE_API_TIMEOUT = int(os.getenv("NSE_API_TIMEOUT", "30"))

# Rate Limiting Configuration
RATE_LIMIT_REQUESTS_PER_SECOND = int(os.getenv("RATE_LIMIT_REQUESTS_PER_SECOND", "10"))
RATE_LIMIT_BURST_CAPACITY = int(os.getenv("RATE_LIMIT_BURST_CAPACITY", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "300"))  # 5 minutes
CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS = int(os.getenv("CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS", "3"))
CIRCUIT_BREAKER_EXPECTED_EXCEPTION = Exception

# API Specific Rate Limits (requests per minute)
BSE_API_RATE_LIMIT = int(os.getenv("BSE_API_RATE_LIMIT", "100"))
NSE_API_RATE_LIMIT = int(os.getenv("NSE_API_RATE_LIMIT", "50"))

# Bulkhead Configuration
MAX_CONCURRENT_DB_REQUESTS = int(os.getenv("MAX_CONCURRENT_DB_REQUESTS", "50"))
MAX_CONCURRENT_API_REQUESTS = int(os.getenv("MAX_CONCURRENT_API_REQUESTS", "20"))

# Monitoring Configuration
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "60"))

# Compliance Configuration
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "365"))
COMPLIANCE_LEVEL = os.getenv("COMPLIANCE_LEVEL", "HIGH")

# Security Configuration
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your-encryption-key-here")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "480"))  # 8 hours

# Performance Configuration
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
ASYNC_TIMEOUT = int(os.getenv("ASYNC_TIMEOUT", "300"))  # 5 minutes

# Log Level Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Web Scraping Configuration
BASE_URL = "https://www.chittorgarh.com"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))  # seconds between requests

# User Agent
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"

# Enterprise Features
ENTERPRISE_MODE = os.getenv("ENTERPRISE_MODE", "true").lower() == "true"
OFFICIAL_APIS_ENABLED = os.getenv("OFFICIAL_APIS_ENABLED", "true").lower() == "true"
MULTI_SOURCE_ENABLED = os.getenv("MULTI_SOURCE_ENABLED", "true").lower() == "true"

def check_email_config():
    """Check if email configuration is available and provide helpful error message if not."""
    # Check for SMTP credentials
    has_smtp = all([SENDER_EMAIL, SENDER_PASSWORD])

    if not has_smtp:
        print("❌ No email configuration found!")
        print("You need SMTP credentials to send emails.")
        print("\n📧 SMTP Configuration:")
        print("Set these environment variables in GitHub repository secrets:")
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

def check_enterprise_config():
    """Check if enterprise configuration is properly set up."""
    issues = []

    # Check database
    if not DATABASE_URL or DATABASE_URL.startswith("postgresql://user:password"):
        issues.append("❌ DATABASE_URL not properly configured")

    # Check Redis
    if not REDIS_URL or REDIS_URL == "redis://localhost:6379/0":
        issues.append("❌ REDIS_URL not properly configured")

    # Check API keys (optional but recommended)
    if not BSE_API_KEY:
        issues.append("⚠️  BSE_API_KEY not configured (will fallback to scraping)")

    if not NSE_API_KEY:
        issues.append("⚠️  NSE_API_KEY not configured (will fallback to scraping)")

    # Check security
    if ENCRYPTION_KEY == "your-encryption-key-here":
        issues.append("❌ ENCRYPTION_KEY not properly configured")

    if JWT_SECRET_KEY == "your-jwt-secret-key-here":
        issues.append("❌ JWT_SECRET_KEY not properly configured")

    if issues:
        print("\n🔧 Enterprise Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
        print("\n📋 Required Environment Variables:")
        print("   DATABASE_URL=postgresql://user:password@host:port/database")
        print("   REDIS_URL=redis://host:port/db")
        print("   BSE_API_KEY=your-bse-api-key")
        print("   NSE_API_KEY=your-nse-api-key")
        print("   ENCRYPTION_KEY=your-32-char-encryption-key")
        print("   JWT_SECRET_KEY=your-jwt-secret-key")
        return False

    print("✅ Enterprise configuration validated")
    return True

def validate_email_config() -> None:
    """Raise if required email config is missing. Call this at runtime when sending email."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        raise ValueError(
            "Missing required email configuration.\n"
            "Please set the following environment variables in GitHub repository secrets:\n"
            "1. SENDER_EMAIL: Your email address (Gmail, Outlook, etc.)\n"
            "2. SENDER_PASSWORD: Your App Password\n\n"
            "For Gmail users:\n"
            "1. Enable 2-Factor Authentication\n"
            "2. Generate an App Password at: https://myaccount.google.com/apppasswords\n"
            "3. Use the App Password as SENDER_PASSWORD"
        )

def get_database_config() -> dict:
    """Get database configuration dictionary."""
    return {
        'url': DATABASE_URL,
        'pool_size': DB_POOL_SIZE,
        'max_overflow': DB_MAX_OVERFLOW,
        'pool_timeout': DB_POOL_TIMEOUT
    }

def get_cache_config() -> dict:
    """Get cache configuration dictionary."""
    return {
        'url': REDIS_URL,
        'ttl_seconds': CACHE_TTL_SECONDS,
        'max_memory': CACHE_MAX_MEMORY
    }

def get_api_config() -> dict:
    """Get API configuration dictionary."""
    return {
        'bse': {
            'api_key': BSE_API_KEY,
            'base_url': BSE_API_BASE_URL,
            'timeout': BSE_API_TIMEOUT
        },
        'nse': {
            'api_key': NSE_API_KEY,
            'base_url': NSE_API_BASE_URL,
            'timeout': NSE_API_TIMEOUT
        }
    }

def get_monitoring_config() -> dict:
    """Get monitoring configuration dictionary."""
    return {
        "enabled": MONITORING_ENABLED,
        "metrics_retention_days": METRICS_RETENTION_DAYS,
        "alert_cooldown_minutes": ALERT_COOLDOWN_MINUTES,
    }

def get_rate_limit_config() -> dict:
    """Get rate limiting configuration dictionary."""
    return {
        "requests_per_second": RATE_LIMIT_REQUESTS_PER_SECOND,
        "burst_capacity": RATE_LIMIT_BURST_CAPACITY,
        "time_window": RATE_LIMIT_WINDOW_SECONDS,
        "bse_api_limit": BSE_API_RATE_LIMIT,
        "nse_api_limit": NSE_API_RATE_LIMIT
    }

def get_circuit_breaker_config() -> dict:
    """Get circuit breaker configuration dictionary."""
    return {
        "failure_threshold": CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        "recovery_timeout": CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        "half_open_max_requests": CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS
    }

def get_bulkhead_config() -> dict:
    """Get bulkhead configuration dictionary."""
    return {
        "max_concurrent_db_requests": MAX_CONCURRENT_DB_REQUESTS,
        "max_concurrent_api_requests": MAX_CONCURRENT_API_REQUESTS
    }

def get_compliance_config() -> dict:
    """Get compliance configuration dictionary."""
    return {
        'audit_enabled': AUDIT_ENABLED,
        'audit_retention_days': AUDIT_RETENTION_DAYS,
        'compliance_level': COMPLIANCE_LEVEL
    }
