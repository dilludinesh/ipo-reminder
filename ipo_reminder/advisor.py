"""Personal IPO Investment Advisor - Intelligent recommendation engine."""
import logging
import re
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .sources.chittorgarh import IPOInfo

logger = logging.getLogger(__name__)

@dataclass
class IPORecommendation:
    """IPO recommendation with detailed analysis."""
    ipo: IPOInfo
    recommendation: str  # STRONG BUY, BUY, APPLY, NEUTRAL, AVOID
    confidence: float    # 0.0 to 1.0
    reasoning: List[str]
    risk_level: str     # LOW, MEDIUM, HIGH
    investment_amount: str  # Suggested amount
    key_factors: Dict[str, str]

class PersonalIPOAdvisor:
    """Intelligent IPO advisor for personal investment decisions."""
    
    def __init__(self):
        # Personal investment criteria - customize these for Dinesh
        self.criteria = {
            'preferred_sectors': [
                'technology', 'fintech', 'healthcare', 'pharmaceuticals',
                'renewable energy', 'electric vehicles', 'infrastructure',
                'banking', 'insurance', 'consumer goods'
            ],
            'avoid_sectors': [
                'tobacco', 'alcohol', 'gambling', 'mining', 'coal'
            ],
            'min_issue_size_cr': 50,  # Minimum issue size in crores
            'max_issue_size_cr': 5000,  # Maximum for risk management
            'preferred_price_range': (100, 2000),  # Price band preference
            'risk_tolerance': 'MEDIUM',  # LOW, MEDIUM, HIGH
            'investment_horizon': 'LONG_TERM',  # SHORT_TERM, MEDIUM_TERM, LONG_TERM
            'max_investment_per_ipo': 50000  # Maximum investment amount
        }
        
    def analyze_ipo(self, ipo: IPOInfo) -> IPORecommendation:
        """Provide personalized IPO recommendation."""
        logger.info(f"Analyzing IPO: {ipo.name}")
        
        recommendation = "NEUTRAL"
        confidence = 0.5
        reasoning = []
        risk_level = "MEDIUM"
        investment_amount = "₹10,000-25,000"
        key_factors = {}
        
        # Analyze company name and sector
        sector_score, sector_reasoning = self._analyze_sector(ipo.name)
        reasoning.extend(sector_reasoning)
        
        # Analyze issue size
        size_score, size_reasoning = self._analyze_issue_size(ipo.issue_size)
        reasoning.extend(size_reasoning)
        
        # Analyze price band
        price_score, price_reasoning = self._analyze_price_band(ipo.price_band)
        reasoning.extend(price_reasoning)
        
        # Analyze platform (Mainboard vs SME)
        platform_score, platform_reasoning = self._analyze_platform(ipo.name)
        reasoning.extend(platform_reasoning)
        
        # Calculate overall score
        overall_score = (sector_score * 0.4 + size_score * 0.2 + 
                        price_score * 0.2 + platform_score * 0.2)
        
        # Determine recommendation
        if overall_score >= 0.8:
            recommendation = "STRONG BUY"
            confidence = min(0.95, overall_score)
            investment_amount = "₹25,000-50,000"
            risk_level = "MEDIUM"
        elif overall_score >= 0.65:
            recommendation = "BUY"
            confidence = overall_score
            investment_amount = "₹15,000-30,000"
            risk_level = "MEDIUM"
        elif overall_score >= 0.5:
            recommendation = "APPLY"
            confidence = overall_score
            investment_amount = "₹10,000-20,000"
            risk_level = "MEDIUM"
        elif overall_score >= 0.3:
            recommendation = "NEUTRAL"
            confidence = overall_score
            investment_amount = "₹5,000-10,000"
            risk_level = "MEDIUM-HIGH"
        else:
            recommendation = "AVOID"
            confidence = 1.0 - overall_score
            investment_amount = "₹0 (Skip this IPO)"
            risk_level = "HIGH"
        
        # Add personalized insights
        key_factors = {
            'sector_fit': f"{sector_score:.1f}/1.0",
            'size_appropriateness': f"{size_score:.1f}/1.0",
            'price_attractiveness': f"{price_score:.1f}/1.0",
            'platform_preference': f"{platform_score:.1f}/1.0",
            'overall_score': f"{overall_score:.2f}/1.0"
        }
        
        return IPORecommendation(
            ipo=ipo,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            risk_level=risk_level,
            investment_amount=investment_amount,
            key_factors=key_factors
        )
    
    def _analyze_sector(self, company_name: str) -> Tuple[float, List[str]]:
        """Analyze sector alignment with personal preferences."""
        name_lower = company_name.lower()
        reasoning = []
        score = 0.5  # neutral baseline
        
        # Check preferred sectors
        for sector in self.criteria['preferred_sectors']:
            if any(keyword in name_lower for keyword in self._get_sector_keywords(sector)):
                score = 0.8
                reasoning.append(f"✅ {sector.title()} sector aligns with your investment preferences")
                break
        
        # Check sectors to avoid
        for sector in self.criteria['avoid_sectors']:
            if any(keyword in name_lower for keyword in self._get_sector_keywords(sector)):
                score = 0.2
                reasoning.append(f"❌ {sector.title()} sector - consider avoiding based on your criteria")
                break
        
        # Special tech/fintech bonus
        if any(word in name_lower for word in ['tech', 'digital', 'software', 'fintech', 'ai', 'data']):
            score = min(1.0, score + 0.2)
            reasoning.append("🚀 Technology company - strong growth potential")
        
        if not reasoning:
            reasoning.append("ℹ️ Sector analysis: Neutral - no strong preference indicated")
        
        return score, reasoning
    
    def _get_sector_keywords(self, sector: str) -> List[str]:
        """Get keywords for sector identification."""
        keyword_map = {
            'technology': ['tech', 'software', 'digital', 'ai', 'data', 'cyber', 'cloud'],
            'fintech': ['fintech', 'financial tech', 'payments', 'digital banking'],
            'healthcare': ['health', 'medical', 'hospital', 'pharmaceutical', 'biotech'],
            'pharmaceuticals': ['pharma', 'pharmaceutical', 'drug', 'medicine'],
            'renewable energy': ['solar', 'wind', 'renewable', 'green energy', 'clean energy'],
            'electric vehicles': ['electric', 'ev', 'battery', 'automotive'],
            'infrastructure': ['infrastructure', 'construction', 'engineering', 'roads'],
            'banking': ['bank', 'banking', 'financial services'],
            'insurance': ['insurance', 'life insurance', 'general insurance'],
            'consumer goods': ['consumer', 'retail', 'fmcg', 'food', 'beverage'],
            'tobacco': ['tobacco', 'cigarette', 'smoking'],
            'alcohol': ['alcohol', 'beer', 'liquor', 'brewery'],
            'gambling': ['gaming', 'casino', 'betting'],
            'mining': ['mining', 'coal', 'mineral', 'extraction'],
            'coal': ['coal', 'thermal']
        }
        return keyword_map.get(sector, [sector])
    
    def _analyze_issue_size(self, issue_size: str) -> Tuple[float, List[str]]:
        """Analyze issue size appropriateness."""
        if not issue_size:
            return 0.5, ["ℹ️ Issue size not available"]
        
        reasoning = []
        score = 0.5
        
        # Extract number from issue size
        size_match = re.search(r'([\d,]+)', issue_size.replace('₹', '').replace(',', ''))
        if size_match:
            try:
                size_cr = float(size_match.group(1))
                
                if 'lakh' in issue_size.lower():
                    size_cr = size_cr / 100  # Convert lakhs to crores
                
                if self.criteria['min_issue_size_cr'] <= size_cr <= self.criteria['max_issue_size_cr']:
                    score = 0.8
                    reasoning.append(f"✅ Issue size ₹{size_cr:.0f} Cr is appropriate for your portfolio")
                elif size_cr < self.criteria['min_issue_size_cr']:
                    score = 0.4
                    reasoning.append(f"⚠️ Small issue size ₹{size_cr:.0f} Cr - higher risk but potential upside")
                else:
                    score = 0.3
                    reasoning.append(f"⚠️ Large issue size ₹{size_cr:.0f} Cr - may limit listing gains")
                    
            except ValueError:
                reasoning.append("ℹ️ Could not parse issue size for analysis")
        else:
            reasoning.append("ℹ️ Issue size format not recognized")
        
        return score, reasoning
    
    def _analyze_price_band(self, price_band: str) -> Tuple[float, List[str]]:
        """Analyze price band attractiveness."""
        if not price_band:
            return 0.5, ["ℹ️ Price band not available"]
        
        reasoning = []
        score = 0.5
        
        # Extract price range
        price_match = re.search(r'₹?\s*(\d+)[-–]\s*₹?\s*(\d+)', price_band)
        if price_match:
            try:
                min_price = int(price_match.group(1))
                max_price = int(price_match.group(2))
                avg_price = (min_price + max_price) / 2
                
                pref_min, pref_max = self.criteria['preferred_price_range']
                
                if pref_min <= avg_price <= pref_max:
                    score = 0.8
                    reasoning.append(f"✅ Price range ₹{min_price}-{max_price} is in your preferred range")
                elif avg_price < pref_min:
                    score = 0.6
                    reasoning.append(f"💰 Lower price ₹{min_price}-{max_price} - good value but verify quality")
                else:
                    score = 0.4
                    reasoning.append(f"💸 Higher price ₹{min_price}-{max_price} - ensure strong fundamentals")
                    
            except ValueError:
                reasoning.append("ℹ️ Could not parse price band for analysis")
        else:
            reasoning.append("ℹ️ Price band format not recognized")
        
        return score, reasoning
    
    def _analyze_platform(self, company_name: str) -> Tuple[float, List[str]]:
        """Analyze listing platform (Mainboard vs SME)."""
        reasoning = []
        
        if '(SME)' in company_name or '(SME Emerge)' in company_name:
            score = 0.6
            reasoning.append("🏢 SME IPO - Higher risk but potential for significant returns")
            reasoning.append("⚠️ SME platform has lower liquidity - plan for longer holding period")
        else:
            score = 0.8
            reasoning.append("📈 Mainboard IPO - Better liquidity and institutional participation")
            reasoning.append("✅ Mainboard listing provides better exit options")
        
        return score, reasoning

def get_personalized_recommendations(ipos: List[IPOInfo]) -> List[IPORecommendation]:
    """Get personalized IPO recommendations for Dinesh."""
    advisor = PersonalIPOAdvisor()
    recommendations = []
    
    for ipo in ipos:
        recommendation = advisor.analyze_ipo(ipo)
        recommendations.append(recommendation)
    
    # Sort by recommendation strength
    recommendation_order = {
        'STRONG BUY': 5,
        'BUY': 4,
        'APPLY': 3,
        'NEUTRAL': 2,
        'AVOID': 1
    }
    
    recommendations.sort(key=lambda x: (
        recommendation_order.get(x.recommendation, 0),
        x.confidence
    ), reverse=True)
    
    return recommendations
