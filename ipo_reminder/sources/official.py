"""Official IPO data sources - SEBI, BSE, NSE for maximum reliability."""
import logging
import re
import json
import time
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from ..config import REQUEST_TIMEOUT, USER_AGENT
from .chittorgarh import IPOInfo

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

class OfficialIPOScraper:
    """Scraper for official IPO sources with robust error handling."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def get_sebi_ipos(self) -> List[IPOInfo]:
        """Get IPO data from SEBI - most authoritative source."""
        logger.info("Fetching IPO data from SEBI...")
        
        try:
            # SEBI Public Issues pages - try multiple URLs
            urls = [
                "https://www.sebi.gov.in/reports-and-statistics/statistics/public-issues",
                "https://www.sebi.gov.in/sebiweb/home/list/1/1/1/1/All",
                "https://www.sebi.gov.in/sebiweb/home/list/5/33/0/1/Public-Issues"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    ipos = []
                    
                    # Look for IPO tables/cards in SEBI structure
                    tables = soup.find_all('table')
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) < 2:
                            continue
                            
                        # Check if this is an IPO-related table
                        header_text = ' '.join([th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])])
                        if not any(keyword in header_text for keyword in ['company', 'issue', 'public', 'ipo']):
                            continue
                        
                        for row in rows[1:]:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 3:
                                company_name = self._extract_company_name(cells[0].get_text().strip())
                                
                                if company_name and len(company_name) > 2:
                                    # Try to extract dates and other info from subsequent cells
                                    dates_info = self._extract_dates_from_cells(cells[1:])
                                    
                                    ipo = IPOInfo(
                                        name=company_name,
                                        detail_url=self._extract_link(cells[0]),
                                        gmp_url=None,
                                        open_date=dates_info.get('open_date'),
                                        close_date=dates_info.get('close_date'),
                                        price_band=dates_info.get('price_band'),
                                        lot_size=dates_info.get('lot_size'),
                                        issue_size=dates_info.get('issue_size')
                                    )
                                    ipos.append(ipo)
                    
                    if ipos:
                        logger.info(f"Found {len(ipos)} IPOs from SEBI ({url})")
                        return ipos
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue
            
            logger.info("No IPOs found from any SEBI URL")
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch SEBI IPOs: {e}")
            return []
    
    def get_bse_ipos(self) -> List[IPOInfo]:
        """Get IPO data from BSE - official exchange source (Mainboard + SME)."""
        logger.info("Fetching IPO data from BSE...")
        
        try:
            # BSE IPO section - including SME platform
            ipo_urls = [
                # Mainboard IPOs
                "https://www.bseindia.com/corporates/list_scrips.aspx?expandable=1",
                "https://www.bseindia.com/static/markets/PublicIssues/PubIssueMain.aspx",
                # SME Platform IPOs
                "https://www.bseindia.com/markets/equity/EQReports/SMEipo.aspx",
                "https://www.bseindia.com/corporates/SME_new_listing.aspx",
                "https://www.bseindia.com/static/markets/PublicIssues/SME_PubIssueMain.aspx"
            ]
            
            all_ipos = []
            
            for ipo_url in ipo_urls:
                try:
                    response = self.session.get(ipo_url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Determine if this is SME or Mainboard
                    is_sme = 'sme' in ipo_url.lower()
                    platform = "SME" if is_sme else "Mainboard"
                    
                    # Look for IPO tables
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) < 2:
                            continue
                            
                        for row in rows[1:]:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 3:
                                company_name = self._extract_company_name(cells[0].get_text().strip())
                                
                                if company_name and len(company_name) > 2:
                                    dates_info = self._extract_dates_from_cells(cells[1:])
                                    
                                    # Add platform information to company name
                                    enhanced_name = f"{company_name} ({platform})"
                                    
                                    ipo = IPOInfo(
                                        name=enhanced_name,
                                        detail_url=self._extract_link(cells[0]),
                                        gmp_url=None,
                                        open_date=dates_info.get('open_date'),
                                        close_date=dates_info.get('close_date'),
                                        price_band=dates_info.get('price_band'),
                                        lot_size=dates_info.get('lot_size'),
                                        issue_size=dates_info.get('issue_size')
                                    )
                                    all_ipos.append(ipo)
                
                except Exception as e:
                    logger.warning(f"Failed to fetch from {ipo_url}: {e}")
                    continue
            
            # Remove duplicates
            unique_ipos = self._remove_duplicates(all_ipos)
            logger.info(f"Found {len(unique_ipos)} unique IPOs from BSE (Mainboard + SME)")
            return unique_ipos
            
        except Exception as e:
            logger.error(f"Failed to fetch BSE IPOs: {e}")
            return []
    
    def get_nse_ipos(self) -> List[IPOInfo]:
        """Get IPO data from NSE - official exchange source (Mainboard + SME)."""
        logger.info("Fetching IPO data from NSE...")
        
        try:
            # NSE IPO pages - including SME/Emerge platform
            urls = [
                # Mainboard IPOs
                "https://www.nseindia.com/companies-listing/corporate-actions-public-issues",
                "https://www.nseindia.com/market-data/securities-available-for-trading",
                # SME/Emerge Platform
                "https://www.nseindia.com/companies-listing/sme-emerge",
                "https://www.nseindia.com/market-data/emerge-market"
            ]
            
            all_ipos = []
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Determine platform type
                    is_sme = any(term in url.lower() for term in ['sme', 'emerge'])
                    platform = "SME Emerge" if is_sme else "Mainboard"
                    
                    # NSE often uses div-based layouts
                    # Look for IPO-related content
                    ipo_divs = soup.find_all('div', class_=re.compile(r'.*ipo.*|.*issue.*|.*public.*', re.I))
                    
                    for div in ipo_divs:
                        text_content = div.get_text().strip()
                        if len(text_content) > 10 and 'ipo' in text_content.lower():
                            company_name = self._extract_company_from_text(text_content)
                            if company_name:
                                # Add platform information
                                enhanced_name = f"{company_name} ({platform})"
                                
                                ipo = IPOInfo(
                                    name=enhanced_name,
                                    detail_url=self._extract_link(div),
                                    gmp_url=None,
                                    open_date=None,
                                    close_date=None
                                )
                                all_ipos.append(ipo)
                
                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue
            
            # Also try to get structured data from NSE API endpoints
            api_ipos = self._get_nse_api_data()
            all_ipos.extend(api_ipos)
            
            unique_ipos = self._remove_duplicates(all_ipos)
            logger.info(f"Found {len(unique_ipos)} unique IPOs from NSE (Mainboard + SME)")
            return unique_ipos
            
        except Exception as e:
            logger.error(f"Failed to fetch NSE IPOs: {e}")
            return []
    
    def _get_nse_api_data(self) -> List[IPOInfo]:
        """Try to get data from NSE API endpoints (Mainboard + SME)."""
        try:
            # NSE sometimes has API endpoints for IPO data
            api_urls = [
                # Mainboard APIs
                "https://www.nseindia.com/api/ipo-current-issues",
                "https://www.nseindia.com/api/public-issues",
                # SME/Emerge APIs
                "https://www.nseindia.com/api/emerge-ipo",
                "https://www.nseindia.com/api/sme-issues"
            ]
            
            ipos = []
            for api_url in api_urls:
                try:
                    response = self.session.get(api_url, timeout=REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Determine platform type
                        is_sme = any(term in api_url.lower() for term in ['sme', 'emerge'])
                        platform = "SME Emerge" if is_sme else "Mainboard"
                        
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'name' in item:
                                    company_name = item.get('name', '')
                                    enhanced_name = f"{company_name} ({platform})"
                                    
                                    ipo = IPOInfo(
                                        name=enhanced_name,
                                        detail_url=None,
                                        gmp_url=None,
                                        open_date=self._parse_date(item.get('openDate')),
                                        close_date=self._parse_date(item.get('closeDate')),
                                        price_band=item.get('priceBand'),
                                        lot_size=item.get('lotSize'),
                                        issue_size=item.get('issueSize')
                                    )
                                    ipos.append(ipo)
                except:
                    continue
            
            return ipos
            
        except Exception as e:
            logger.debug(f"NSE API fetch failed: {e}")
            return []
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract and clean company name from text."""
        if not text:
            return None
            
        # Clean the text
        text = text.strip()
        
        # Remove common prefixes/suffixes
        text = re.sub(r'^(IPO|Public Issue|Issue)\s*[-:]?\s*', '', text, flags=re.I)
        text = re.sub(r'\s*(IPO|Public Issue|Ltd\.?|Limited|Private|Pvt\.?)?\s*$', '', text, flags=re.I)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Validate
        if len(text) < 3 or len(text) > 100:
            return None
            
        return text
    
    def _extract_company_from_text(self, text: str) -> Optional[str]:
        """Extract company name from longer text content."""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.lower().startswith(('date', 'open', 'close', 'price', 'size')):
                company = self._extract_company_name(line)
                if company:
                    return company
        return None
    
    def _extract_dates_from_cells(self, cells) -> Dict[str, Any]:
        """Extract dates and other info from table cells."""
        info = {}
        
        for cell in cells:
            text = cell.get_text().strip()
            
            # Try to extract dates
            date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
            if date_match:
                date_obj = self._parse_date(date_match.group())
                if date_obj:
                    if 'open' in text.lower():
                        info['open_date'] = date_obj
                    elif 'close' in text.lower():
                        info['close_date'] = date_obj
            
            # Try to extract price band
            price_match = re.search(r'₹\s*\d+[-–]\d+', text)
            if price_match:
                info['price_band'] = price_match.group()
            
            # Try to extract lot size
            lot_match = re.search(r'(\d+)\s*(shares?|lots?)', text, re.I)
            if lot_match:
                info['lot_size'] = lot_match.group(1)
            
            # Try to extract issue size
            size_match = re.search(r'₹\s*\d+(?:\.\d+)?\s*(cr|crore|million)', text, re.I)
            if size_match:
                info['issue_size'] = size_match.group()
        
        return info
    
    def _extract_link(self, element) -> Optional[str]:
        """Extract URL from element."""
        try:
            link = element.find('a')
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"https://www.sebi.gov.in{href}"
        except:
            pass
        return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        if not date_str:
            return None
            
        try:
            # Try various date formats
            for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y']:
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
            
            # Try dateutil parser as fallback
            parsed = dateparser.parse(date_str)
            if parsed:
                return parsed.date()
                
        except Exception as e:
            logger.debug(f"Date parsing failed for '{date_str}': {e}")
        
        return None
    
    def _remove_duplicates(self, ipos: List[IPOInfo]) -> List[IPOInfo]:
        """Remove duplicate IPOs based on company name."""
        seen = set()
        unique_ipos = []
        
        for ipo in ipos:
            # Normalize name for comparison
            normalized_name = re.sub(r'[^\w\s]', '', ipo.name.lower()).strip()
            if normalized_name not in seen:
                seen.add(normalized_name)
                unique_ipos.append(ipo)
        
        return unique_ipos


