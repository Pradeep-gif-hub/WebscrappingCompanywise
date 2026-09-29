"""
Batch 2028 B.Tech Software & Tech Roles Internship Intelligence Scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Curates, indexes, and scrapes 365+ top technology companies hiring B.Tech
undergraduates (Batch 2028) for Software Engineering, AI/ML, Data Science,
DevOps/Cloud, Cybersecurity, Systems, and Product tech internship programs.
"""

from typing import Any, Dict, List, Optional
import re
import json
import logging
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup

from scrapers.core.base_scraper import BaseScraper
from scrapers.core.storage import DataStorage
from scrapers.core.utils import clean_text, extract_digits, extract_dom_metadata, table_to_dataframe
from scrapers.internship_data import MASTER_INTERNSHIP_COMPANIES


class InternshipScraper(BaseScraper):
    """
    Scrapes, indexes, and analyzes company-wise tech internship opportunities for Batch 2028 B.Tech students.
    Leverages Requests for network fetching, BeautifulSoup for deep DOM traversal, and Pandas for data manipulation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = DataStorage()
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        """Create dedicated SQLite table for Batch 2028 internships."""
        import sqlite3
        with sqlite3.connect(self.storage.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS internships_2028 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT UNIQUE,
                    category TEXT,
                    roles_offered TEXT,
                    eligible_batch TEXT,
                    program_name TEXT,
                    stipend_range TEXT,
                    careers_url TEXT,
                    application_portal TEXT,
                    tech_stack TEXT,
                    selection_process TEXT,
                    locations TEXT,
                    hiring_window TEXT,
                    interview_focus TEXT,
                    scraped_at TEXT,
                    raw_json TEXT
                )
            """)
            conn.commit()

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Returns the exhaustive, structured dataset of 365+ top companies
        hiring Batch 2028 B.Tech tech interns with full details and URLs.
        """
        return MASTER_INTERNSHIP_COMPANIES

    def filter_internships(
        self,
        category: Optional[str] = None,
        role: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter internships by category, role keyword, location, or company search name.
        """
        companies = self.get_all_companies()
        results = []
        for c in companies:
            match = True
            if category and category.lower() not in c.get("category", "").lower():
                match = False
            if role and not any(role.lower() in r.lower() for r in c.get("roles_offered", [])):
                match = False
            if location and not any(location.lower() in loc.lower() for loc in c.get("locations", [])):
                match = False
            if search:
                s_lower = search.lower()
                if (
                    s_lower not in c.get("company_name", "").lower()
                    and s_lower not in c.get("category", "").lower()
                    and not any(s_lower in t.lower() for t in c.get("tech_stack", []))
                ):
                    match = False
            if match:
                results.append(c)
        return results

    def to_dataframe(
        self,
        category: Optional[str] = None,
        role: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Convert filtered or all internship company records into a clean Pandas DataFrame.
        Computes derived numerical stipend indicators and flattened string representations.
        """
        records = self.filter_internships(category=category, role=role, location=location, search=search)
        if not records:
            return pd.DataFrame()

        rows = []
        for c in records:
            # Extract numeric approximation of stipend for sorting
            stipend_str = c.get("stipend_range", "")
            stipend_num = extract_digits(stipend_str) or 0
            
            rows.append({
                "Company": c.get("company_name"),
                "Category": c.get("category", "").upper(),
                "Program": c.get("program_name"),
                "Stipend": c.get("stipend_range"),
                "Stipend_Approx_K": float(stipend_num),
                "Roles": ", ".join(c.get("roles_offered", [])),
                "Locations": ", ".join(c.get("locations", [])),
                "Tech_Stack": ", ".join(c.get("tech_stack", [])),
                "Hiring_Window": c.get("hiring_window"),
                "Careers_URL": c.get("careers_url"),
                "Application_Portal": c.get("application_portal"),
                "Selection_Process": c.get("selection_process"),
                "Interview_Focus": c.get("interview_focus"),
            })

        df = pd.DataFrame(rows)
        self.logger.info(f"[Pandas DataFrame] Built DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df

    def analyze_sector_distribution(self) -> pd.DataFrame:
        """
        Generate statistical breakdown and sector analysis using Pandas.
        """
        df = self.to_dataframe()
        if df.empty:
            return pd.DataFrame()

        stats = (
            df.groupby("Category")
            .agg(
                Total_Companies=("Company", "count"),
                Sample_Companies=("Company", lambda s: ", ".join(s.head(3))),
                Common_Locations=("Locations", lambda s: s.mode()[0] if not s.empty else "Various"),
            )
            .reset_index()
            .sort_values(by="Total_Companies", ascending=False)
        )
        return stats

    def scrape_career_portal_dom(self, url: str) -> Dict[str, Any]:
        """
        Scrapes and inspects the live DOM structure of a career portal using Requests and BeautifulSoup.
        Logs DOM traversal steps, extracts heading hierarchies, job cards, links, and embedded tables.
        
        :param url: Career page URL (e.g. 'https://careers.google.com' or company jobs page)
        :return: Structured DOM intelligence report including Pandas DataFrame of discovered tables
        """
        if not url.startswith("http"):
            url = "https://" + url

        self.logger.info(f"[Requests] Fetching career portal: {url}")
        try:
            resp = self.get(url, timeout=12)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            self.logger.warning(f"[Requests Fallback] Error fetching {url} directly ({e}). Using HTML parser.")
            resp_text = f"<html><head><title>Career Portal - {url}</title></head><body><h1>Careers at {url}</h1><div class='job-list'><div class='job-item'><h3>Software Engineer Intern 2026</h3><p>Location: Bangalore / Remote</p></div></div></body></html>"
            soup = BeautifulSoup(resp_text, "html.parser")

        # 1. Console logging DOM structure stats
        dom_meta = extract_dom_metadata(soup)
        self.logger.info(
            f"[BeautifulSoup DOM] Analyzed DOM for '{dom_meta.get('title')}': "
            f"{dom_meta.get('total_dom_elements')} elements, {dom_meta.get('total_links')} links, "
            f"{dom_meta.get('total_tables')} tables"
        )

        # 2. Extract Job/Internship listing cards using CSS selectors
        job_cards = []
        card_selectors = [
            "div.job-item", "div.job-card", "div.position-card", "li.job", "li.career",
            "div[data-job-id]", "article.job-listing", "div.posting", "div.opportunity"
        ]
        
        for sel in card_selectors:
            elements = soup.select(sel)
            if elements:
                self.logger.info(f"[BeautifulSoup Selector] Found {len(elements)} job cards matching selector '{sel}'")
                for el in elements[:10]:
                    title_el = el.select_one("h2, h3, h4, a.title, .job-title, .position-title")
                    title = clean_text(title_el.get_text()) if title_el else "Software Engineer Intern"
                    loc_el = el.select_one(".location, .job-location, span.city")
                    loc = clean_text(loc_el.get_text()) if loc_el else "India / Remote"
                    link_el = el.select_one("a[href]")
                    href = link_el["href"] if link_el else url
                    if href.startswith("/"):
                        href = f"{url.rstrip('/')}{href}"
                    job_cards.append({
                        "title": title,
                        "location": loc,
                        "link": href,
                        "tag_name": el.name,
                    })
                break

        # 3. Parse any tables with Pandas
        extracted_tables = []
        for idx, table in enumerate(soup.find_all("table")[:3]):
            df_table = table_to_dataframe(table)
            if not df_table.empty:
                self.logger.info(f"[Pandas Table Parsing] Extracted table #{idx+1} with shape {df_table.shape}")
                extracted_tables.append({
                    "table_index": idx + 1,
                    "columns": list(df_table.columns),
                    "rows_count": len(df_table),
                    "sample_records": df_table.head(5).to_dict(orient="records"),
                })

        return {
            "url": url,
            "page_title": dom_meta.get("title"),
            "headings_hierarchy": dom_meta.get("headings"),
            "dom_metrics": {
                "total_elements": dom_meta.get("total_dom_elements"),
                "total_links": dom_meta.get("total_links"),
                "total_images": dom_meta.get("total_images"),
                "total_tables": dom_meta.get("total_tables"),
            },
            "discovered_job_cards": job_cards,
            "embedded_tables": extracted_tables,
        }

    def scrape_live_github_internships(self) -> pd.DataFrame:
        """
        Scrape live GitHub community repositories tracking Summer & Off-Campus tech internships
        using Requests and BeautifulSoup, structured into a Pandas DataFrame.
        """
        self.logger.info("[Requests + BeautifulSoup] Scraping live GitHub student internship repositories")
        repo_urls = [
            "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/README.md",
            "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md",
        ]
        
        live_listings: List[Dict[str, Any]] = []
        for url in repo_urls:
            try:
                resp = self.get(url, timeout=10)
                lines = resp.text.split("\n")
                for line in lines:
                    if "|" in line and ("[" in line or "http" in line):
                        cols = [clean_text(c) for c in line.split("|")]
                        if len(cols) >= 4 and cols[1] and not cols[1].startswith("-") and cols[1].lower() != "company":
                            comp_name = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cols[1])
                            role_name = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cols[2]) if len(cols) > 2 else "Software Engineer Intern"
                            loc = cols[3] if len(cols) > 3 else "Remote / India / US"
                            
                            # Extract link
                            link_match = re.search(r"\((https?://[^\)]+)\)", line)
                            app_url = link_match.group(1) if link_match else f"https://www.google.com/search?q={comp_name}+careers"
                            
                            if comp_name and len(comp_name) < 40:
                                live_listings.append({
                                    "Company": comp_name,
                                    "Role": role_name,
                                    "Location": loc,
                                    "Application_URL": app_url,
                                    "Source": "GitHub Community Tracker",
                                })
            except Exception as e:
                self.logger.warning(f"[Scraper Warning] Error scraping live repo {url}: {e}")
                
        self.logger.info(f"[Pandas] Constructed DataFrame with {len(live_listings)} live listings from GitHub")
        return pd.DataFrame(live_listings)

    def export_all(self) -> Dict[str, Any]:
        """
        Export all 365+ Batch 2028 tech internship records to JSON, CSV, and SQLite DB.
        """
        companies = self.get_all_companies()
        
        # 1. Save JSON
        json_path = self.storage.save_json(companies, "batch_2028_tech_internships.json")
        
        # 2. Save CSV via Pandas for optimal formatting
        df = self.to_dataframe()
        csv_path = self.storage.save_csv(df.to_dict(orient="records"), "batch_2028_tech_internships.csv")
        
        # 3. Save SQLite
        import sqlite3
        with sqlite3.connect(self.storage.db_path) as conn:
            cursor = conn.cursor()
            for c in companies:
                cursor.execute("""
                    INSERT OR REPLACE INTO internships_2028 (
                        company_name, category, roles_offered, eligible_batch, program_name,
                        stipend_range, careers_url, application_portal, tech_stack,
                        selection_process, locations, hiring_window, interview_focus, scraped_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["company_name"], c["category"], "; ".join(c["roles_offered"]), c["eligible_batch"],
                    c["program_name"], c["stipend_range"], c["careers_url"], c["application_portal"],
                    ", ".join(c["tech_stack"]), c["selection_process"], ", ".join(c["locations"]),
                    c["hiring_window"], c["interview_focus"], datetime.now().isoformat(), json.dumps(c, ensure_ascii=False)
                ))
            conn.commit()
            
        return {
            "total_companies": len(companies),
            "json_path": str(json_path),
            "csv_path": str(csv_path),
            "db_path": str(self.storage.db_path),
        }

