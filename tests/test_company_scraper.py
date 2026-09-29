"""
Tests for Company & Tech Stack Scraper.
"""

import pytest
from scrapers.company_scraper import CompanyScraper


@pytest.fixture
def company_scraper():
    return CompanyScraper(min_delay=0.1, max_delay=0.2)


def test_scrape_company_jobs(company_scraper):
    jobs = company_scraper.scrape_company_jobs(query="python", limit=3)
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    first = jobs[0]
    assert "company_name" in first
    assert "position" in first
    assert "tech_stack" in first
    assert isinstance(first["tech_stack"], list)


def test_scrape_github_org(company_scraper):
    gh = company_scraper.scrape_github_org("google")
    assert isinstance(gh, dict)
    assert "organization" in gh
    assert "github_handle" in gh
    assert gh["github_handle"] == "google"
    assert "popular_repositories" in gh


def test_scrape_company_website_meta(company_scraper):
    meta = company_scraper.scrape_company_website_meta("https://github.com")
    assert isinstance(meta, dict)
    assert "domain" in meta
    assert "detected_technologies" in meta
    assert isinstance(meta["detected_technologies"], list)


def test_build_company_dossier(company_scraper):
    dossier = company_scraper.build_company_dossier("Vercel")
    assert isinstance(dossier, dict)
    assert dossier["name"] == "Vercel"
    assert "tech_stack" in dossier
    assert "job_openings_count" in dossier
    assert "github_overview" in dossier
