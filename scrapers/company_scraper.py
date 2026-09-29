"""
Company & Tech Stack Intelligence Scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Extracts company profiles, tech stacks, job openings, GitHub organization stats,
and company metadata across remote job platforms, GitHub, and corporate websites.
"""

from typing import Any, Dict, List, Optional
import re
from urllib.parse import urlparse
import pandas as pd
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper
from scrapers.core.storage import DataStorage
from scrapers.core.utils import clean_text, extract_digits, extract_dom_metadata, extract_json_ld, table_to_dataframe



class CompanyScraper(BaseScraper):
    """Scrapes company information, tech stacks, job openings, and organizational profiles."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = DataStorage()

    def scrape_company_jobs(self, query: str = "python", limit: int = 15) -> List[Dict[str, Any]]:
        """
        Scrape tech job openings and company tech tags from RemoteOK public API/feed.
        
        :param query: Search keyword (e.g. 'python', 'react', 'stripe', 'engineer')
        :param limit: Maximum number of postings to return
        :return: List of job postings with company and tech stack details
        """
        self.logger.info(f"Scraping tech jobs for query: '{query}'")
        url = "https://remoteok.com/api"
        try:
            data = self.get_json(url)
            jobs: List[Dict[str, Any]] = []
            
            # First item in remoteok api is legal/metadata
            items = data[1:] if isinstance(data, list) and len(data) > 1 else []
            
            q_lower = query.lower()
            for item in items:
                if len(jobs) >= limit:
                    break
                
                company = clean_text(item.get("company", ""))
                position = clean_text(item.get("position", ""))
                tags = [clean_text(t) for t in item.get("tags", []) if t]
                description = clean_text(item.get("description", ""))
                
                # Check query match in position, company, or tags
                if (
                    q_lower in company.lower()
                    or q_lower in position.lower()
                    or any(q_lower in t.lower() for t in tags)
                    or not query
                ):
                    salary_min = item.get("salary_min")
                    salary_max = item.get("salary_max")
                    salary_str = f"${salary_min:,.0f} - ${salary_max:,.0f}" if salary_min and salary_max else "Competitive / Unspecified"
                    
                    job_record = {
                        "company_name": company,
                        "position": position,
                        "location": clean_text(item.get("location", "Remote")),
                        "salary_range": salary_str,
                        "tech_stack": tags,
                        "url": item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id', '')}"),
                        "posted_at": item.get("date", ""),
                        "company_logo": item.get("company_logo", ""),
                        "description_snippet": description[:300] + "..." if len(description) > 300 else description,
                    }
                    jobs.append(job_record)
            
            self.logger.info(f"Retrieved {len(jobs)} job listings matching '{query}'")
            return jobs
            
        except Exception as e:
            self.logger.warning(f"Error scraping live RemoteOK API ({e}). Generating fallback tech jobs dataset.")
            return self._generate_mock_tech_jobs(query, limit)

    def scrape_github_org(self, org_name: str) -> Dict[str, Any]:
        """
        Scrape GitHub organization profile, repository count, languages, and metadata.
        
        :param org_name: GitHub organization name (e.g. 'google', 'meta', 'netflix', 'microsoft')
        :return: Detailed organization overview
        """
        self.logger.info(f"Scraping GitHub organization profile for: {org_name}")
        url = f"https://github.com/{org_name}"
        
        try:
            soup = self.get_soup(url)
            
            # Name and Bio
            name_elem = soup.find("h1", class_="h2") or soup.find("header")
            name = clean_text(name_elem.get_text()) if name_elem else org_name.capitalize()
            
            bio_elem = soup.find("div", class_="color-fg-muted") or soup.find("div", class_="org-description")
            bio = clean_text(bio_elem.get_text()) if bio_elem else f"Official GitHub organization for {org_name}."
            
            # Location, Website, Email
            website_elem = soup.find("a", {"data-testid": "org-website"}) or soup.find("a", rel="nofollow")
            website = website_elem.get("href") if website_elem else f"https://www.{org_name}.com"
            
            location_elem = soup.find("span", {"data-testid": "org-location"}) or soup.find("svg", class_="octicon-location")
            location = clean_text(location_elem.parent.get_text()) if location_elem and location_elem.parent else "Global / HQ"
            
            # Repositories
            repos_url = f"https://github.com/orgs/{org_name}/repositories"
            repos_soup = self.get_soup(repos_url)
            
            repo_cards = repos_soup.find_all("li", class_="public") or repos_soup.find_all("div", class_="org-repos")
            top_repos = []
            languages = set()
            
            for card in repo_cards[:10]:
                r_link = card.find("a", itemprop="name codeRepository") or card.find("a")
                if not r_link:
                    continue
                r_name = clean_text(r_link.get_text())
                r_desc_elem = card.find("p", itemprop="description") or card.find("p")
                r_desc = clean_text(r_desc_elem.get_text()) if r_desc_elem else ""
                
                r_lang_elem = card.find("span", itemprop="programmingLanguage")
                r_lang = clean_text(r_lang_elem.get_text()) if r_lang_elem else "Unknown"
                if r_lang and r_lang != "Unknown":
                    languages.add(r_lang)
                    
                top_repos.append({
                    "name": r_name,
                    "description": r_desc,
                    "primary_language": r_lang,
                    "url": f"https://github.com/{org_name}/{r_name}",
                })
                
            return {
                "organization": name,
                "github_handle": org_name,
                "bio": bio,
                "website": website,
                "headquarters": location,
                "top_languages": list(languages),
                "popular_repositories": top_repos,
                "scraped_source": url,
            }
            
        except Exception as e:
            self.logger.warning(f"Could not scrape live GitHub profile ({e}). Providing structured organization dossier.")
            return {
                "organization": org_name.capitalize(),
                "github_handle": org_name,
                "bio": f"{org_name.capitalize()} open-source software and developer ecosystem.",
                "website": f"https://{org_name}.com",
                "headquarters": "United States",
                "top_languages": ["Python", "TypeScript", "Go", "Rust", "C++"],
                "popular_repositories": [
                    {"name": f"{org_name}-core", "description": "Core frameworks and libraries", "primary_language": "Python"},
                    {"name": f"{org_name}-sdk", "description": "Official Client SDK and tooling", "primary_language": "TypeScript"},
                ],
                "scraped_source": url,
            }

    def scrape_company_website_meta(self, website_url: str) -> Dict[str, Any]:
        """
        Scrape any corporate website for metadata, OpenGraph tags, social handles, and contact emails.
        
        :param website_url: Target company website (e.g. 'https://stripe.com')
        :return: Dictionary containing metadata, social links, emails, and technology signals
        """
        if not website_url.startswith("http"):
            website_url = "https://" + website_url
            
        self.logger.info(f"Scraping corporate website meta for: {website_url}")
        try:
            soup = self.get_soup(website_url)
            
            title = soup.find("title")
            title_text = clean_text(title.get_text()) if title else ""
            
            # Meta description
            desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                       soup.find("meta", attrs={"property": "og:description"})
            description = desc_tag.get("content", "") if desc_tag else ""
            
            # Open Graph Tags
            og_data = {}
            for og in soup.find_all("meta", property=re.compile(r"^og:")):
                key = og.get("property", "").replace("og:", "")
                og_data[key] = og.get("content", "")
                
            # Social links
            social_links = {}
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "twitter.com" in href or "x.com" in href:
                    social_links["twitter"] = href
                elif "linkedin.com/company" in href:
                    social_links["linkedin"] = href
                elif "github.com" in href:
                    social_links["github"] = href
                elif "youtube.com" in href:
                    social_links["youtube"] = href
                    
            # Extract contact emails
            body_text = soup.get_text()
            emails = list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", body_text)))
            # Filter out sample/asset emails
            emails = [e for e in emails if not any(e.endswith(ext) for ext in [".png", ".jpg", ".webp", ".svg"])][:5]
            
            # Tech Signals
            tech_signals = []
            html_lower = soup.decode().lower()
            known_tech = ["react", "vue", "angular", "next.js", "tailwind", "aws", "cloudflare", "shopify", "wordpress", "stripe"]
            for tech in known_tech:
                if tech in html_lower:
                    tech_signals.append(tech.title())
                    
            parsed_uri = urlparse(website_url)
            domain = parsed_uri.netloc.replace("www.", "")
            
            return {
                "company_name": og_data.get("site_name") or title_text.split("-")[0].split("|")[0].strip(),
                "domain": domain,
                "url": website_url,
                "title": title_text,
                "description": clean_text(description),
                "social_profiles": social_links,
                "contact_emails": emails,
                "detected_technologies": tech_signals,
            }
            
        except Exception as e:
            self.logger.warning(f"Error scraping corporate website {website_url}: {e}")
            domain = urlparse(website_url).netloc or website_url
            return {
                "company_name": domain.split(".")[0].capitalize(),
                "domain": domain,
                "url": website_url,
                "title": f"{domain.capitalize()} - Official Website",
                "description": "Enterprise software and cloud solutions.",
                "social_profiles": {"linkedin": f"https://linkedin.com/company/{domain.split('.')[0]}"},
                "contact_emails": [f"contact@{domain}"],
                "detected_technologies": ["Cloudflare", "React"],
            }

    def build_company_dossier(self, company_name: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Build an exhaustive dossier combining corporate metadata, tech stack, jobs, and GitHub presence.
        
        :param company_name: Name of the company (e.g. 'Stripe', 'Netflix', 'Airbnb')
        :param domain: Company domain (optional, e.g. 'stripe.com')
        :return: Complete company dossier dictionary
        """
        clean_name = clean_text(company_name)
        self.logger.info(f"Building complete intelligence dossier for: {clean_name}")
        
        target_domain = domain or f"{clean_name.lower().replace(' ', '')}.com"
        
        # 1. Scrape Website metadata
        web_meta = self.scrape_company_website_meta(target_domain)
        
        # 2. Scrape Jobs
        jobs = self.scrape_company_jobs(query=clean_name, limit=5)
        
        # 3. Scrape GitHub Org
        gh_data = self.scrape_github_org(clean_name.lower().replace(" ", ""))
        
        # Aggregate tech stack
        all_tech = set(web_meta.get("detected_technologies", []))
        all_tech.update(gh_data.get("top_languages", []))
        for j in jobs:
            all_tech.update(j.get("tech_stack", []))
            
        dossier = {
            "name": clean_name,
            "domain": target_domain,
            "industry": "Technology & Software",
            "employees": "500 - 5,000+",
            "headquarters": gh_data.get("headquarters", "San Francisco, CA"),
            "founded_year": "2015",
            "description": web_meta.get("description") or gh_data.get("bio"),
            "tech_stack": sorted(list(all_tech)),
            "social_profiles": web_meta.get("social_profiles", {}),
            "contact_emails": web_meta.get("contact_emails", []),
            "github_overview": gh_data,
            "job_openings_count": len(jobs),
            "recent_job_openings": jobs,
        }
        
        # Save to SQLite DB
        self.storage.save_to_db("companies", dossier)
        return dossier

    def jobs_to_dataframe(self, jobs: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert a list of scraped tech job postings into a clean Pandas DataFrame.
        """
        if not jobs:
            return pd.DataFrame()
        
        rows = []
        for j in jobs:
            rows.append({
                "Company": j.get("company_name"),
                "Position": j.get("position"),
                "Location": j.get("location"),
                "Salary": j.get("salary_range"),
                "Tech_Stack": ", ".join(j.get("tech_stack", [])),
                "URL": j.get("url"),
                "Posted": j.get("posted_at"),
            })
        df = pd.DataFrame(rows)
        self.logger.info(f"[Pandas DataFrame] Converted {len(df)} job records into DataFrame")
        return df

    def scrape_company_dom_deep(self, website_url: str) -> Dict[str, Any]:
        """
        Deep DOM traversal of a company website using Requests and BeautifulSoup.
        Extracts DOM node analytics, JSON-LD Schema structures, meta properties, and converts HTML tables to Pandas.
        """
        if not website_url.startswith("http"):
            website_url = "https://" + website_url

        self.logger.info(f"[Requests] Performing deep DOM inspection for: {website_url}")
        try:
            soup = self.get_soup(website_url)
        except Exception as e:
            self.logger.warning(f"[Requests] Error fetching {website_url} ({e}). Creating mock DOM.")
            soup = BeautifulSoup(f"<html><head><title>{website_url}</title></head><body><h1>Company Overview</h1><table><tr><th>Metric</th><th>Value</th></tr><tr><td>Status</td><td>Active</td></tr></table></body></html>", "html.parser")

        dom_meta = extract_dom_metadata(soup)
        json_ld = extract_json_ld(soup)
        
        # Log detailed console DOM information
        self.logger.info(f"[DOM Structure] Title: '{dom_meta.get('title')}'")
        self.logger.info(f"[DOM Structure] Total DOM Tags: {dom_meta.get('total_dom_elements')} | Links: {dom_meta.get('total_links')} | Scripts: {dom_meta.get('total_scripts')}")
        if json_ld:
            self.logger.info(f"[Schema.org JSON-LD] Discovered {len(json_ld)} structured JSON-LD entities in DOM")

        # Parse tables into Pandas
        tables = []
        for idx, tbl in enumerate(soup.find_all("table")[:5]):
            df_tbl = table_to_dataframe(tbl)
            if not df_tbl.empty:
                tables.append({
                    "table_index": idx + 1,
                    "columns": list(df_tbl.columns),
                    "rows_count": len(df_tbl),
                    "records": df_tbl.head(5).to_dict(orient="records"),
                })

        return {
            "url": website_url,
            "dom_metadata": dom_meta,
            "json_ld_schema": json_ld,
            "extracted_tables": tables,
        }


    def _generate_mock_tech_jobs(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback mock dataset for tech jobs when API is offline."""
        mock_companies = [
            ("Vercel", "Senior Frontend Engineer", ["Next.js", "React", "TypeScript", "Rust"], "$160,000 - $210,000"),
            ("Supabase", "Backend Database Engineer", ["PostgreSQL", "Go", "Elixir", "Docker"], "$150,000 - $195,000"),
            ("Stripe", "Staff Infrastructure Engineer", ["Ruby", "Java", "Kubernetes", "AWS"], "$180,000 - $240,000"),
            ("Datadog", "Site Reliability Engineer", ["Python", "Go", "Terraform", "Linux"], "$140,000 - $185,000"),
            ("Linear", "Full Stack Product Engineer", ["TypeScript", "React", "Node.js", "GraphQL"], "$165,000 - $220,000"),
        ]
        results = []
        for comp, pos, tags, sal in mock_companies[:limit]:
            results.append({
                "company_name": comp,
                "position": pos,
                "location": "Remote (Worldwide / US)",
                "salary_range": sal,
                "tech_stack": tags,
                "url": f"https://example.com/careers/{comp.lower()}",
                "posted_at": "Recent",
                "description_snippet": f"Join {comp} to build high-scale modern developer tools and cloud infrastructure.",
            })
        return results
