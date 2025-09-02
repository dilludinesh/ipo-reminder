"""Utility functions for IPO analysis and formatting."""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import date

logger = logging.getLogger(__name__)


def sanitize_input(text: str) -> str:
    """Sanitize input text to prevent injection attacks."""
    if not text:
        return ""
    # Remove HTML tags and dangerous characters
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'[<>]', '', text)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()


def validate_price_band(price_band: str) -> Optional[Dict[str, float]]:
    """Validate and parse price band into min/max/avg prices."""
    if not price_band or price_band == "Price TBA":
        return None

    try:
        # Extract prices using regex
        price_match = re.findall(r'₹?\s*(\d+(?:,\d+)*)', price_band.replace(' ', ''))
        if not price_match:
            return None

        prices = []
        for price_str in price_match:
            clean_price = price_str.replace(',', '')
            if clean_price.isdigit():
                prices.append(float(clean_price))

        if not prices:
            return None

        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        return {
            'min': min_price,
            'max': max_price,
            'avg': avg_price
        }

    except Exception as e:
        logger.warning(f"Error parsing price band '{price_band}': {e}")
        return None


def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    if amount >= 10000000:  # 10 crores
        return f"₹{amount/10000000:.1f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f} L"
    else:
        return f"₹{amount:,.0f}"


def calculate_risk_score(company_name: str, price_band: str, sector: str = "") -> Dict[str, Any]:
    """Calculate comprehensive risk score for an IPO."""
    risk_score = 50  # Base score
    risk_factors = []

    name_lower = company_name.lower()

    # Company size risk
    if any(term in name_lower for term in ['sme', 'small', 'micro', 'emerge']):
        risk_score += 25  # Increased from 20
        risk_factors.append("SME company - higher risk")

    # Sector risk
    high_risk_sectors = ['real estate', 'construction', 'mining', 'gambling']
    if any(sector_term in name_lower for sector_term in high_risk_sectors):
        risk_score += 20  # Increased from 15
        risk_factors.append(f"High-risk sector: {sector}")

    # Price risk
    price_info = validate_price_band(price_band)
    if price_info:
        if price_info['avg'] > 1000:
            risk_score += 20  # Increased from 15
            risk_factors.append("High price point")
        elif price_info['avg'] < 50:
            risk_score -= 5
            risk_factors.append("Low price point - accessible")

    # Regulatory risk
    regulated_sectors = ['bank', 'finance', 'insurance', 'healthcare', 'pharma']
    if any(reg_term in name_lower for reg_term in regulated_sectors):
        risk_score += 15  # Increased from 10
        risk_factors.append("Highly regulated sector")

    return {
        'score': min(100, max(0, risk_score)),
        'level': 'HIGH' if risk_score >= 70 else 'MEDIUM' if risk_score > 40 else 'LOW',
        'factors': risk_factors
    }


