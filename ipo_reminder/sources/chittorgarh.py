import re
import time
import json
import datetime as dt
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Dict

import requests
from bs4 import BeautifulSoup
import pandas as pd
from dateutil import parser as dateparser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BASE = "https://www.chittorgarh.com"
UPCOMING = BASE + "/ipo/ipo_calendar_timeline/"
ALT_UPCOMING = BASE + "/report/latest-ipo-gmp/56/"  # fallback to get names/dates when calendar shifts

@dataclass
class IPOInfo:
    name: str
    detail_url: Optional[str]
    gmp_url: Optional[str]
    open_date: Optional[dt.date]
    close_date: Optional[dt.date]
    price_band: Optional[str] = None
    lot_size: Optional[str] = None
    issue_size: Optional[str] = None
    review_summary: Optional[str] = None
    expert_recommendation: Optional[str] = None
    gmp_latest: Optional[str] = None
    gmp_trend: Optional[str] = None  # rising/steady/falling/unknown

def _clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()

def _parse_date(val: str) -> Optional[dt.date]:
    if not val:
        return None
    val = val.replace("–", "-").replace("—", "-")
    try:
        return dateparser.parse(val, dayfirst=True, fuzzy=True).date()
    except Exception:
        return None

def _fetch(url: str) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None

def _find_ipo_rows(soup: BeautifulSoup) -> List[Dict]:
    rows = []
    # Look for tables with IPO timelines
    for table in soup.select("table"):
        headers = [ _clean_text(th.get_text(" ", strip=True)).lower() for th in table.select("thead th")]
        if not headers:
            # sometimes tables don't have thead; try first row
            first = table.select_one("tr")
            if first:
                headers = [ _clean_text(th.get_text(" ", strip=True)).lower() for th in first.select("th")]
        if not headers:
            continue
        # we expect columns like 'ipo name', 'open', 'close'
        if any("ipo" in h and "name" in h for h in headers) and any("close" in h for h in headers):
            for tr in table.select("tbody tr"):
                cols = [ _clean_text(td.get_text(" ", strip=True)) for td in tr.select("td") ]
                links = tr.select("a[href]")
                detail_url = None
                gmp_url = None
                for a in links:
                    href = a.get("href")
                    if href and "/ipo/" in href and not href.endswith("/ipo/"):
                        detail_url = BASE + href if href.startswith("/") else href
                    if href and "ipo_gmp" in href:
                        gmp_url = BASE + href if href.startswith("/") else href
                # map columns roughly
                # attempt to find name/open/close by header index
                d = dict()
                for i, h in enumerate(headers):
                    if i < len(cols):
                        d[h] = cols[i]
                name = cols[0] if cols else None
                open_date = None
                close_date = None
                # find first header with 'open' and with 'close'
                for i, h in enumerate(headers):
                    if "open" in h and i < len(cols):
                        open_date = _parse_date(cols[i])
                    if "close" in h and i < len(cols):
                        close_date = _parse_date(cols[i])
                if name:
                    rows.append({
                        "name": name,
                        "detail_url": detail_url,
                        "gmp_url": gmp_url,
                        "open_date": open_date,
                        "close_date": close_date
                    })
    return rows

def get_upcoming_ipos() -> List[IPOInfo]:
    soup = _fetch(UPCOMING)
    rows = _find_ipo_rows(soup) if soup else []
    if not rows:
        # fallback to alternative page that at least lists many current IPOs
        soup2 = _fetch(ALT_UPCOMING)
        rows = _find_ipo_rows(soup2) if soup2 else []
    ipos = []
    for r in rows:
        ipos.append(IPOInfo(
            name=r.get("name"),
            detail_url=r.get("detail_url"),
            gmp_url=r.get("gmp_url"),
            open_date=r.get("open_date"),
            close_date=r.get("close_date"),
        ))
    return ipos

def enrich_with_details(ipo: IPOInfo) -> IPOInfo:
    # Parse details from IPO page
    if ipo.detail_url:
        soup = _fetch(ipo.detail_url)
        if soup:
            # price band, lot size, issue size appear in key-value tables or bullet lists
            text = _clean_text(soup.get_text(" ", strip=True))
            # rough regexes
            m = re.search(r"price\s*band[:\s]*₹?\s*([\d,]+)\s*[-–]\s*₹?\s*([\d,]+)", text, flags=re.I)
            if m:
                ipo.price_band = f"₹{m.group(1)} – ₹{m.group(2)}"
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
