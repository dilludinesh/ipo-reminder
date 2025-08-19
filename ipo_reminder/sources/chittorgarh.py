"""Scraper for Chittorgarh IPO data."""
import logging
import re
import time
import random
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Set, Tuple

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import BASE_URL, REQUEST_TIMEOUT, REQUEST_RETRIES, REQUEST_DELAY, USER_AGENT

# Configure logging
logger = logging.getLogger(__name__)

# Constants
UPCOMING_PATH = "/ipo/ipo_calendar_timeline/"
ALT_UPCOMING_PATH = "/report/latest-ipo-gmp/56/"

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

# Set up a session with retry logic
session = requests.Session()
retry_strategy = Retry(
    total=REQUEST_RETRIES,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

@dataclass
class IPOInfo:
    """Class representing an IPO with all relevant information.
    
    Attributes:
        name: Name of the IPO
        detail_url: URL to the IPO details page
        gmp_url: URL to the GMP (Grey Market Premium) page
        open_date: Date when the IPO opens for subscription
        close_date: Date when the IPO closes
        price_band: Price range per share
        lot_size: Number of shares per lot
        issue_size: Total size of the IPO issue
        review_summary: Summary of the IPO review
        expert_recommendation: Expert's recommendation
        gmp_latest: Latest GMP value
        gmp_trend: Trend of GMP (rising/steady/falling/unknown)
        recommendation: Our recommendation (APPLY/AVOID/NEUTRAL)
        recommendation_reason: Reason for the recommendation
    """
    name: str
    detail_url: Optional[str]
    gmp_url: Optional[str]
    open_date: Optional[date]
    close_date: Optional[date]
    price_band: Optional[str] = None
    lot_size: Optional[str] = None
    issue_size: Optional[str] = None
    review_summary: Optional[str] = None
    expert_recommendation: Optional[str] = None
    gmp_latest: Optional[str] = None
    gmp_trend: Optional[str] = None  # rising/steady/falling/unknown
    recommendation: Optional[str] = None  # APPLY/AVOID/NEUTRAL
    recommendation_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert IPOInfo to a dictionary.
        
        Returns:
            Dictionary representation of the IPO
        """
        result = asdict(self)
        # Convert date objects to ISO format strings
        for field in ['open_date', 'close_date']:
            if field in result and result[field] is not None:
                result[field] = result[field].isoformat()
        return result
        
    def is_closing_today(self, today: Optional[date] = None) -> bool:
        """Check if the IPO is closing today.
        
        Args:
            today: Reference date (defaults to today)
            
        Returns:
            True if the IPO is closing today, False otherwise
        """
        if today is None:
            today = date.today()
        return self.close_date == today if self.close_date else False

def _clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()

def _parse_date(date_str: str) -> Optional[date]:
    """Parse date string into a date object.
    
    Args:
        date_str: Date string to parse (e.g., "01-Jan-2023")
        
    Returns:
        datetime.date object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None
        
    # Common date string cleanups
    date_str = date_str.strip()
    date_str = date_str.replace("–", "-").replace("—", "-")
    
    try:
        parsed = dateparser.parse(date_str, dayfirst=True, fuzzy=True)
        return parsed.date() if parsed else None
    except (ValueError, OverflowError, AttributeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None

def _fetch(url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object.
    
    Args:
        url: URL to fetch
        params: Optional query parameters
        
    Returns:
        BeautifulSoup object or None if request fails
    """
    if not url:
        logger.error("No URL provided to _fetch")
        return None
        
    try:
        # Add a small delay to be nice to the server
        time.sleep(REQUEST_DELAY + random.uniform(0, 0.5))
        
        logger.debug(f"Fetching URL: {url}")
        response = session.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        
        response.raise_for_status()
        
        # Check if we got rate limited or got a captcha page
        if "captcha" in response.text.lower() or "access denied" in response.text.lower():
            logger.warning("Possible CAPTCHA or access denied page detected")
            return None
            
        return BeautifulSoup(response.text, 'html.parser')
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
        return None

def _find_ipo_rows(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract IPO information from HTML tables.
    
    Args:
        soup: BeautifulSoup object containing the HTML
        
    Returns:
        List of dictionaries containing IPO information
    """
    rows = []
    if not soup:
        return rows
        
    # Look for tables with IPO timelines
    for table in soup.select("table"):
        try:
            # Get headers from thead or first row
            headers = [_clean_text(th.get_text(" ", strip=True)).lower() 
                      for th in table.select("thead th") or table.select("tr:first-child th")]
            
            # Skip if not an IPO table
            if not headers or not any("ipo" in h for h in headers) or not any("close" in h for h in headers):
                continue
                
            # Process each row in the table body
            for tr in table.select("tbody tr"):
                try:
                    # Skip header rows
                    if tr.select("th"):
                        continue
                        
                    cols = [_clean_text(td.get_text(" ", strip=True)) 
                           for td in tr.select("td")]
                    
                    if not cols:
                        continue
                        
                    # Extract links
                    links = tr.select("a[href]")
                    detail_url = next((f"{BASE_URL}{a['href']}" if a['href'].startswith("/") else a['href']
                                     for a in links if "/ipo/" in a.get('href', '') and not a['href'].endswith("/ipo/")), None)
                    gmp_url = next((f"{BASE_URL}{a['href']}" if a['href'].startswith("/") else a['href']
                                  for a in links if "ipo_gmp" in a.get('href', '')), None)
                    
                    # Map columns to headers
                    row_data = {h: cols[i] if i < len(cols) else "" 
                              for i, h in enumerate(headers)}
                    
                    # Extract dates
                    open_date = next((_parse_date(cols[i]) for i, h in enumerate(headers) 
                                    if i < len(cols) and "open" in h), None)
                    close_date = next((_parse_date(cols[i]) for i, h in enumerate(headers) 
                                     if i < len(cols) and "close" in h), None)
                    
                    # Skip if no name
                    name = cols[0] if cols else None
                    if not name:
                        continue
                        
                    rows.append({
                        'name': name,
                        'detail_url': detail_url,
                        'gmp_url': gmp_url,
                        'open_date': open_date,
                        'close_date': close_date,
                        **row_data
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing table row: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error processing table: {e}")
            continue
            
    return rows

def get_upcoming_ipos() -> List[IPOInfo]:
    """Fetch and parse upcoming IPOs from Chittorgarh website.
    
    This function tries multiple pages to get the most comprehensive list of IPOs.
    
    Returns:
        List of IPOInfo objects containing IPO details
    """
    ipos = []
    
    # Try the main IPO calendar page first
    logger.info("Fetching main IPO calendar page...")
    soup = _fetch(f"{BASE_URL}{UPCOMING_PATH}")
    if soup:
        rows = _find_ipo_rows(soup)
        if rows:
            logger.info(f"Found {len(rows)} IPOs on main page")
            ipos.extend(rows)
    
    # Fallback to alternative page if no IPOs found
    if not ipos:
        logger.info("No IPOs found on main page, trying alternative page...")
        soup = _fetch(f"{BASE_URL}{ALT_UPCOMING_PATH}")
        if soup:
            rows = _find_ipo_rows(soup)
            if rows:
                logger.info(f"Found {len(rows)} IPOs on alternative page")
                ipos.extend(rows)
    
    # Convert rows to IPOInfo objects
    result = []
    for row in ipos:
        try:
            ipo = IPOInfo(
                name=row.get("name"),
                detail_url=row.get("detail_url"),
                gmp_url=row.get("gmp_url"),
                open_date=row.get("open_date"),
                close_date=row.get("close_date"),
            )
            result.append(ipo)
        except Exception as e:
            logger.warning(f"Failed to create IPOInfo for row {row}: {e}")
    
    logger.info(f"Successfully parsed {len(result)} IPOs")
    return result

def _parse_ipo_details(soup: BeautifulSoup) -> Dict[str, str]:
    """Parse IPO details from the detail page HTML.
    
    Args:
        soup: BeautifulSoup object of the IPO detail page
        
    Returns:
        Dictionary containing parsed details (price_band, lot_size, etc.)
    """
    if not soup:
        return {}
        
    details = {}
    text = _clean_text(soup.get_text(" ", strip=True))
    
    # Extract price band
    m = re.search(r"price\s*band[\s:]*₹?\s*([\d,]+)\s*[–-]\s*₹?\s*([\d,]+)", text, flags=re.I)
    if m:
        details['price_band'] = f"₹{m.group(1).strip()} - ₹{m.group(2).strip()}"
    
    # Extract lot size
    m = re.search(r"lot\s*size[\s:]*([\d,]+)", text, flags=re.I)
    if m:
        details['lot_size'] = m.group(1).strip()
    
    # Extract issue size
    m = re.search(r"issue\s*size[\s:]*₹?\s*([\d,.]+)\s*(?:cr\.?|crore)", text, flags=re.I)
    if m:
        details['issue_size'] = f"₹{m.group(1).strip()} crore"
    
    # Find review/analysis
    review = soup.find("div", class_=re.compile("(?i)review|analysis|verdict"))
    if review:
        details['review_summary'] = _clean_text(review.get_text(" ", strip=True))
    
    return details

def _parse_gmp_details(soup: BeautifulSoup) -> Dict[str, str]:
    """Parse GMP details from the GMP page HTML.
    
    Args:
        soup: BeautifulSoup object of the GMP page
        
    Returns:
        Dictionary containing GMP details (gmp_latest, gmp_trend)
    """
    if not soup:
        return {}
        
    details = {}
    text = _clean_text(soup.get_text(" ", strip=True))
    
    # Extract latest GMP
    m = re.search(r"latest\s*gmp[\s:]*₹?\s*([\d,.]+)", text, flags=re.I)
    if m:
        details['gmp_latest'] = f"₹{m.group(1).strip()}"
    
    # Determine GMP trend
    if any(word in text.lower() for word in ["increase", "rise", "up"]):
        details['gmp_trend'] = "rising"
    elif any(word in text.lower() for word in ["decrease", "fall", "drop"]):
        details['gmp_trend'] = "falling"
    elif any(word in text.lower() for word in ["stable", "same", "unchanged"]):
        details['gmp_trend'] = "steady"
    
    return details

def enrich_with_details(ipo: IPOInfo) -> IPOInfo:
    """Enrich IPO information with additional details from detail and GMP pages.
    
    Args:
        ipo: IPOInfo object to enrich
        
    Returns:
        Enriched IPOInfo object
    """
    if not ipo or not isinstance(ipo, IPOInfo):
        logger.warning("Invalid IPOInfo object provided for enrichment")
        return ipo
    
    try:
        # Parse details from IPO page
        if ipo.detail_url:
            logger.debug(f"Fetching details for {ipo.name} from {ipo.detail_url}")
            soup = _fetch(ipo.detail_url)
            if soup:
                details = _parse_ipo_details(soup)
                for key, value in details.items():
                    setattr(ipo, key, value)
        
        # Parse GMP data if available
        if ipo.gmp_url:
            logger.debug(f"Fetching GMP details for {ipo.name} from {ipo.gmp_url}")
            soup = _fetch(ipo.gmp_url)
            if soup:
                gmp_details = _parse_gmp_details(soup)
                for key, value in gmp_details.items():
                    setattr(ipo, key, value)
        
        return ipo
        
    except Exception as e:
        logger.error(f"Error enriching IPO {ipo.name if ipo else 'Unknown'}: {e}", exc_info=True)
        return ipo
            m = re.search(r"(market\s*lot|lot\s*size)[:\s]*([\d,]+)\s*shares", text, flags=re.I)
            if m:
                ipo.lot_size = f"{m.group(2)} shares"
            m = re.search(r"(issue\s*size)[:\s]*₹?\s*([₹\d.,\sA-Za-z]+)", text, flags=re.I)
            if m:
                ipo.issue_size = _clean_text(m.group(2))
            # reviews
            review_section = None
            for h in soup.select("h2, h3"):
                if "review" in h.get_text(" ", strip=True).lower():
                    review_section = h
                    break
            if review_section:
                # capture some text following the header
                snippet = []
                node = review_section
                for _ in range(10):
                    node = node.find_next_sibling()
                    if not node:
                        break
                    snippet.append(node.get_text(" ", strip=True))
                combined = " ".join(snippet)
                combined = _clean_text(combined)
                ipo.review_summary = combined[:550] + ("..." if len(combined) > 550 else "")
                # expert recommendation heuristic
                if re.search(r"\bsubscribe|apply\b", combined, flags=re.I):
                    ipo.expert_recommendation = "Subscribe"
                elif re.search(r"\bavoid\b", combined, flags=re.I):
                    ipo.expert_recommendation = "Avoid"
                elif re.search(r"\bneutral|listed gains?|listing gains?\b", combined, flags=re.I):
                    ipo.expert_recommendation = "Neutral"
    # Attempt to fetch GMP page
    if not ipo.gmp_url and ipo.detail_url:
        # Guess GMP URL from slug
        m = re.search(r"/ipo/([^/]+)/", ipo.detail_url)
        if m:
            slug = m.group(1)
            ipo.gmp_url = f"{BASE}/ipo_gmp/{slug}/"
    if ipo.gmp_url:
        soup = _fetch(ipo.gmp_url)
        if soup:
            # try to locate a table with GMP history
            tables = soup.select("table")
            gmp_vals = []
            for table in tables:
                headers = [re.sub(r"\s+", " ", th.get_text(" ", strip=True)).lower() for th in table.select("th")]
                if any("gmp" in h for h in headers):
                    for tr in table.select("tbody tr"):
                        tds = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)) for td in tr.select("td")]
                        # find number in row
                        for cell in tds:
                            m = re.search(r"(-?\d+)", cell.replace(",", ""))
                            if m:
                                try:
                                    gmp_vals.append(int(m.group(1)))
                                    break
                                except:
                                    pass
            if gmp_vals:
                ipo.gmp_latest = f"₹{gmp_vals[0]}"  # assuming first row is latest; adjust if needed
                if len(gmp_vals) >= 3:
                    # simple trend using last 3
                    last3 = gmp_vals[:3]
                    if last3[0] > last3[1] >= last3[2]:
                        ipo.gmp_trend = "rising"
                    elif last3[0] < last3[1] <= last3[2]:
                        ipo.gmp_trend = "falling"
                    else:
                        ipo.gmp_trend = "steady"
                else:
                    ipo.gmp_trend = "unknown"
            else:
                # fallback: try to find a single GMP value in page text
                txt = _clean_text(soup.get_text(" ", strip=True))
                m = re.search(r"gmp[^₹\d-]*([₹]?\s*-?\d+)", txt, flags=re.I)
                if m:
                    ipo.gmp_latest = m.group(1).replace(" ", "")
                    ipo.gmp_trend = "unknown"
    return ipo

def today_ipos_closing(now_date: dt.date) -> List[IPOInfo]:
    ipos = get_upcoming_ipos()
    closing = []
    for ipo in ipos:
        if ipo.close_date and ipo.close_date == now_date:
            closing.append(enrich_with_details(ipo))
    return closing

def decide_apply_avoid(ipo: IPOInfo) -> Tuple[str, str]:
    """Return (recommendation, reason)"""
    rec = (ipo.expert_recommendation or "").lower()
    gmp = (ipo.gmp_latest or "")
    trend = (ipo.gmp_trend or "unknown")
    # numeric gmp if present
    gmp_num = None
    m = re.search(r"-?\d+", gmp.replace(",", ""))
    if m:
        try:
            gmp_num = int(m.group(0))
        except:
            pass
    # rules
    if rec in ("subscribe", "apply"):
        if gmp_num is not None and gmp_num >= 0 and trend in ("rising", "steady"):
            return "APPLY ✅", "Subscribe rating + non-negative GMP"
        return "APPLY (Cautious) ✅", "Positive expert view; GMP signal not strong"
    if rec == "avoid":
        if gmp_num is not None and gmp_num < 0:
            return "AVOID ❌", "Avoid rating + negative GMP"
        return "AVOID ❌", "Avoid rating from expert review"
    # neutral / unknown
    if gmp_num is not None and gmp_num > 0 and trend == "rising":
        return "NEUTRAL (Listing gains) ⚖", "Mixed reviews but rising GMP"
    return "NEUTRAL ⚖", "Mixed/insufficient data; apply only if thesis fits"

def format_email(now_date: dt.date, ipos: List[IPOInfo]) -> Tuple[str, str]:
    subject = f"IPO Reminder – {now_date.strftime('%d %b %Y')} (Last-day alerts)"
    if not ipos:
        body = f"Hello 👋\n\nNo IPOs are closing today ({now_date.strftime('%d-%b-%Y')}).\n\n— IPO Reminder Bot"
        return subject, body
    lines = [f"Hello 👋\n\nThese IPO(s) close today ({now_date.strftime('%d-%b-%Y')}):\n"]
    for ipo in ipos:
        rec, reason = decide_apply_avoid(ipo)
        lines.append(f"• {ipo.name}")
        if ipo.price_band: lines.append(f"  - Price Band: {ipo.price_band}")
        if ipo.lot_size: lines.append(f"  - Lot Size: {ipo.lot_size}")
        if ipo.issue_size: lines.append(f"  - Issue Size: {ipo.issue_size}")
        if ipo.gmp_latest: lines.append(f"  - GMP: {ipo.gmp_latest} ({ipo.gmp_trend or 'unknown'})")
        if ipo.expert_recommendation: lines.append(f"  - Expert View: {ipo.expert_recommendation}")
        lines.append(f"  - Bot Suggestion: {rec}")
        lines.append(f"  - Reason: {reason}")
        if ipo.detail_url: lines.append(f"  - Details: {ipo.detail_url}")
        if ipo.gmp_url: lines.append(f"  - GMP Page: {ipo.gmp_url}")
        if ipo.close_date: lines.append(f"  - Close Date: {ipo.close_date.strftime('%d-%b-%Y')}")
        lines.append("")
    lines.append("Note: Suggestions are informational, not financial advice.\n— IPO Reminder Bot")
    return subject, "\n".join(lines)