def get_official_ipos(target_date: date) -> List[IPOInfo]:
    """
    Get IPO data from official sources with robust fallback chain.
    
    Priority order:
    1. SEBI (most authoritative)
    2. BSE (official exchange)
    3. NSE (official exchange)
    """
    scraper = OfficialIPOScraper()
    all_ipos = []
    
    # Try SEBI first (most reliable)
    try:
        sebi_ipos = scraper.get_sebi_ipos()
        all_ipos.extend(sebi_ipos)
        if sebi_ipos:
            logger.info(f"Successfully fetched {len(sebi_ipos)} IPOs from SEBI")
    except Exception as e:
        logger.warning(f"SEBI fetch failed: {e}")
    
    # Add BSE data
    try:
        bse_ipos = scraper.get_bse_ipos()
        all_ipos.extend(bse_ipos)
        if bse_ipos:
            logger.info(f"Successfully fetched {len(bse_ipos)} IPOs from BSE")
    except Exception as e:
        logger.warning(f"BSE fetch failed: {e}")
    
    # Add NSE data
    try:
        nse_ipos = scraper.get_nse_ipos()
        all_ipos.extend(nse_ipos)
        if nse_ipos:
            logger.info(f"Successfully fetched {len(nse_ipos)} IPOs from NSE")
    except Exception as e:
        logger.warning(f"NSE fetch failed: {e}")
    
    # Remove duplicates across all sources
    unique_ipos = scraper._remove_duplicates(all_ipos)
    
    # Filter for IPOs closing on target date
    closing_today = []
    for ipo in unique_ipos:
        if ipo.close_date == target_date:
            closing_today.append(ipo)
    
    logger.info(f"Found {len(closing_today)} IPOs closing on {target_date} from official sources")
    logger.info(f"Total unique IPOs found: {len(unique_ipos)}")
    
    return closing_today
