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


def format_personal_guide_email(now_date, ipos: List) -> Tuple[str, str, str]:
    """Format clean, focused email as personal investment guide."""
    return format_ipo_email_html(now_date, ipos)


def format_ipo_email_html(today_date, ipos: List) -> Tuple[str, str, str]:
    """Formats a professional HTML email with IPO recommendations."""
    from .deep_analyzer import DeepIPOAnalyzer

    formatted_date = today_date.strftime("%d %b %Y")
    subject = f"IPO Investment Guide • {formatted_date}"

    if not ipos:
        text_body = f"No IPOs closing today ({formatted_date}). Your investment guide: Stay patient, focus on quality opportunities."
        html_body = f"""
        <p>No IPOs closing today ({formatted_date}).</p>
        <p><strong>Your investment guide:</strong> Stay patient and focus on quality opportunities.</p>
        """
        return subject, text_body, html_body

    analyzer = DeepIPOAnalyzer()
    
    # --- Text Body Generation ---
    text_lines = [f"Your Personal IPO Investment Guide - {formatted_date}\n"]
    for i, ipo in enumerate(ipos, 1):
        company_name = getattr(ipo, 'name', 'Unknown Company')
        price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', 'Price TBA')
        analysis = analyzer.analyze_ipo_comprehensive(company_name, price_band)

        action_map = {
            "STRONG_BUY": "✅ APPLY", "BUY": "✅ APPLY",
            "AVOID": "❌ AVOID", "STRONG_AVOID": "❌ AVOID"
        }
        action = action_map.get(analysis.recommendation, "❌ AVOID")
        
        confidence_text = f"{analysis.confidence_score}% confidence"
        insight = analysis.key_strengths[0] if analysis.key_strengths else (analysis.key_risks[0] if analysis.key_risks else "No specific insight.")

        text_lines.extend([
            f"{i}. {company_name}",
            f"   Price: {price_band}",
            f"   My Recommendation: {action} ({confidence_text})",
            f"   Key Insight: {insight}\n"
        ])
    text_lines.append("---\nYour personal investment guide - based on deep fundamental analysis.")
    text_body = "\n".join(text_lines)

    # --- HTML Body Generation ---
    html_parts = [f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">IPO Investment Guide</h1>
            <p style="margin: 0;">{formatted_date}</p>
        </div>
        <div style="padding: 20px;">
    """]

    for ipo in ipos:
        company_name = getattr(ipo, 'name', 'Unknown Company')
        price_band = getattr(ipo, 'price_band', None) or getattr(ipo, 'price_range', 'Price TBA')
        analysis = analyzer.analyze_ipo_comprehensive(company_name, price_band)

        rec_map = {
            "STRONG_BUY": ("#28a745", "APPLY"), "BUY": ("#28a745", "APPLY"),
            "AVOID": ("#dc3545", "AVOID"), "STRONG_AVOID": ("#dc3545", "AVOID")
        }
        rec_color, rec_text = rec_map.get(analysis.recommendation, ("#dc3545", "AVOID"))
        
        insight = analysis.key_strengths[0] if analysis.key_strengths else (analysis.key_risks[0] if analysis.key_risks else "Not available.")

        html_parts.append(f"""
        <div style="margin-bottom: 20px; padding: 15px; border-left: 5px solid {rec_color}; background-color: #f9f9f9; border-radius: 5px;">
            <h3 style="margin-top: 0; margin-bottom: 10px; color: #444;">{company_name}</h3>
            <p style="margin: 5px 0;"><strong>Price:</strong> {price_band}</p>
            <p style="margin: 5px 0;"><strong>Recommendation:</strong> <span style="color: {rec_color}; font-weight: bold;">{rec_text}</span></p>
            <p style="margin: 5px 0;"><strong>Confidence:</strong> {analysis.confidence_score}%</p>
            <p style="margin: 5px 0;"><strong>Key Insight:</strong> {insight}</p>
        </div>
        """)

    html_parts.append("""
        </div>
        <div style="background-color: #f2f2f2; color: #666; padding: 15px; text-align: center; font-size: 12px;">
            <p style="margin: 0;">This guide is based on automated fundamental analysis. Always do your own research.</p>
        </div>
    </div>
    """)
    html_body = "".join(html_parts)

    return subject, text_body, html_body
