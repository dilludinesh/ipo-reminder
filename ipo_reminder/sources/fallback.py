"""Alternative IPO data sources when Chittorgarh fails."""
import logging
import re
import requests
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from ipo_reminder.config import REQUEST_TIMEOUT, USER_AGENT
from .chittorgarh import IPOInfo, _clean_text, _parse_date

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

def get_bse_ipos() -> List[IPOInfo]:
    """Try to get IPO data from BSE website."""
    try:
        # BSE IPO page
        url = "https://www.bseindia.com/corporates/list_scrips.aspx?expandable=1"
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for IPO tables
            ipos = []
            tables = soup.select('table')
            
            for table in tables:
                rows = table.select('tr')
                if len(rows) < 2:
                    continue
                    
                headers = [th.get_text().strip().lower() for th in rows[0].select('th, td')]
                
                # Check if this looks like an IPO table
                if not any('ipo' in h or 'company' in h for h in headers):
                    continue
                    
                for row in rows[1:]:
                    cells = [td.get_text().strip() for td in row.select('td')]
                    if len(cells) >= 3:
                        name = cells[0]
                        if name and len(name) > 3:  # Basic validation
                            ipo = IPOInfo(
                                name=name,
                                detail_url=None,
                                gmp_url=None,
                                open_date=None,
                                close_date=None
                            )
                            ipos.append(ipo)
            
            logger.info(f"Found {len(ipos)} IPOs from BSE")
            return ipos
            
    except Exception as e:
        logger.warning(f"Failed to fetch BSE IPOs: {e}")
    
    return []

def get_nse_ipos() -> List[IPOInfo]:
    """Try to get IPO data from NSE website."""
    try:
        # NSE IPO page
        url = "https://www.nseindia.com/companies-listing/corporate-actions-public-issues"
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for IPO data
            ipos = []
            # NSE often uses div structures
            ipo_divs = soup.select('div')
            
            for div in ipo_divs:
                text = div.get_text().strip()
                if 'ipo' in text.lower() and len(text) > 10:
                    # Try to extract company name
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.lower().startswith(('date', 'open', 'close', 'status')):
                            ipo = IPOInfo(
                                name=line,
                                detail_url=None,
                                gmp_url=None,
                                open_date=None,
                                close_date=None
                            )
                            ipos.append(ipo)
                            break
            
            logger.info(f"Found {len(ipos)} IPOs from NSE")
            return ipos
            
    except Exception as e:
        logger.warning(f"Failed to fetch NSE IPOs: {e}")
    
    return []

def get_fallback_ipos(target_date: date) -> List[IPOInfo]:
    """Get IPO data from alternative sources when main scraper fails."""
    
    logger.info("Trying alternative IPO data sources...")
    
    # Try other sources
    all_ipos = []
    
    # Try BSE
    bse_ipos = get_bse_ipos()
    all_ipos.extend(bse_ipos)
    
    # Try NSE
    nse_ipos = get_nse_ipos()
    all_ipos.extend(nse_ipos)
    
    # Filter for closing today
    closing_today = []
    for ipo in all_ipos:
        if ipo.close_date == target_date:
            closing_today.append(ipo)
    
    logger.info(f"Found {len(closing_today)} IPOs closing on {target_date} from alternative sources")
    return closing_today


class FallbackScraper:
    """Fallback scraper for IPO data."""

    def get_upcoming_ipos(self) -> List[Dict[str, Any]]:
        """Get upcoming IPOs from fallback sources."""
        try:
            from datetime import date as date_type
            today = date_type.today()
            fallback_ipos = get_fallback_ipos(today)
            ipo_data = []

            for ipo in fallback_ipos:
                ipo_dict = {
                    'company_name': ipo.name,
                    'ipo_open_date': ipo.open_date.isoformat() if ipo.open_date else None,
                    'ipo_close_date': ipo.close_date.isoformat() if ipo.close_date else None,
                    'price_range': ipo.price_band,
                    'lot_size': ipo.lot_size,
                    'platform': 'Mainboard',  # Default, could be enhanced
                    'source': 'fallback'
                }
                ipo_data.append(ipo_dict)

            return ipo_data
        except Exception as e:
            logger.error(f"FallbackScraper error: {e}")
            return []
