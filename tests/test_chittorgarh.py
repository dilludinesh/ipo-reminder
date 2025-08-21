import pytest
from ipo_reminder.sources.chittorgarh import _parse_date
from datetime import date

def test_parse_date_valid():
    assert _parse_date("01-Jan-2025") == date(2025, 1, 1)
    assert _parse_date("31-12-2024") == date(2024, 12, 31)
    assert _parse_date("2025-08-21") == date(2025, 8, 21)

def test_parse_date_invalid():
    assert _parse_date("") is None
    assert _parse_date(None) is None
    assert _parse_date("not a date") is None
