"""Official API integrations for BSE and NSE with circuit breaker pattern."""
import asyncio
import logging
import time
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import aiohttp
import requests
from circuitbreaker import circuit

from ..database import DatabaseManager, IPOData, AuditLog
from ..cache import cache_manager, cache_ipo_data
from ..config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

@dataclass
class OfficialIPOData:
    """Standardized IPO data from official sources."""
    company_name: str
    symbol: str
    platform: str  # "Mainboard" or "SME"
    price_band: str
    min_price: Optional[float]
    max_price: Optional[float]
    lot_size: Optional[int]
    issue_size: Optional[float]  # in crores
    open_date: Optional[date]
    close_date: Optional[date]
    listing_date: Optional[date]
    sector: Optional[str]
    source: str  # "BSE" or "NSE"
    source_url: Optional[str]

class CircuitBreakerMixin:
    """Mixin for circuit breaker functionality."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        self.state = "CLOSED"

    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        # Open circuit after 5 failures
        if self.failure_count >= 5:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened for {self.service_name}")

    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            # Allow retry after 5 minutes
            if self.last_failure_time and (datetime.now() - self.last_failure_time).seconds > 300:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False

class BSEAPIClient(CircuitBreakerMixin):
    """Official BSE API client with circuit breaker."""

    def __init__(self):
        super().__init__("BSE_API")
        self.base_url = "https://api.bseindia.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IPO_Reminder/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    @circuit(failure_threshold=5, recovery_timeout=300, expected_exception=Exception)
    def get_ipo_data(self, target_date: date) -> List[OfficialIPOData]:
        """Get IPO data from BSE with circuit breaker protection."""
        if not self.can_execute():
            logger.warning("BSE API circuit breaker is OPEN, skipping request")
            return []

        try:
            # BSE IPO endpoint (this would be the actual API endpoint)
            url = f"{self.base_url}/corporates/list_scrips.aspx"

            params = {
                'expandable': '1',
                'date': target_date.strftime('%Y-%m-%d')
            }

            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Parse BSE response (simplified - actual implementation would parse real API response)
            ipos = self._parse_bse_response(response.json() if response.headers.get('content-type', '').startswith('application/json') else {})

            self.record_success()
            logger.info(f"Successfully fetched {len(ipos)} IPOs from BSE API")
            return ipos

        except Exception as e:
            self.record_failure()
            logger.error(f"BSE API request failed: {e}")
            return []

    def _parse_bse_response(self, data: Dict[str, Any]) -> List[OfficialIPOData]:
        """Parse BSE API response."""
        ipos = []

        # This is a placeholder - actual implementation would parse real BSE API response
        # For now, return empty list as BSE doesn't have a public IPO API
        return ipos

class NSEAPIClient(CircuitBreakerMixin):
    """Official NSE API client with circuit breaker."""

    def __init__(self):
        super().__init__("NSE_API")
        self.base_url = "https://www.nseindia.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IPO_Reminder/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

    @circuit(failure_threshold=5, recovery_timeout=300, expected_exception=Exception)
    def get_ipo_data(self, target_date: date) -> List[OfficialIPOData]:
        """Get IPO data from NSE with circuit breaker protection."""
        if not self.can_execute():
            logger.warning("NSE API circuit breaker is OPEN, skipping request")
            return []

        try:
            # NSE IPO endpoint
            url = f"{self.base_url}/ipo-master"

            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            ipos = self._parse_nse_response(response.json())

            # Filter for target date
            closing_today = [ipo for ipo in ipos if ipo.close_date == target_date]

            self.record_success()
            logger.info(f"Successfully fetched {len(closing_today)} IPOs from NSE API")
            return closing_today

        except Exception as e:
            self.record_failure()
            logger.error(f"NSE API request failed: {e}")
            return []

    def _parse_nse_response(self, data: Dict[str, Any]) -> List[OfficialIPOData]:
        """Parse NSE API response."""
        ipos = []

        try:
            # NSE API response structure (simplified)
            if 'data' in data:
                for item in data['data']:
                    ipo = OfficialIPOData(
                        company_name=item.get('companyName', ''),
                        symbol=item.get('symbol', ''),
                        platform="Mainboard",  # NSE has both, but this is simplified
                        price_band=item.get('priceBand', ''),
                        min_price=float(item.get('minPrice', 0)) if item.get('minPrice') else None,
                        max_price=float(item.get('maxPrice', 0)) if item.get('maxPrice') else None,
                        lot_size=int(item.get('lotSize', 0)) if item.get('lotSize') else None,
                        issue_size=float(item.get('issueSize', 0)) if item.get('issueSize') else None,
                        open_date=self._parse_date(item.get('openDate')),
                        close_date=self._parse_date(item.get('closeDate')),
                        listing_date=self._parse_date(item.get('listingDate')),
                        sector=item.get('sector'),
                        source="NSE",
                        source_url=f"https://www.nseindia.com/get-quotes/equity?symbol={item.get('symbol', '')}"
                    )
                    ipos.append(ipo)

        except Exception as e:
            logger.error(f"Error parsing NSE response: {e}")

        return ipos

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string from NSE API."""
        if not date_str:
            return None

        try:
            # NSE date format: "21-Sep-2023"
            return datetime.strptime(date_str, '%d-%b-%Y').date()
        except Exception:
            return None

