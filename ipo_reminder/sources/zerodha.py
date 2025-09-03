"""Scraper for Zerodha IPO data."""
import logging
import re
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from ipo_reminder.config import REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)

@dataclass
class ZerodhaIPO:
    """IPO information from Zerodha."""
    name: str
    symbol: str
    ipo_dates: str
    listing_date: str
    price_range: str
    platform: str  # "Mainboard" or "SME"
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    lot_size: Optional[int] = None


def get_zerodha_ipos() -> List[ZerodhaIPO]:
    """Fetch IPO data from Zerodha."""
    logger.info("Fetching IPO data from Zerodha...")
    
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        
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
            try:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        # Extract data from cells
                        name_cell = cells[1] if len(cells) > 1 else cells[0]
                        
                        # Parse the HTML structure to get clean company name
                        company_name = ""
                        symbol = ""
                        
                        # Look for the ipo-name span which contains the actual company name
                        ipo_name_span = name_cell.find('span', class_='ipo-name')
                        if ipo_name_span:
                            company_name = ipo_name_span.get_text(strip=True)
                        
                        # Look for the ipo-symbol span
                        ipo_symbol_span = name_cell.find('span', class_='ipo-symbol')
                        if ipo_symbol_span:
                            # Extract just the symbol text, excluding SME type
                            symbol_text = ipo_symbol_span.get_text(strip=True)
                            # Check if it's an SME IPO
                            is_sme = 'SME' in symbol_text.upper()
                            # Remove SME from symbol if present
                            symbol = re.sub(r'\bSME\b', '', symbol_text, flags=re.I).strip()
                        else:
                            is_sme = False
                            symbol = ""
                        
                        # Determine platform
                        platform = "SME" if is_sme else "Mainboard"
                        
                        # Clean the company name
                        name = _clean_company_name(company_name)
                        
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
                            platform=platform,
                            open_date=open_date,
                            close_date=close_date
                        )
                        
                        ipos.append(ipo)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing IPO row: {e}")
                        continue
                    
            except Exception as e:
                logger.warning(f"Error processing table row: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(ipos)} IPOs from Zerodha")
        return ipos
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching Zerodha IPO data: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing Zerodha IPO data: {e}")
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


def _clean_company_name(name: str) -> str:
    """Clean and format company name for better display."""
    if not name:
        return name
    
    # Capitalize words properly (Title Case)
    name = name.title()
    
    # Handle special cases for company name formatting
    # Fix common capitalization issues
    name = re.sub(r'\bLtd\b', 'Ltd', name)
    name = re.sub(r'\bPvt\b', 'Pvt', name)
    name = re.sub(r'\bInc\b', 'Inc', name)
    name = re.sub(r'\bCorp\b', 'Corp', name)
    
    return name


def _extract_company_name_from_raw(raw_text: str) -> str:
    """Extract company name from raw concatenated text as fallback."""
    if not raw_text:
        return ""
    
    # Try to find patterns that look like company names
    # Look for title-case words that aren't all caps
    words = raw_text.split()
    company_words = []
    
    for word in words:
        # Skip if it's all caps and looks like a symbol
        if word.isupper() and len(word) <= 10:
            continue
        # Skip if it contains 'SME'
        if 'SME' in word.upper():
            continue
        company_words.append(word)
    
    return ' '.join(company_words) if company_words else raw_text


class ZerodhaScraper:
    """Scraper for Zerodha IPO data."""

    def get_upcoming_ipos(self) -> List[Dict[str, Any]]:
        """Get upcoming IPOs from Zerodha."""
        try:
            zerodha_ipos = get_zerodha_ipos()
            ipo_data = []

            for ipo in zerodha_ipos:
                ipo_dict = {
                    'company_name': ipo.name,
                    'ipo_open_date': ipo.open_date.isoformat() if ipo.open_date else None,
                    'ipo_close_date': ipo.close_date.isoformat() if ipo.close_date else None,
                    'price_range': ipo.price_range,
                    'lot_size': ipo.lot_size,
                    'platform': ipo.platform,
                    'source': 'zerodha'
                }
                ipo_data.append(ipo_dict)

            return ipo_data
        except Exception as e:
            logger.error(f"ZerodhaScraper error: {e}")
            return []
