"""
Tests for Batch 2028 Tech Internship Intelligence Scraper.
"""

import pytest
import os
from scrapers.internship_scraper import InternshipScraper


@pytest.fixture
def internship_scraper():
    return InternshipScraper(min_delay=0.0, max_delay=0.0)


def test_get_all_companies(internship_scraper):
    companies = internship_scraper.get_all_companies()
    assert isinstance(companies, list)
    assert len(companies) >= 350, f"Expected 350+ companies, got {len(companies)}"
    
    first = companies[0]
    assert "company_name" in first
    assert "category" in first
    assert "roles_offered" in first
    assert "eligible_batch" in first
    assert "careers_url" in first
    assert "stipend_range" in first
    assert "tech_stack" in first
    assert "Batch 2028" in first["eligible_batch"]


def test_filter_by_category(internship_scraper):
    faang_results = internship_scraper.filter_internships(category="FAANG")
    assert len(faang_results) >= 20
    assert any(c["company_name"] == "Google" for c in faang_results)
    assert any(c["company_name"] == "Microsoft" for c in faang_results)


def test_filter_by_role(internship_scraper):
    sde_results = internship_scraper.filter_internships(role="SWE")
    assert len(sde_results) > 0
    assert any("SWE" in " ".join(c["roles_offered"]) for c in sde_results)


def test_filter_by_location(internship_scraper):
    blr_results = internship_scraper.filter_internships(location="Bangalore")
    assert len(blr_results) >= 150
    assert any("Bangalore" in " ".join(c["locations"]) for c in blr_results)


def test_search_internships(internship_scraper):
    results = internship_scraper.filter_internships(search="Jane Street")
    assert len(results) >= 1
    assert results[0]["company_name"] == "Jane Street"
    assert "Quant" in results[0]["category"]


def test_export_all_internships(internship_scraper, tmp_path):
    res = internship_scraper.export_all()
    assert "total_companies" in res
    assert res["total_companies"] >= 350
    assert os.path.exists(res["json_path"])
    assert os.path.exists(res["csv_path"])
    assert os.path.exists(res["db_path"])


def test_to_dataframe(internship_scraper):
    import pandas as pd
    df = internship_scraper.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 350
    assert "Company" in df.columns
    assert "Category" in df.columns
    assert "Stipend" in df.columns
    assert "Roles" in df.columns


def test_analyze_sector_distribution(internship_scraper):
    stats = internship_scraper.analyze_sector_distribution()
    assert not stats.empty
    assert "Category" in stats.columns
    assert "Total_Companies" in stats.columns
    assert stats["Total_Companies"].sum() >= 350


def test_scrape_career_portal_dom(internship_scraper):
    dom_report = internship_scraper.scrape_career_portal_dom("https://careers.google.com")
    assert "page_title" in dom_report
    assert "dom_metrics" in dom_report
    assert "headings_hierarchy" in dom_report