class OfficialAPIManager:
    """Manager for official API integrations with caching and fallbacks."""

    def __init__(self):
        self.bse_client = BSEAPIClient()
        self.nse_client = NSEAPIClient()

    @cache_ipo_data(ttl_seconds=1800)  # Cache for 30 minutes
    def get_official_ipos(self, target_date: date) -> List[OfficialIPOData]:
        """Get IPO data from official sources with caching."""
        all_ipos = []

        # Try NSE first (more reliable)
        nse_ipos = self.nse_client.get_ipo_data(target_date)
        all_ipos.extend(nse_ipos)

        # Try BSE as backup
        if not all_ipos or len(all_ipos) < 2:  # If NSE fails or returns few results
            bse_ipos = self.bse_client.get_ipo_data(target_date)
            all_ipos.extend(bse_ipos)

        # Remove duplicates based on company name
        unique_ipos = self._remove_duplicates(all_ipos)

        logger.info(f"Retrieved {len(unique_ipos)} unique IPOs from official APIs")
        return unique_ipos

    def _remove_duplicates(self, ipos: List[OfficialIPOData]) -> List[OfficialIPOData]:
        """Remove duplicate IPOs based on company name."""
        seen = set()
        unique_ipos = []

        for ipo in ipos:
            normalized_name = ipo.company_name.lower().strip()
            if normalized_name not in seen and normalized_name:
                seen.add(normalized_name)
                unique_ipos.append(ipo)

        return unique_ipos

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all API clients."""
        return {
            'bse_api': {
                'state': self.bse_client.state,
                'failure_count': self.bse_client.failure_count,
                'last_failure': self.bse_client.last_failure_time.isoformat() if self.bse_client.last_failure_time else None,
                'last_success': self.bse_client.last_success_time.isoformat() if self.bse_client.last_success_time else None
            },
            'nse_api': {
                'state': self.nse_client.state,
                'failure_count': self.nse_client.failure_count,
                'last_failure': self.nse_client.last_failure_time.isoformat() if self.nse_client.last_failure_time else None,
                'last_success': self.nse_client.last_success_time.isoformat() if self.nse_client.last_success_time else None
            }
        }

    async def get_official_ipos_async(self, target_date: date) -> List[OfficialIPOData]:
        """Async version for better performance."""
        # This would implement async HTTP requests for better performance
        # For now, delegate to sync version
        return self.get_official_ipos(target_date)

# Global instance
official_api_manager = OfficialAPIManager()

def get_official_ipos(target_date: date) -> List[OfficialIPOData]:
    """Convenience function to get official IPO data."""
    return official_api_manager.get_official_ipos(target_date)
