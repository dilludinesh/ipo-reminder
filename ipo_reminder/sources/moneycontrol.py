"""Moneycontrol IPO data source - reliable financial portal."""
import logging
import re
from datetime import datetime, date
from typing import List, Optional

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
    "Referer": "https://www.moneycontrol.com/"
}

def get_moneycontrol_ipos(target_date: date) -> List[IPOInfo]:
    """Get IPO data from Moneycontrol - reliable financial source."""
    logger.info("Fetching IPO data from Moneycontrol...")
    
    try:
        # Moneycontrol IPO section - including SME
        urls = [
            # Mainboard IPOs
            "https://www.moneycontrol.com/ipo/",
            "https://www.moneycontrol.com/news/ipo/",
            "https://www.moneycontrol.com/stocks/ipo/",
            # SME IPOs
            "https://www.moneycontrol.com/news/sme-ipo/",
            "https://www.moneycontrol.com/stocks/sme-ipo/"
        ]
        
        session = requests.Session()
        session.headers.update(HEADERS)
        
        all_ipos = []
        
        for url in urls:
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Determine platform type
                is_sme = 'sme' in url.lower()
                platform = "SME" if is_sme else "Mainboard"
                
                # Look for IPO tables and cards
                # Moneycontrol often uses structured tables
                tables = soup.find_all('table')
                for table in tables:
                    ipos = _parse_moneycontrol_table(table, target_date, platform)
                    all_ipos.extend(ipos)
                
                # Also look for IPO cards/divs
                ipo_containers = soup.find_all(['div', 'section'], class_=re.compile(r'.*ipo.*', re.I))
                for container in ipo_containers:
                    ipos = _parse_moneycontrol_container(container, target_date, platform)
                    all_ipos.extend(ipos)
                
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue
        
        # Remove duplicates
        unique_ipos = _remove_duplicates(all_ipos)
        
        # Filter for target date
        closing_today = [ipo for ipo in unique_ipos if ipo.close_date == target_date]
        
        logger.info(f"Found {len(closing_today)} IPOs closing on {target_date} from Moneycontrol")
        return closing_today
        
    except Exception as e:
        logger.error(f"Failed to fetch Moneycontrol IPOs: {e}")
        return []

def _parse_moneycontrol_table(table, target_date: date, platform: str = "Mainboard") -> List[IPOInfo]:
    """Parse IPO data from Moneycontrol table."""
    ipos = []
    
    try:
        rows = table.find_all('tr')
        if len(rows) < 2:
            return ipos
        
        # Check if this looks like an IPO table
        header_text = ' '.join([th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])])
        if not any(keyword in header_text for keyword in ['company', 'issue', 'ipo', 'open', 'close']):
            return ipos
        
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                # Extract company name from first cell
                company_name = _clean_company_name(cells[0].get_text().strip())
                
                if company_name and len(company_name) > 2:
                    # Add platform information to company name
                    enhanced_name = f"{company_name} ({platform})"
                    
                    # Extract other information
                    open_date = None
                    close_date = None
                    price_band = None
                    lot_size = None
                    issue_size = None
                    
                    for i, cell in enumerate(cells[1:], 1):
                        text = cell.get_text().strip()
                        
                        # Try to identify date columns
                        date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
                        if date_match:
                            parsed_date = _parse_date(date_match.group())
                            if parsed_date:
                                # Determine if it's open or close date based on position or context
                                if i == 1 or 'open' in header_text:
                                    open_date = parsed_date
                                elif i == 2 or 'close' in header_text:
                                    close_date = parsed_date
                        
                        # Try to extract price band
                        if '₹' in text and '-' in text:
                            price_band = text
                        
                        # Try to extract lot size
                        if re.search(r'\d+', text) and any(word in text.lower() for word in ['lot', 'share']):
                            lot_size = re.search(r'\d+', text).group()
                        
                        # Try to extract issue size
                        if '₹' in text and any(word in text.lower() for word in ['cr', 'crore', 'lakh']):
                            issue_size = text
                    
                    # Get detail URL if available
                    detail_url = None
                    link = cells[0].find('a')
                    if link and link.get('href'):
                        href = link.get('href')
                        if href.startswith('http'):
                            detail_url = href
                        elif href.startswith('/'):
                            detail_url = f"https://www.moneycontrol.com{href}"
                    
                    ipo = IPOInfo(
                        name=enhanced_name,
                        detail_url=detail_url,
                        gmp_url=None,
                        open_date=open_date,
                        close_date=close_date,
                        price_band=price_band,
                        lot_size=lot_size,
                        issue_size=issue_size
                    )
                    ipos.append(ipo)
    
    except Exception as e:
        logger.debug(f"Error parsing Moneycontrol table: {e}")
    
    return ipos

def _parse_moneycontrol_container(container, target_date: date, platform: str = "Mainboard") -> List[IPOInfo]:
    """Parse IPO data from Moneycontrol container/card."""
    ipos = []
    
    try:
        text_content = container.get_text()
        
        # Look for company names and dates
        # Moneycontrol often has structured content
        company_matches = re.findall(r'([A-Z][a-zA-Z\s&]+(?:Ltd|Limited|Inc|Corp))', text_content)
        
        for company_match in company_matches:
            company_name = _clean_company_name(company_match.strip())
            
            if company_name and len(company_name) > 2:
                # Add platform information
                enhanced_name = f"{company_name} ({platform})"
                
                # Try to find associated dates in the same container
                date_matches = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text_content)
                
                open_date = None
                close_date = None
                
                for date_str in date_matches:
                    parsed_date = _parse_date(date_str)
                    if parsed_date:
                        if not open_date:
                            open_date = parsed_date
                        elif not close_date:
                            close_date = parsed_date
                
                ipo = IPOInfo(
                    name=enhanced_name,
                    detail_url=None,
                    gmp_url=None,
                    open_date=open_date,
                    close_date=close_date
                )
                ipos.append(ipo)
    
    except Exception as e:
        logger.debug(f"Error parsing Moneycontrol container: {e}")
    
    return ipos

def _clean_company_name(name: str) -> Optional[str]:
    """Clean and validate company name."""
    if not name:
        return None
    
    # Remove common prefixes and suffixes
    name = re.sub(r'^(IPO|Issue):\s*', '', name, flags=re.I)
    name = re.sub(r'\s*(IPO|Issue|Ltd\.?|Limited|Private|Pvt\.?)?\s*$', '', name, flags=re.I)
    
    # Clean whitespace
    name = ' '.join(name.split())
    
    # Validate length
    if len(name) < 3 or len(name) > 100:
        return None
    
    return name

def _parse_date(date_str: str) -> Optional[date]:
    """Parse date string."""
    if not date_str:
        return None
    
    try:
        # Try common formats
        for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y']:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        # Try dateutil parser
        parsed = dateparser.parse(date_str)
        if parsed:
            return parsed.date()
    
    except Exception:
        pass
    
    return None

def _remove_duplicates(ipos: List[IPOInfo]) -> List[IPOInfo]:
    """Remove duplicate IPOs."""
    seen = set()
    unique_ipos = []
    
    for ipo in ipos:
        normalized_name = re.sub(r'[^\w\s]', '', ipo.name.lower()).strip()
        if normalized_name not in seen:
            seen.add(normalized_name)
            unique_ipos.append(ipo)
    
    return unique_ipos
