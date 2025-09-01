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
            'llp', 'private limited', 'pvt ltd'
        ]
        
        # Main board indicators
        self.main_board_indicators = [
            'technologies', 'corporation', 'industries', 'enterprises',
            'systems', 'solutions', 'group', 'international', 'global'
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
        
        # Price-based classification
        if price_band:
            avg_price = self._extract_average_price(price_band)
            if avg_price:
                # Very low price often indicates SME
                if avg_price < 50:
                    return IPOCategory(
                        category="SME",
                        exchange="BSE_SME/NSE_EMERGE", 
                        min_application_size=self._estimate_min_investment(price_band, lot_size),
                        lot_size=lot_size,
                        retail_friendly=False
                    )
                # Higher price often indicates Main Board
                elif avg_price > 200:
                    return IPOCategory(
                        category="MAIN_BOARD",
                        exchange="NSE/BSE",
                        min_application_size=self._estimate_min_investment(price_band, lot_size),
                        lot_size=lot_size,
                        retail_friendly=True
                    )
        
        # Business name analysis
        if any(indicator in name_lower for indicator in self.main_board_indicators):
            return IPOCategory(
                category="MAIN_BOARD",
                exchange="NSE/BSE",
                min_application_size=self._estimate_min_investment(price_band, lot_size),
                lot_size=lot_size,
                retail_friendly=True
            )
        
        # Default to Main Board if uncertain (safer assumption)
        return IPOCategory(
            category="MAIN_BOARD", 
            exchange="NSE/BSE",
            min_application_size=self._estimate_min_investment(price_band, lot_size),
            lot_size=lot_size,
            retail_friendly=True
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


def format_retail_investor_email(now_date, ipos: List) -> Tuple[str, str]:
    """Format email prioritizing Main Board IPOs for retail investors."""
    from datetime import date
    from .deep_analyzer import DeepIPOAnalyzer
    
    # Create subject line
    formatted_date = now_date.strftime("%d %b %Y")
    subject = f"IPO Alert • Retail Focus • {formatted_date}"
    
    if not ipos:
        body = f"""No IPOs closing today ({formatted_date})

Perfect time to research upcoming Main Board opportunities.
"""
        return subject, body
    
    # Categorize IPOs
    main_board_ipos, sme_ipos = categorize_ipos(ipos)
    
    analyzer = DeepIPOAnalyzer()
    lines = [f"IPO Analysis for Retail Investors - {formatted_date}\n"]
    
    # MAIN BOARD IPOs (Primary Focus)
    if main_board_ipos:
        lines.append("🏛️ MAIN BOARD IPOs (PRIMARY FOCUS)")
        lines.append("=" * 40)
        
        for i, ipo in enumerate(main_board_ipos, 1):
            company_name = getattr(ipo, 'name', 'Unknown Company')
            price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', 'Price TBA')
            
            # Perform deep analysis
            analysis = analyzer.analyze_ipo_comprehensive(company_name, price_band)
            
            # Convert to action
            if analysis.recommendation in ["STRONG_BUY", "BUY"]:
                action = "✅ APPLY"
                emoji = "🚀" if analysis.recommendation == "STRONG_BUY" else "✅"
            elif analysis.recommendation == "HOLD":
                action = "⚠️ RESEARCH"
                emoji = "⚠️"
            else:
                action = "❌ AVOID"
                emoji = "❌"
            
            lines.append(f"\n{i}. {company_name}")
            lines.append(f"   Price: {price_band}")
            lines.append(f"   Exchange: {ipo.category.exchange}")
            lines.append(f"   Min Investment: ~₹{ipo.category.min_application_size:,}")
            lines.append(f"   {emoji} Advice: {action}")
            lines.append(f"   Confidence: {analysis.confidence_score}% | Risk: {analysis.risk_score}/100")
            
            # Add key insight
            if analysis.key_strengths:
                lines.append(f"   💪 {analysis.key_strengths[0]}")
            if analysis.key_risks:
                lines.append(f"   ⚠️ {analysis.key_risks[0]}")
    else:
        lines.append("🏛️ MAIN BOARD IPOs: None closing today")
    
    # SME IPOs (Secondary Focus)
    if sme_ipos:
        lines.append(f"\n\n🏢 SME IPOs (HIGHER RISK - SECONDARY FOCUS)")
        lines.append("=" * 45)
        lines.append("⚠️ SME IPOs are higher risk - invest only small amounts")
        
        for i, ipo in enumerate(sme_ipos, 1):
            company_name = getattr(ipo, 'name', 'Unknown Company')
            price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', 'Price TBA')
            
            # Perform analysis (with extra caution for SME)
            analysis = analyzer.analyze_ipo_comprehensive(company_name, price_band)
            
            # More conservative for SME
            if analysis.recommendation in ["STRONG_BUY", "BUY"]:
                action = "⚠️ SMALL POSITION" 
                emoji = "⚠️"
            elif analysis.recommendation == "HOLD":
                action = "🔍 RESEARCH DEEPLY"
                emoji = "🔍"
            else:
                action = "❌ AVOID"
                emoji = "❌"
            
            lines.append(f"\n{i}. {company_name}")
            lines.append(f"   Price: {price_band}")
            lines.append(f"   Exchange: {ipo.category.exchange}")
            lines.append(f"   Min Investment: ~₹{ipo.category.min_application_size:,}")
            lines.append(f"   {emoji} SME Advice: {action}")
            lines.append(f"   Risk Score: {analysis.risk_score}/100 (SME = Higher Risk)")
    
    # Investment guidance for retail investors
    lines.append(f"\n\n💡 RETAIL INVESTOR GUIDANCE:")
    lines.append("• Focus primarily on Main Board IPOs (lower risk)")
    lines.append("• SME IPOs: Only invest small amounts you can afford to lose")
    lines.append("• Main Board IPOs have better liquidity and transparency")
    lines.append("• Diversify - don't put all money in one IPO")
    
    lines.append(f"\n---")
    lines.append("Analysis based on fundamental research.")
    lines.append("Main Board IPOs prioritized for retail investors.")
    
    body = "\n".join(lines)
    return subject, body
