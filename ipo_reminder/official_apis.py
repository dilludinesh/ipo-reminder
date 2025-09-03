"""
Official API integrations for BSE and NSE with circuit breaker pattern.

This module provides robust API clients for BSE and NSE with the following features:
- Circuit breaker pattern to prevent cascading failures
- Exponential backoff with jitter for retries
- Comprehensive error handling and logging
- Request timeouts and connection pooling
- Caching of responses
"""
import asyncio
import logging
import random
import time
from datetime import date, datetime, timedelta
from functools import wraps
from typing import List, Optional, Dict, Any, Tuple, Callable, TypeVar, Type, cast
from dataclasses import dataclass
import aiohttp
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryCallState
)

from database import DatabaseManager, IPOData, AuditLog
from cache import cache_manager, cache_ipo_data
from config import (
    BSE_API_KEY, BSE_API_BASE_URL, BSE_API_TIMEOUT,
    NSE_API_KEY, NSE_API_BASE_URL, NSE_API_TIMEOUT,
    CIRCUIT_BREAKER_FAILURE_THRESHOLD, CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS, MAX_CONCURRENT_API_REQUESTS,
    BSE_API_RATE_LIMIT, NSE_API_RATE_LIMIT
)
from rate_limiting import (
    RateLimiter, CircuitBreaker, RateLimitExceeded, CircuitOpenError, Bulkhead,
    RateLimitConfig, CircuitBreakerConfig
)

# Type variable for generic function wrapping
F = TypeVar('F', bound=Callable[..., Any])

# Configure logging for tenacity
logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_RETRY_CONFIG = {
    'stop': stop_after_attempt(3),
    'wait': wait_exponential(multiplier=1, min=1, max=10),  # Exponential backoff with jitter
    'retry': retry_if_exception_type(
        (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError)
    ),
    'before_sleep': before_sleep_log(logger, logging.WARNING),
    'reraise': True
}

def async_retry(**retry_kwargs: Any) -> Callable[[F], F]:
    """
    Decorator that adds retry logic to async functions with configurable backoff.
    
    Args:
        **retry_kwargs: Retry configuration parameters
    """
    def decorator(f: F) -> F:
        @wraps(f)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            retry_config = {**DEFAULT_RETRY_CONFIG, **retry_kwargs}
            
            for attempt in range(1, retry_config['stop'].max_attempt_number + 1):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if not retry_config['retry'](e):
                        raise
                    
                    # Calculate wait time with jitter
                    wait_time = retry_config['wait'](RetryCallState(attempt_number=attempt, outcome=last_exception))
                    jitter = wait_time * 0.1 * random.random()  # Add ±10% jitter
                    wait_time = min(wait_time + jitter, retry_config.get('max_wait', 30))
                    
                    # Log the retry
                    retry_config['before_sleep'](None, None, (type(e), e, None), 0)
                    
                    # Wait before retry
                    await asyncio.sleep(wait_time)
            
            # If we've exhausted all retries
            raise last_exception  # type: ignore
            
        return cast(F, wrapped)
    return decorator

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

class BSEAPIClient:
    """
    Official BSE API client with rate limiting and circuit breaking.
    
    Features:
    - Token bucket rate limiting
    - Circuit breaker pattern
    - Automatic retries with exponential backoff
    - Connection pooling
    - Comprehensive error handling and logging
    """
    
    def __init__(self):
        self.base_url = BSE_API_BASE_URL
        self.timeout = aiohttp.ClientTimeout(total=BSE_API_TIMEOUT)
        self.session = None
        self.connector = aiohttp.TCPConnector(
            limit_per_host=10,
            ttl_dns_cache=300,
            enable_cleanup_closed=True
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'X-Bse-API-Key': BSE_API_KEY
        }
        
        # Initialize rate limiter and circuit breaker
        rate_limit_config = RateLimitConfig(
            requests_per_second=BSE_API_RATE_LIMIT / 60,  # Convert per minute to per second
            burst_capacity=BSE_API_RATE_LIMIT // 2,
            time_window=60
        )
        self.rate_limiter = RateLimiter(rate_limit_config)
        
        circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            half_open_max_requests=CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS
        )
        self.circuit_breaker = CircuitBreaker("BSE_API", circuit_breaker_config)
        self.bulkhead = Bulkhead(MAX_CONCURRENT_API_REQUESTS)

    async def initialize(self) -> None:
        """Initialize the BSE API client with aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers=self.headers,
                raise_for_status=True
            )
        logger.info("BSE API client initialized")

    async def shutdown(self) -> None:
        """Shutdown the BSE API client and clean up resources."""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            if self.connector and not self.connector.closed:
                await self.connector.close()
            logger.info("BSE API client shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down BSE API client: {e}", exc_info=True)
            raise

    async def get_status(self) -> Dict[str, Any]:
        """Get client status."""
        return {
            'service': 'BSE_API',
            'state': self.circuit_breaker.state,
            'failure_count': self.circuit_breaker.failure_count
        }

    @async_retry(stop=stop_after_attempt(3), reraise=True)
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting and circuit breaking.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for aiohttp request
            logger.error(
                f"Request to {url} failed: {str(e)}",
                extra={'url': url, 'error': str(e)},
                exc_info=True
            )
            raise
            
    async def fetch_ipos(self) -> List[Dict[str, Any]]:
        """Fetch IPO data from BSE with circuit breaker and retry logic.
        
        Returns:
            List of IPO data dictionaries
        """
        if not self.can_execute():
            status = self.get_status()
            logger.warning(
                f"Circuit breaker is {status['state']} for BSE API, skipping request. "
                f"Failures: {status['failure_count']}, "
                f"Last failure: {status.get('last_failure', 'never')}"
            )
            return []

        cache_key = f"bse_ipos_{date.today().isoformat()}"
        
        # Try to get from cache first
        try:
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.debug("Returning cached BSE IPO data")
                return cached
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        
        try:
            logger.info("Fetching IPO data from BSE API")
            
            # Make the API request with retry logic
            response = await self._make_request(
                'GET',
                '/api/ipo/GetIPOData',
                params={
                    'type': 'all',
                    'from': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'to': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d')
                }
            )
            
            # Process the response
            ipos = self._process_bse_response(response)
            
            # Cache the result for 1 hour
            try:
                await cache_manager.set(cache_key, ipos, ttl=3600)
            except Exception as e:
                logger.warning(f"Failed to cache BSE IPO data: {e}")
            

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

        return ipos
    
    def _parse_issue_size(self, size_str: str) -> Optional[float]:
        """Parse issue size string into float (in crores)."""
        if not size_str:
            return None
            
        try:
            # Handle formats like "1,234.56" or "1,234.56 Cr"
            size_str = size_str.lower().replace('cr', '').replace(',', '').strip()
            return float(size_str) if size_str else None
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string from NSE API."""
        if not date_str:
            return None

        try:
            # NSE date format: "21-Sep-2023"
            return datetime.strptime(str(date_str).strip(), '%d-%b-%Y').date()
        except (ValueError, TypeError):
            return None

