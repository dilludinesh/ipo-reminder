"""
IPO categorization module for Main Board vs SME classification.
"""

import logging
import re
from typing import List, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IPOCategory:
    """IPO category classification."""
    category: str  # MAIN_BOARD, SME, UNKNOWN
    exchange: str  # BSE, NSE, BSE_SME, NSE_EMERGE
    min_application_size: int  # Minimum investment amount
    lot_size: int = None
    retail_friendly: bool = True

class IPOCategorizer:
    """Categorizes IPOs into Main Board vs SME."""
    
    def __init__(self):
        # SME indicators in company names
        self.sme_indicators = [
            'sme', 'small', 'micro', 'emerge', 'limited liability partnership',
            'llp', 'private limited', 'pvt ltd', 'projects', 'engineering projects',
            'oval', 'enterprises', 'services', 'ventures', 'associates'
        ]
        
        # Main board indicators (must be strong indicators)
        self.main_board_indicators = [
            'technologies limited', 'corporation limited', 'industries limited',
            'international limited', 'global limited', 'systems limited',
            'solutions limited'
        ]
        
        # Known large companies (definitely main board)
        self.large_companies = [
            'hdfc', 'icici', 'sbi', 'tcs', 'infosys', 'wipro', 'reliance',
            'bajaj', 'mahindra', 'tata', 'maruti', 'bharti', 'adani'
        ]
    
    def categorize_ipo(self, company_name: str, price_band: str = None, 
                      lot_size: int = None) -> IPOCategory:
        """Categorize IPO as Main Board or SME."""
        
        name_lower = company_name.lower()
        
        # Check for known large companies (definitely Main Board)
        if any(large_company in name_lower for large_company in self.large_companies):
            return IPOCategory(
                category="MAIN_BOARD",
                exchange="NSE/BSE",
                min_application_size=self._estimate_min_investment(price_band, lot_size),
                lot_size=lot_size,
                retail_friendly=True
            )
        
        # Check for explicit SME indicators
        if any(sme_indicator in name_lower for sme_indicator in self.sme_indicators):
            return IPOCategory(
                category="SME",
                exchange="BSE_SME/NSE_EMERGE",
                min_application_size=self._estimate_min_investment(price_band, lot_size),
                lot_size=lot_size,
                retail_friendly=False  # Higher risk for retail
            )
        
        # Price-based classification (more aggressive SME detection)
        if price_band:
            avg_price = self._extract_average_price(price_band)
            if avg_price:
                # Low price strongly indicates SME
                if avg_price < 100:
                    return IPOCategory(
                        category="SME",
                        exchange="BSE_SME/NSE_EMERGE", 
                        min_application_size=self._estimate_min_investment(price_band, lot_size),
                        lot_size=lot_size,
                        retail_friendly=False
                    )
                # Very high price indicates Main Board
                elif avg_price > 500:
                    return IPOCategory(
                        category="MAIN_BOARD",
                        exchange="NSE/BSE",
                        min_application_size=self._estimate_min_investment(price_band, lot_size),
                        lot_size=lot_size,
                        retail_friendly=True
                    )
        
        # Business name analysis (stricter criteria for Main Board)
        if any(indicator in name_lower for indicator in self.main_board_indicators):
            return IPOCategory(
                category="MAIN_BOARD",
                exchange="NSE/BSE",
                min_application_size=self._estimate_min_investment(price_band, lot_size),
                lot_size=lot_size,
                retail_friendly=True
            )
        
        # Default to SME if uncertain (safer for retail investors to be cautious)
        return IPOCategory(
            category="SME", 
            exchange="BSE_SME/NSE_EMERGE",
            min_application_size=self._estimate_min_investment(price_band, lot_size),
            lot_size=lot_size,
            retail_friendly=False
        )
    
    def _extract_average_price(self, price_band: str) -> float:
        """Extract average price from price band."""
        try:
            if price_band and "₹" in price_band:
                prices = re.findall(r'₹(\d+(?:,\d+)*)', price_band.replace(' ', ''))
                if prices:
                    clean_prices = [int(p.replace(',', '')) for p in prices]
                    return sum(clean_prices) / len(clean_prices)
        except Exception:
            pass
        return None
    
    def _estimate_min_investment(self, price_band: str, lot_size: int = None) -> int:
        """Estimate minimum investment amount."""
        avg_price = self._extract_average_price(price_band)
        if avg_price and lot_size:
            return int(avg_price * lot_size)
        elif avg_price:
            # Assume standard lot sizes
            if avg_price < 100:
                return int(avg_price * 150)  # SME typical lot
            else:
                return int(avg_price * 75)   # Main board typical lot
        return 15000  # Default minimum


def categorize_ipos(ipos: List) -> Tuple[List, List]:
    """Categorize IPOs into Main Board and SME lists."""
    categorizer = IPOCategorizer()
    
    main_board_ipos = []
    sme_ipos = []
    
    for ipo in ipos:
        company_name = getattr(ipo, 'name', 'Unknown Company')
        price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', None)
        lot_size = getattr(ipo, 'lot_size', None)
        
        category = categorizer.categorize_ipo(company_name, price_band, lot_size)
        
        # Add category info to IPO object
        ipo.category = category
        
        if category.category == "MAIN_BOARD":
            main_board_ipos.append(ipo)
        else:
            sme_ipos.append(ipo)
    
    return main_board_ipos, sme_ipos


def format_personal_guide_email(now_date, ipos: List) -> Tuple[str, str]:
    """Format clean, focused email as personal investment guide."""
    from datetime import date
    from .deep_analyzer import DeepIPOAnalyzer

    # Create subject line
    formatted_date = now_date.strftime("%d %b %Y")
    subject = f"IPO Investment Guide • {formatted_date}"

    if not ipos:
        body = f"""No IPOs closing today ({formatted_date})

Your investment guide: Stay patient, focus on quality opportunities.
"""
        return subject, body

    analyzer = DeepIPOAnalyzer()
    lines = [f"Your Personal IPO Investment Guide - {formatted_date}\n"]

    for i, ipo in enumerate(ipos, 1):
        company_name = getattr(ipo, 'name', 'Unknown Company')
        price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', 'Price TBA')

        # Perform deep analysis
        analysis = analyzer.analyze_ipo_comprehensive(company_name, price_band)

        # Convert to clear action
        if analysis.recommendation in ["STRONG_BUY", "BUY"]:
            action = "✅ APPLY"
            confidence_text = f"High confidence ({analysis.confidence_score}%)"
        elif analysis.recommendation == "HOLD":
            action = "⚠️ HOLD"
            confidence_text = f"Moderate confidence ({analysis.confidence_score}%)"
        else:
            action = "❌ AVOID"
            confidence_text = f"Strong avoid ({analysis.confidence_score}%)"

        lines.append(f"{i}. {company_name}")
        lines.append(f"   Price: {price_band}")
        lines.append(f"   My Recommendation: {action}")
        lines.append(f"   Analysis Confidence: {confidence_text}")

        # Add key insight (just one, most important)
        if analysis.key_strengths:
            lines.append(f"   Key Strength: {analysis.key_strengths[0]}")
        elif analysis.key_risks:
            lines.append(f"   Key Risk: {analysis.key_risks[0]}")

        lines.append("")

    lines.append("---")
    lines.append("Your personal investment guide - based on deep fundamental analysis.")
    lines.append("No guesswork, just clear guidance for your portfolio decisions.")

    body = "\n".join(lines)
    return subject, body
