"""Investment analysis and recommendation engine for IPOs."""
import logging
from datetime import date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InvestmentAnalysis:
    """Investment analysis for an IPO."""
    recommendation: str  # STRONG BUY, BUY, HOLD, AVOID, STRONG AVOID
    confidence: str     # HIGH, MEDIUM, LOW
    reasoning: List[str]
    risk_level: str     # LOW, MEDIUM, HIGH, VERY HIGH
    investment_horizon: str  # SHORT_TERM, MEDIUM_TERM, LONG_TERM
    key_factors: Dict[str, str]  # Factor -> Analysis
    
    
def analyze_ipo_investment(ipo_name: str, price_band: str, sector: str = None, 
                          listing_date: str = None) -> InvestmentAnalysis:
    """Analyze IPO and provide investment recommendation."""
    
    # Investment analysis factors
    reasoning = []
    key_factors = {}
    risk_level = "MEDIUM"
    confidence = "MEDIUM"
    recommendation = "HOLD"
    investment_horizon = "MEDIUM_TERM"
    
    # Analyze company name for sector/business indicators
    name_lower = ipo_name.lower()
    
    # Healthcare/Pharma companies (check first as it's more specific)
    if any(health_word in name_lower for health_word in ['healthcare', 'pharma', 'medical', 'bio', 'drug', 'hospital']):
        key_factors["Sector"] = "Healthcare - Defensive sector with steady demand"
        reasoning.append("✅ Healthcare is a defensive sector with consistent demand")
        reasoning.append("📈 Aging population drives healthcare growth")
        recommendation = "BUY"
        confidence = "HIGH"
        
    # Technology companies analysis
    elif any(tech_word in name_lower for tech_word in ['tech', 'software', 'digital', 'cyber', 'data', 'ai', 'automation']):
        key_factors["Sector"] = "Technology - High growth potential"
        reasoning.append("✅ Technology sector shows strong growth prospects")
        reasoning.append("⚡ Digital transformation trend supports tech companies")
        if "ai" in name_lower or "automation" in name_lower:
            recommendation = "BUY"
            confidence = "HIGH"
            reasoning.append("🚀 AI/Automation is a high-growth sector")
        
    # Engineering/Infrastructure
    elif any(infra_word in name_lower for infra_word in ['engineering', 'construction', 'infrastructure', 'projects']):
        key_factors["Sector"] = "Infrastructure/Engineering - Government spending dependent"
        reasoning.append("⚠️ Infrastructure sector dependent on government policies")
        reasoning.append("📊 Check order book and project pipeline before investing")
        risk_level = "MEDIUM"
        
    # Manufacturing/Industrial
    elif any(mfg_word in name_lower for mfg_word in ['manufacturing', 'industrial', 'auto', 'steel', 'chemical']):
        key_factors["Sector"] = "Manufacturing - Cyclical business"
        reasoning.append("📊 Manufacturing is cyclical - depends on economic conditions")
        reasoning.append("⚠️ Monitor raw material costs and demand cycles")
        
    # Financial services
    elif any(fin_word in name_lower for fin_word in ['bank', 'finance', 'insurance', 'mutual', 'capital']):
        key_factors["Sector"] = "Financial Services - Regulatory dependent"
        reasoning.append("📋 Financial sector is heavily regulated")
        reasoning.append("💰 Interest rate environment affects profitability")
        
    # Retail/Consumer
    elif any(retail_word in name_lower for retail_word in ['retail', 'consumer', 'fashion', 'food', 'restaurant']):
        key_factors["Sector"] = "Consumer/Retail - Brand and location dependent"
        reasoning.append("🛍️ Retail success depends on brand strength and locations")
        reasoning.append("📱 E-commerce disruption affects traditional retail")
        
    # Real Estate
    elif any(re_word in name_lower for re_word in ['real estate', 'property', 'housing', 'land']):
        key_factors["Sector"] = "Real Estate - Interest rate sensitive"
        reasoning.append("🏠 Real estate is sensitive to interest rates")
        reasoning.append("⚠️ Regulatory changes can impact profitability")
        risk_level = "HIGH"
        
    # Small/SME companies analysis
    if any(sme_indicator in name_lower for sme_indicator in ['sme', 'small', 'micro']):
        key_factors["Company Size"] = "SME - Higher risk, higher potential returns"
        reasoning.append("⚠️ SME companies have higher risk due to smaller scale")
        reasoning.append("💡 Can offer higher returns if business model is strong")
        risk_level = "HIGH"
        if recommendation == "BUY":
            recommendation = "HOLD"
            
    # Price band analysis
    if price_band and price_band != "Price TBA":
        try:
            # Extract price range
            import re
            prices = re.findall(r'₹(\d+)', price_band.replace(',', ''))
            if len(prices) >= 2:
                min_price = int(prices[0])
                max_price = int(prices[-1])
                avg_price = (min_price + max_price) / 2
                
                key_factors["Price Analysis"] = f"₹{avg_price:.0f} average price"
                
                if avg_price < 100:
                    reasoning.append("💰 Low price point makes it accessible for retail investors")
                elif avg_price > 500:
                    reasoning.append("💸 High price point - suitable for larger investments")
                    
                # Valuation guidance
                if avg_price < 200:
                    reasoning.append("📊 Consider company fundamentals over price for small companies")
                    
        except Exception:
            pass
    
    # Listing timeline analysis
    if listing_date:
        key_factors["Listing"] = f"Lists on {listing_date}"
        reasoning.append("📅 Check market conditions near listing date")
        reasoning.append("⏰ First day performance can be volatile")
        
    # General investment advice
    reasoning.extend([
        "📖 Read the prospectus thoroughly before investing",
        "💼 Check company's business model and revenue streams",
        "🔍 Analyze peer companies and sector valuations",
        "📈 Consider your risk tolerance and investment goals"
    ])
    
    # Risk level adjustments
    if "STRONG" in recommendation:
        confidence = "HIGH"
    elif recommendation == "AVOID":
        risk_level = "VERY HIGH"
        
    return InvestmentAnalysis(
        recommendation=recommendation,
        confidence=confidence,
        reasoning=reasoning,
        risk_level=risk_level,
        investment_horizon=investment_horizon,
        key_factors=key_factors
    )