def generate_investment_thesis(company_name: str, price_band: str) -> Dict[str, Any]:
    """Generate investment thesis based on company analysis."""
    thesis = {
        'recommendation': 'HOLD',
        'confidence': 'MEDIUM',
        'key_points': [],
        'risks': [],
        'opportunities': []
    }

    name_lower = company_name.lower()

    # Technology companies
    if any(tech in name_lower for tech in ['tech', 'software', 'digital', 'ai', 'data']):
        thesis['recommendation'] = 'BUY'
        thesis['confidence'] = 'HIGH'
        thesis['key_points'].append("Technology sector with strong growth potential")
        thesis['opportunities'].append("Digital transformation driving demand")
        thesis['risks'].append("Rapid technological changes")

    # Healthcare/Pharma
    elif any(health in name_lower for health in ['healthcare', 'pharma', 'medical', 'bio']):
        thesis['recommendation'] = 'BUY'
        thesis['confidence'] = 'HIGH'
        thesis['key_points'].append("Defensive sector with stable demand")
        thesis['opportunities'].append("Aging population and healthcare needs")
        thesis['risks'].append("Regulatory changes and approval delays")

    # Financial Services
    elif any(fin in name_lower for fin in ['bank', 'finance', 'insurance']):
        thesis['recommendation'] = 'HOLD'
        thesis['confidence'] = 'MEDIUM'
        thesis['key_points'].append("Established sector with steady returns")
        thesis['opportunities'].append("Financial inclusion and digital banking")
        thesis['risks'].append("Interest rate changes and regulatory pressure")

    # Real Estate
    elif any(re in name_lower for re in ['real estate', 'property', 'construction']):
        thesis['recommendation'] = 'AVOID'
        thesis['confidence'] = 'HIGH'
        thesis['key_points'].append("Interest rate sensitive sector")
        thesis['risks'].append("Economic slowdowns impact demand")
        thesis['risks'].append("Regulatory changes affect profitability")

    # Manufacturing
    elif any(mfg in name_lower for mfg in ['manufacturing', 'industrial', 'steel', 'chemical']):
        thesis['recommendation'] = 'HOLD'
        thesis['confidence'] = 'MEDIUM'
        thesis['key_points'].append("Cyclical sector dependent on economic conditions")
        thesis['opportunities'].append("Infrastructure development drives demand")
        thesis['risks'].append("Commodity price volatility")

    # SME companies
    if any(sme in name_lower for sme in ['sme', 'small', 'micro']):
        thesis['risks'].append("Limited track record and higher business risk")
        thesis['opportunities'].append("Potential for significant growth if business model succeeds")

    return thesis


def create_email_summary(ipos: List, today_date: date) -> Dict[str, Any]:
    """Create a comprehensive email summary for IPOs."""
    summary = {
        'total_ipos': len(ipos),
        'main_board': 0,
        'sme': 0,
        'high_recommendation': 0,
        'medium_recommendation': 0,
        'low_recommendation': 0,
        'sectors': set(),
        'price_ranges': [],
        'key_highlights': []
    }

    for ipo in ipos:
        company_name = getattr(ipo, 'name', 'Unknown')
        price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', None)

        # Categorize by type
        if '(SME)' in company_name or any(sme in company_name.lower() for sme in ['sme', 'emerge']):
            summary['sme'] += 1
        else:
            summary['main_board'] += 1

        # Analyze sector
        name_lower = company_name.lower()
        if any(tech in name_lower for tech in ['tech', 'software', 'digital']):
            summary['sectors'].add('Technology')
        elif any(health in name_lower for health in ['healthcare', 'pharma', 'medical']):
            summary['sectors'].add('Healthcare')
        elif any(fin in name_lower for fin in ['bank', 'finance', 'insurance']):
            summary['sectors'].add('Financial Services')
        else:
            summary['sectors'].add('Other')

        # Price analysis
        price_info = validate_price_band(price_band)
        if price_info:
            summary['price_ranges'].append(price_info['avg'])

        # Generate thesis for recommendations
        thesis = generate_investment_thesis(company_name, price_band or "")
        if thesis['recommendation'] == 'BUY':
            summary['high_recommendation'] += 1
        elif thesis['recommendation'] == 'HOLD':
            summary['medium_recommendation'] += 1
        else:
            summary['low_recommendation'] += 1

    # Calculate averages
    if summary['price_ranges']:
        summary['avg_price'] = sum(summary['price_ranges']) / len(summary['price_ranges'])
    else:
        summary['avg_price'] = 0

    # Generate key highlights
    if summary['high_recommendation'] > 0:
        summary['key_highlights'].append(f"{summary['high_recommendation']} high-potential IPOs")
    if summary['sme'] > 0:
        summary['key_highlights'].append(f"{summary['sme']} SME IPOs with growth potential")
    if summary['main_board'] > 0:
        summary['key_highlights'].append(f"{summary['main_board']} Main Board IPOs")

    return summary
