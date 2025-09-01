"""Scraper for Zerodha IPO data."""
import logging
import re
from datetime import datetime, date
from typing import List, Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from ..config import REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)

@dataclass
class ZerodhaIPO:
    """IPO information from Zerodha."""
    name: str
    symbol: str
    ipo_dates: str
    listing_date: str
    price_range: str
    open_date: Optional[date] = None
    close_date: Optional[date] = None


def get_zerodha_ipos() -> List[ZerodhaIPO]:
    """Fetch IPO data from Zerodha."""
    logger.info("Fetching IPO data from Zerodha...")
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get("https://zerodha.com/ipo", headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        # Find the IPO table
        tables = soup.find_all('table')
        if not tables:
            logger.warning("No tables found on Zerodha IPO page")
            return []
        
        table = tables[0]
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                try:
                    # Extract data from cells
                    name_cell = cells[1] if len(cells) > 1 else cells[0]
                    company_info = name_cell.get_text(strip=True)
                    
                    # Extract symbol and name
                    symbol_match = re.search(r'^([A-Z]+)(?:SME)?(.+)', company_info)
                    if symbol_match:
                        symbol = symbol_match.group(1)
                        name = symbol_match.group(2).strip()
                    else:
                        symbol = ""
                        name = company_info
                    
                    # Extract dates and other info
                    ipo_dates = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    listing_date = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    price_range = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                    
                    # Parse open and close dates from IPO dates string
                    open_date, close_date = _parse_ipo_dates(ipo_dates)
                    
                    ipo = ZerodhaIPO(
                        name=name,
                        symbol=symbol,
                        ipo_dates=ipo_dates,
                        listing_date=listing_date,
                        price_range=price_range,
                        open_date=open_date,
                        close_date=close_date
                    )
                    
                    ipos.append(ipo)
                    
                except Exception as e:
                    logger.warning(f"Error parsing IPO row: {e}")
                    continue
        
        logger.info(f"Successfully fetched {len(ipos)} IPOs from Zerodha")
        return ipos
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Zerodha IPO data: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing Zerodha IPO data: {e}")
        return []


def _parse_ipo_dates(date_str: str) -> tuple[Optional[date], Optional[date]]:
    """Parse IPO date range string to extract open and close dates."""
    if not date_str:
        return None, None
    
    try:
        # Handle formats like "28th Aug 2025 – 01st Sep 2025"
        if '–' in date_str or '-' in date_str:
            separator = '–' if '–' in date_str else '-'
            parts = date_str.split(separator)
            if len(parts) == 2:
                start_str = parts[0].strip()
                end_str = parts[1].strip()
                
                # Parse dates
                open_date = _parse_single_date(start_str)
                close_date = _parse_single_date(end_str)
                
                return open_date, close_date
        
        # Handle single date formats
        single_date = _parse_single_date(date_str)
        return single_date, single_date
        
    except Exception as e:
        logger.warning(f"Error parsing date string '{date_str}': {e}")
        return None, None


def _parse_single_date(date_str: str) -> Optional[date]:
    """Parse a single date string."""
    if not date_str:
        return None
    
    try:
        # Clean the date string
        cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Try to parse with dateutil
        parsed_date = dateparser.parse(cleaned, fuzzy=True)
        if parsed_date:
            return parsed_date.date()
        
        return None
        
    except Exception:
        return None


def get_zerodha_ipos_closing_today(target_date: date) -> List[ZerodhaIPO]:
    """Get IPOs closing on the specified date from Zerodha."""
    all_ipos = get_zerodha_ipos()
    closing_today = []
    
    for ipo in all_ipos:
        if ipo.close_date and ipo.close_date == target_date:
            closing_today.append(ipo)
    
    logger.info(f"Found {len(closing_today)} IPOs closing on {target_date} from Zerodha")
    return closing_today
