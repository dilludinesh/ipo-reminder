"""
Pytest configuration and fixtures for IPO Reminder tests.
"""
import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
os.environ['BSE_API_KEY'] = 'test_bse_key'
os.environ['NSE_API_KEY'] = 'test_nse_key'

# Pytest event loop policy for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# Common fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch('ipo_reminder.database.DatabaseManager') as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.get_session.return_value = mock_session
        yield mock_db, mock_session

@pytest.fixture
def mock_cache():
    """Mock cache manager."""
    with patch('ipo_reminder.cache.CacheManager') as mock_cache:
        yield mock_cache

@pytest.fixture
def mock_emailer():
    """Mock emailer."""
    with patch('ipo_reminder.emailer.Emailer') as mock_emailer:
        yield mock_emailer

# Sample test data
@pytest.fixture
def sample_ipo_data():
    """Sample IPO data for testing."""
    return {
        'name': 'Test IPO',
        'symbol': 'TST',
        'price_range': '100-110',
        'lot_size': 15,
        'issue_date': '2023-11-01',
        'close_date': '2023-11-03',
        'listing_date': '2023-11-10',
        'min_investment': 15000,
        'source': 'test_source',
        'url': 'http://example.com/ipo/test',
    }
