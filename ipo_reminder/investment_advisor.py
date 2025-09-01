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
    """Format email with comprehensive investment advice."""
    
    # Create subject line
    day_name = now_date.strftime("%A")
    formatted_date = now_date.strftime("%d %b %Y")
    subject = f"IPO Investment Alert • {day_name}, {formatted_date}"
    
    if not ipos:
        body = f"""📊 IPO MARKET UPDATE - {formatted_date}

No IPOs closing today. Market is quiet.

💡 USE THIS TIME TO:
• Research upcoming IPOs in your pipeline
• Review your current portfolio allocation
• Study sector trends and market conditions
• Build cash reserves for quality opportunities

📈 INVESTMENT TIP:
Quality IPOs are rare. It's better to wait for the right opportunity than to invest in mediocre companies just because they're available.

---
⚠️ This is for educational purposes. Consult your financial advisor for personalized advice.
"""
        return subject, body
    
    # Build comprehensive investment email
    lines = [f"📊 IPO INVESTMENT ALERT - {formatted_date}"]
    lines.append(f"\n{len(ipos)} IPO(s) closing today - INVESTMENT ANALYSIS:\n")
    
    for i, ipo in enumerate(ipos, 1):
        company_name = getattr(ipo, 'name', 'Unknown Company')
        price_band = getattr(ipo, 'price_band', 'Price TBA')
        listing_date = getattr(ipo, 'listing_date', None) or \
                      getattr(ipo, 'ipo_dates', None) or "TBA"
        
        # Get investment analysis
        analysis = analyze_ipo_investment(company_name, price_band, listing_date=listing_date)
        
        lines.append(f"{'='*60}")
        lines.append(f"{i}. 🏢 {company_name}")
        lines.append(f"💰 Price: {price_band}")
        lines.append(f"📅 Listing: {listing_date}")
        lines.append("")
        
        # Investment recommendation
        rec_emoji = {
            "STRONG BUY": "🚀",
            "BUY": "✅", 
            "HOLD": "⚠️",
            "AVOID": "❌",
            "STRONG AVOID": "🚫"
        }.get(analysis.recommendation, "📊")
        
        lines.append(f"{rec_emoji} RECOMMENDATION: {analysis.recommendation}")
        lines.append(f"🎯 Confidence: {analysis.confidence}")
        lines.append(f"⚡ Risk Level: {analysis.risk_level}")
        lines.append(f"📈 Investment Horizon: {analysis.investment_horizon.replace('_', ' ')}")
        lines.append("")
        
        # Key factors
        lines.append("🔍 KEY FACTORS:")
        for factor, description in analysis.key_factors.items():
            lines.append(f"  • {factor}: {description}")
        lines.append("")
        
        # Investment reasoning
        lines.append("💡 ANALYSIS:")
        for reason in analysis.reasoning[:8]:  # Limit to most important points
            lines.append(f"  {reason}")
        lines.append("")
        
        # Specific investment advice
        if analysis.recommendation in ["STRONG BUY", "BUY"]:
            lines.append("💰 INVESTMENT ADVICE:")
            lines.append("  • Consider for portfolio allocation")
            lines.append("  • Start with smaller position, can increase if performs well")
            lines.append("  • Good for long-term wealth creation")
        elif analysis.recommendation == "HOLD":
            lines.append("⚖️ INVESTMENT ADVICE:")
            lines.append("  • Suitable for moderate risk investors")
            lines.append("  • Research thoroughly before investing")
            lines.append("  • Consider waiting for better entry opportunities")
        else:
            lines.append("⛔ INVESTMENT ADVICE:")
            lines.append("  • High risk - avoid unless you're experienced")
            lines.append("  • Better opportunities likely available elsewhere")
            lines.append("  • Focus on quality companies instead")
        
        lines.append("")
    
    # Add market context
    lines.append(get_market_sentiment())
    
    # Add closing advice
    lines.append("""
📋 FINAL CHECKLIST BEFORE INVESTING:
□ Read the company's prospectus completely
□ Check company's debt levels and cash flow
□ Compare with listed peers in same sector  
□ Ensure this fits your risk profile
□ Don't invest more than you can afford to lose
□ Have a clear exit strategy

⚠️ DISCLAIMER: This analysis is for educational purposes only. Past performance doesn't guarantee future results. Please consult with a qualified financial advisor before making investment decisions.

🎯 Remember: It's better to miss a good opportunity than to lose money on a bad one!""")
    
    body = "\n".join(lines)
    return subject, body
