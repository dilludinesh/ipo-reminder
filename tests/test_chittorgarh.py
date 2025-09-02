import pytest
from ipo_reminder.sources.chittorgarh import _parse_date, _clean_text
from ipo_reminder.utils import sanitize_input, validate_price_band, calculate_risk_score
from datetime import date

def test_parse_date_valid():
    assert _parse_date("01-Jan-2025") == date(2025, 1, 1)
    assert _parse_date("31-12-2024") == date(2024, 12, 31)
    assert _parse_date("2025-08-21") == date(2025, 8, 21)

def test_parse_date_invalid():
    assert _parse_date("") is None
    assert _parse_date(None) is None
    assert _parse_date("not a date") is None

def test_clean_text():
    assert _clean_text("  hello   world  ") == "hello world"
    assert _clean_text("<script>alert('xss')</script>Hello") == "alert('xss')Hello"
    assert _clean_text("Normal text") == "Normal text"

def test_sanitize_input():
    assert sanitize_input("<script>alert('xss')</script>") == "alert('xss')"
    assert sanitize_input("normal text") == "normal text"
    assert sanitize_input("text with <b>tags</b>") == "text with tags"

def test_validate_price_band():
    result = validate_price_band("₹100 - ₹120")
    assert result is not None
    assert result['min'] == 100
    assert result['max'] == 120
    assert result['avg'] == 110

    assert validate_price_band("invalid") is None
    assert validate_price_band("") is None

def test_calculate_risk_score():
    # Test SME company
    risk = calculate_risk_score("ABC SME Limited", "₹50 - ₹60")
    assert risk['level'] == 'HIGH'
    assert 'SME company' in str(risk['factors'])

    # Test low-risk company
    risk = calculate_risk_score("Large Tech Corp", "₹200 - ₹250")
    assert risk['level'] in ['LOW', 'MEDIUM']

def test_edge_cases():
    # Test with None inputs
    assert sanitize_input(None) == ""
    assert validate_price_band(None) is None

    # Test with very high prices
    risk = calculate_risk_score("Premium Company", "₹2000 - ₹2500")
    assert risk['level'] == 'HIGH'

    # Test with very low prices
    risk = calculate_risk_score("Budget Company", "₹10 - ₹15")
    assert 'Low price point' in str(risk['factors'])
