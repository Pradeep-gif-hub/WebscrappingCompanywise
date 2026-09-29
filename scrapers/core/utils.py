"""
Utility functions for text cleaning, parsing, and data normalization.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Union
from bs4 import BeautifulSoup, Tag
import pandas as pd


def clean_text(text: Optional[str]) -> str:
    """Normalize unicode, strip whitespace, remove repetitive newlines and tabs."""
    if not text:
        return ""
    # Normalize unicode (e.g. non-breaking spaces \xa0)
    text = unicodedata.normalize("NFKD", str(text))
    # Replace carriage returns and newlines with spaces or single newlines
    text = re.sub(r"[\r\n\t]+", " ", text)
    # Collapse multiple consecutive spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_digits(text: Optional[str], as_int: bool = False) -> Union[str, int, float, None]:
    """Extract digits and optional decimal point from a string."""
    if not text:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", clean_text(text).replace(",", ""))
    if not match:
        return None
    val_str = match.group()
    if as_int:
        try:
            return int(float(val_str))
        except ValueError:
            return None
    try:
        return float(val_str) if "." in val_str else int(val_str)
    except ValueError:
        return None


def parse_price(text: Optional[str]) -> Dict[str, Any]:
    """Extract price value and currency symbol from text string."""
    if not text:
        return {"amount": 0.0, "currency": "USD", "formatted": "$0.00", "is_free": False}
    
    clean = clean_text(text)
    if any(w in clean.lower() for w in ["free", "free to play", "complimentary", "0.00"]):
        return {"amount": 0.0, "currency": "USD", "formatted": "Free", "is_free": True}
    
    currency_map = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "CDN$": "CAD",
        "A$": "AUD",
    }
    
    detected_currency = "USD"
    for symbol, code in currency_map.items():
        if symbol in clean:
            detected_currency = code
            break
            
    digits = extract_digits(clean)
    amount = float(digits) if digits is not None else 0.0
    
    return {
        "amount": amount,
        "currency": detected_currency,
        "formatted": f"{clean}",
        "is_free": amount == 0.0,
    }


def parse_rating(text: Optional[str], max_stars: float = 5.0) -> Dict[str, Any]:
    """Parse rating scores (e.g., '4.5 out of 5', '8.9/10', 'Three', 'Four')."""
    if not text:
        return {"score": None, "max": max_stars, "percentage": None}
    
    word_to_num = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    
    clean = clean_text(text).lower()
    for word, num in word_to_num.items():
        if word == clean or f"star-rating {word}" in clean or f"rating-{word}" in clean:
            return {"score": float(num), "max": 5.0, "percentage": (num / 5.0) * 100}
            
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:/|out of|\s+of\s+)\s*(\d+(?:\.\d+)?)", clean)
    if match:
        score = float(match.group(1))
        scale = float(match.group(2))
        return {"score": score, "max": scale, "percentage": (score / scale) * 100}
        
    num = extract_digits(clean)
    if num is not None:
        score = float(num)
        return {"score": score, "max": max_stars, "percentage": min(100.0, (score / max_stars) * 100)}
        
    return {"score": None, "max": max_stars, "percentage": None}


def slugify(text: str) -> str:
    """Convert text into URL-safe slug."""
    text = clean_text(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def table_to_dataframe(table_tag: Tag) -> pd.DataFrame:
    """Parse an HTML <table> into a clean Pandas DataFrame."""
    if not table_tag or table_tag.name != "table":
        return pd.DataFrame()
        
    rows = []
    # Check headers
    headers = []
    thead = table_tag.find("thead")
    if thead:
        th_tags = thead.find_all(["th", "td"])
        headers = [clean_text(th.get_text()) for th in th_tags if clean_text(th.get_text())]
    
    tbody = table_tag.find("tbody") or table_tag
    for tr in tbody.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        row_vals = [clean_text(c.get_text()) for c in cells]
        if row_vals and any(row_vals):
            # If no header was found previously and this row contains th tags
            if not headers and tr.find_all("th") and not tr.find_all("td"):
                headers = row_vals
            else:
                rows.append(row_vals)
                
    if not rows:
        return pd.DataFrame()
        
    max_cols = max(len(r) for r in rows)
    if headers:
        while len(headers) < max_cols:
            headers.append(f"Column_{len(headers)+1}")
        headers = headers[:max_cols]
    else:
        headers = [f"Col_{i+1}" for i in range(max_cols)]
        
    # Pad rows to uniform length
    padded_rows = [r + [""] * (max_cols - len(r)) for r in rows]
    return pd.DataFrame(padded_rows, columns=headers)


def format_bytes(size: int) -> str:
    """Human readable file/content size formatting."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def extract_dom_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract comprehensive DOM tree analytics, heading hierarchy, meta tags, and link metrics.
    """
    if not soup:
        return {}
        
    title_tag = soup.find("title")
    title = clean_text(title_tag.get_text()) if title_tag else ""
    
    # Meta tags extraction
    meta_tags = {}
    for meta in soup.find_all("meta"):
        name = meta.get("name") or meta.get("property") or meta.get("http-equiv")
        content = meta.get("content")
        if name and content:
            meta_tags[name] = clean_text(content)
            
    # Heading hierarchy
    headings = {
        "h1": [clean_text(h.get_text()) for h in soup.find_all("h1") if clean_text(h.get_text())],
        "h2": [clean_text(h.get_text()) for h in soup.find_all("h2") if clean_text(h.get_text())][:10],
        "h3": [clean_text(h.get_text()) for h in soup.find_all("h3") if clean_text(h.get_text())][:10],
    }
    
    # Links & Images counts
    links = soup.find_all("a", href=True)
    images = soup.find_all("img")
    scripts = soup.find_all("script")
    tables = soup.find_all("table")
    
    return {
        "title": title,
        "meta_tags": meta_tags,
        "headings": headings,
        "total_dom_elements": len(soup.find_all(True)),
        "total_links": len(links),
        "total_images": len(images),
        "total_scripts": len(scripts),
        "total_tables": len(tables),
    }


def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract Schema.org JSON-LD structured data blocks from the DOM."""
    import json
    json_ld_blocks = []
    if not soup:
        return json_ld_blocks
        
    for script in soup.find_all("script", type="application/ld+json"):
        content = script.string or script.get_text()
        if content:
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    json_ld_blocks.extend(parsed)
                elif isinstance(parsed, dict):
                    json_ld_blocks.append(parsed)
            except Exception:
                continue
    return json_ld_blocks


def tables_from_soup(soup: BeautifulSoup) -> List[pd.DataFrame]:
    """Parse all HTML tables within a BeautifulSoup DOM into a list of Pandas DataFrames."""
    if not soup:
        return []
    tables = soup.find_all("table")
    dfs = []
    for tbl in tables:
        df = table_to_dataframe(tbl)
        if not df.empty:
            dfs.append(df)
    return dfs