def get_market_sentiment() -> str:
    """Get general market sentiment advice."""
    return """
📊 CURRENT MARKET CONTEXT:
• Markets are experiencing mixed signals with selective buying
• IPO market sentiment depends on sector and company fundamentals  
• Quality companies with strong business models are preferred
• Avoid companies with high debt or unclear business models

💡 INVESTMENT STRATEGY:
• Diversify across sectors rather than putting all money in one IPO
• Consider your portfolio allocation - don't overweight IPOs
• Keep some cash ready for better opportunities
• Focus on long-term wealth creation over short-term gains
"""


def format_investment_email(now_date: date, ipos: List) -> Tuple[str, str]:
    """Format simple email with just IPO names and APPLY/AVOID guidance."""
    
    # Create subject line
    formatted_date = now_date.strftime("%d %b %Y")
    subject = f"IPO Alert • {formatted_date}"
    
    if not ipos:
        body = f"""No IPOs closing today ({formatted_date})

Market is quiet - good time to research upcoming opportunities.
"""
        return subject, body
    
    # Simple, clean email format
    lines = [f"IPOs closing today ({formatted_date}):\n"]
    
    for i, ipo in enumerate(ipos, 1):
        company_name = getattr(ipo, 'name', 'Unknown Company')
        price_band = getattr(ipo, 'price_band', 'Price TBA')
        
        # Get investment analysis
        analysis = analyze_ipo_investment(company_name, price_band)
        
        # Convert recommendation to simple APPLY/AVOID
        if analysis.recommendation in ["STRONG BUY", "BUY"]:
            action = "✅ APPLY"
        elif analysis.recommendation == "HOLD":
            action = "⚠️ RESEARCH"
        else:
            action = "❌ AVOID"
        
        lines.append(f"{i}. {company_name}")
        lines.append(f"   Price: {price_band}")
        lines.append(f"   Advice: {action}")
        lines.append("")
    
    lines.append("---")
    lines.append("Do your own research before investing.")
    
    body = "\n".join(lines)
    return subject, body