class NSEAPIClient(CircuitBreakerMixin):
    """
    Official NSE API client with circuit breaker and retry logic.
    
    Features:
    - Circuit breaker pattern to prevent cascading failures
    - Automatic retries with exponential backoff
    - Request timeouts and connection pooling
    - Comprehensive error handling and logging
    - Cookie-based session management for NSE
    """

    def __init__(self):
        super().__init__("NSE_API")
        self.base_url = "https://www.nseindia.com/api"
        self.timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        self.session = None
        self.connector = aiohttp.TCPConnector(
            limit_per_host=10,  # Max connections per host
            ttl_dns_cache=300,  # 5 minutes DNS cache TTL
            enable_cleanup_closed=True
        )
        self.cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
        }

    async def initialize(self) -> None:
        """Initialize the NSE API client with aiohttp session and cookies."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers=self.headers,
                cookie_jar=self.cookie_jar,
                raise_for_status=True
            )
        
        # NSE requires cookies from the main page first
        try:
            # First get the main page to set cookies
            async with self.session.get('https://www.nseindia.com/') as response:
                if response.status != 200:
                    response.raise_for_status()
                
                # Ensure we have the required cookies
                cookies = self.cookie_jar.filter_cookies('https://www.nseindia.com')
                if 'nsit' not in cookies or 'nseappid' not in cookies:
                    logger.warning("Required NSE cookies not found")
                
                logger.info("NSE API client initialized with cookies")
                return
                
        except Exception as e:
            logger.error(f"Error initializing NSE API client: {e}", exc_info=True)
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Shutdown the NSE API client and clean up resources."""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            if self.connector and not self.connector.closed:
                await self.connector.close()
            logger.info("NSE API client shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down NSE API client: {e}", exc_info=True)
            raise

    @async_retry(stop=stop_after_attempt(3), reraise=True)
    async def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make an HTTP request with retry and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments to pass to aiohttp request
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            aiohttp.ClientError: For request/connection errors
            ValueError: For invalid responses
        """
        if not self.session or self.session.closed:
            await self.initialize()
            
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            # Ensure we have valid cookies
            cookies = self.cookie_jar.filter_cookies('https://www.nseindia.com')
            if 'nsit' not in cookies or 'nseappid' not in cookies:
                logger.warning("Refreshing NSE cookies")
                await self.initialize()
            
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 403 or 'Access Denied' in await response.text():
                    # Session likely expired, refresh cookies and retry once
                    logger.warning("NSE session expired, refreshing cookies")
                    await self.initialize()
                    async with self.session.request(method, url, **kwargs) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientResponseError as e:
            if e.status == 403:
                logger.warning("NSE API request forbidden, possible rate limiting")
            raise
            
        except aiohttp.ClientError as e:
            logger.error(
                f"Request to {url} failed: {str(e)}",
                extra={'url': url, 'error': str(e)},
                exc_info=True
            )
            raise

    async def get_ipo_data(self, target_date: date) -> List[OfficialIPOData]:
        """Fetch IPO data from NSE with circuit breaker and retry logic.
        
        Args:
            target_date: The target date to fetch IPOs for
            
        Returns:
            List of OfficialIPOData objects
        """
        if not self.can_execute():
            status = self.get_status()
            logger.warning(
                f"Circuit breaker is {status['state']} for NSE API, skipping request. "
                f"Failures: {status['failure_count']}, "
                f"Last failure: {status.get('last_failure', 'never')}"
            )
            return []

        cache_key = f"nse_ipos_{target_date.isoformat()}"
        
        # Try to get from cache first
        try:
            cached = await cache_manager.get(cache_key)
            if cached:
                logger.debug("Returning cached NSE IPO data")
                return [OfficialIPOData(**ipo) for ipo in cached]
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        
        try:
            logger.info("Fetching IPO data from NSE API")
            
            # Ensure we have a valid session
            if not self.session or self.session.closed:
                await self.initialize()
            
            # Make the API request with retry logic
            response = await self._make_request(
                'GET',
                '/ipo',
                headers={
                    **self.headers,
                    'Referer': 'https://www.nseindia.com/get-quotes/ipo'
                }
            )
            
            # Process the response
            ipos = self._process_nse_response(response, target_date)
            
            # Cache the result for 1 hour
            try:
                await cache_manager.set(cache_key, [ipo.__dict__ for ipo in ipos], ttl=3600)
            except Exception as e:
                logger.warning(f"Failed to cache NSE IPO data: {e}")
            
            self.record_success()
            logger.info(f"Successfully fetched {len(ipos)} IPOs from NSE API")
            return ipos
            
        except Exception as e:
            self.record_failure(e)
            logger.error(f"Failed to fetch IPOs from NSE: {e}", exc_info=True)
            return []
    
    def _process_nse_response(self, response: Dict[str, Any], target_date: date) -> List[OfficialIPOData]:
        """Process NSE API response into a list of standardized IPOs.
        
        Args:
            response: Raw API response from NSE
            target_date: The target date to filter IPOs for
            
        Returns:
            List of OfficialIPOData objects
        """
        if not response or not isinstance(response.get('data'), list):
            return []
            
        ipos = []
        for item in response['data']:
            try:
                # Skip withdrawn or cancelled IPOs
                if item.get('status') in ['Withdrawn', 'Cancelled']:
                    continue
                
                # Parse issue dates
                issue_open = self._parse_date(item.get('issueOpenDate'))
                issue_close = self._parse_date(item.get('issueCloseDate'))
                
                # Skip if not active on target date
                if issue_open and issue_close and not (issue_open <= target_date <= issue_close):
                    continue
                    
                ipo = OfficialIPOData(
                    company_name=item.get('companyName', '').strip(),
                    symbol=item.get('symbol', '').strip(),
                    platform='NSE',
                    price_band=item.get('priceRange', '').strip(),
                    min_price=self._parse_issue_size(item.get('minPrice')),
                    max_price=self._parse_issue_size(item.get('maxPrice')),
                    lot_size=int(item.get('lotSize', 0)),
                    issue_size=self._parse_issue_size(item.get('issueSize')),
                    open_date=issue_open,
                    close_date=issue_close,
                    listing_date=self._parse_date(item.get('listingDate')),
                    sector=item.get('industry'),
                    source='NSE',
                    source_url=f"https://www.nseindia.com/companies-listing/corporate-filings-ipo/{item.get('symbol', '').lower()}"
                )
                ipos.append(ipo)
                
            except (ValueError, AttributeError) as e:
                logger.warning(
                    f"Error processing NSE IPO data: {e}",
                    extra={'item': item, 'error': str(e)}
                )
                continue
                
        return ipos
    
    def _parse_issue_size(self, size_str: str) -> Optional[float]:
        """Parse issue size string into float (in crores)."""
        if not size_str:
            return None
            
        try:
            # Handle formats like "1,234.56" or "1,234.56 Cr"
            size_str = str(size_str).lower().replace('cr', '').replace(',', '').strip()
            return float(size_str) if size_str else None
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string from NSE API response."""
        if not date_str:
            return None
            
        try:
            # Try different date formats used by NSE
            for fmt in ('%d-%b-%Y', '%Y-%m-%d', '%d/%m/%Y'):
                try:
                    dt = datetime.strptime(str(date_str).strip(), fmt)
                    return dt.date()
                except ValueError:
                    continue
            return None
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
        all_ipos = []

        # Try NSE first (more reliable)
        nse_ipos = await self.nse_client.get_ipo_data(target_date)
        all_ipos.extend(nse_ipos)

        # Try BSE as backup
        if not all_ipos or len(all_ipos) < 2:  # If NSE fails or returns few results
            bse_ipos = await self.bse_client.get_ipo_data(target_date)
            all_ipos.extend(bse_ipos)

        # Remove duplicates based on company name
        unique_ipos = self._remove_duplicates(all_ipos)

        logger.info(f"Retrieved {len(unique_ipos)} unique IPOs from official APIs")
        return unique_ipos

# Global instance
official_api_manager = OfficialAPIManager()

def get_official_ipos(target_date: date) -> List[OfficialIPOData]:
    """Convenience function to get official IPO data."""
    return official_api_manager.get_official_ipos(target_date)
