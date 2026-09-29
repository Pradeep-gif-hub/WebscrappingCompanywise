"""
Batch 2028 B.Tech Software & Tech Roles Internship Intelligence Scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Curates, indexes, and scrapes 365+ top technology companies hiring B.Tech
undergraduates (Batch 2028) for Software Engineering, AI/ML, Data Science,
DevOps/Cloud, Cybersecurity, Systems, and Product tech internship programs.
"""

from typing import Any, Dict, List, Optional
import re
from scrapers.core.base_scraper import BaseScraper
from scrapers.core.storage import DataStorage
from scrapers.core.utils import clean_text, extract_digits
from scrapers.internship_data import MASTER_INTERNSHIP_COMPANIES


class InternshipScraper(BaseScraper):
    """Scrapes and indexes company-wise tech internship opportunities for Batch 2028 B.Tech students."""

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

    def scrape_live_github_internships(self) -> List[Dict[str, Any]]:
        """
        Scrape live GitHub community repositories tracking Summer & Off-Campus tech internships.
        """
        self.logger.info("Scraping live GitHub student internship repositories")
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
                                    "company_name": comp_name,
                                    "role": role_name,
                                    "location": loc,
                                    "application_url": app_url,
                                    "source": "GitHub Community Tracker",
                                })
            except Exception as e:
                self.logger.warning(f"Error scraping live repo {url}: {e}")
                
        self.logger.info(f"Retrieved {len(live_listings)} live tracked listings from GitHub repositories")
        return live_listings

    def export_all(self) -> Dict[str, Any]:
        """
        Export all 365+ Batch 2028 tech internship records to JSON, CSV, and SQLite DB.
        """
        companies = self.get_all_companies()
        
        # 1. Save JSON
        json_path = self.storage.save_json(companies, "batch_2028_tech_internships.json")
        
        # 2. Save CSV (flatten list fields for excel/csv friendly format)
        csv_records = []
        for c in companies:
            row = dict(c)
            row["roles_offered"] = "; ".join(c.get("roles_offered", []))
            row["tech_stack"] = ", ".join(c.get("tech_stack", []))
            row["locations"] = ", ".join(c.get("locations", []))
            csv_records.append(row)
            
        csv_path = self.storage.save_csv(csv_records, "batch_2028_tech_internships.csv")
        
        # 3. Save SQLite
        import sqlite3
        from datetime import datetime
        import json
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
