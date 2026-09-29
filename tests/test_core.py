"""
Unit and Integration Tests for Core Scraping Engine and Data Storage.
"""

import os
import shutil
import pytest
import pandas as pd
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper
from scrapers.core.storage import DataStorage
from scrapers.core.utils import (
    clean_text,
    extract_digits,
    parse_price,
    parse_rating,
    slugify,
    table_to_dataframe,
    format_bytes,
)


@pytest.fixture
def temp_storage(tmp_path):
    """Provides isolated storage instance in temporary directory."""
    storage = DataStorage(output_dir=str(tmp_path / "data_test"), db_name="test.db")
    yield storage
    # Cleanup


def test_clean_text():
    raw = "  Hello   \n\n\t World\xa0!  \r\n"
    assert clean_text(raw) == "Hello World !"
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_extract_digits():
    assert extract_digits("Price: $149.99 USD") == 149.99
    assert extract_digits("Stock: 50 items", as_int=True) == 50
    assert extract_digits("No digits here") is None
    assert extract_digits(None) is None


def test_parse_price():
    p1 = parse_price("$49.99")
    assert p1["amount"] == 49.99
    assert p1["currency"] == "USD"
    assert p1["is_free"] is False

    p2 = parse_price("£12.50")
    assert p2["amount"] == 12.50
    assert p2["currency"] == "GBP"

    p3 = parse_price("Free to Play")
    assert p3["amount"] == 0.0
    assert p3["is_free"] is True

    p4 = parse_price(None)
    assert p4["amount"] == 0.0


def test_parse_rating():
    r1 = parse_rating("4.5 out of 5")
    assert r1["score"] == 4.5
    assert r1["max"] == 5.0

    r2 = parse_rating("star-rating Four")
    assert r2["score"] == 4.0

    r3 = parse_rating("9/10")
    assert r3["score"] == 9.0
    assert r3["max"] == 10.0


def test_slugify():
    assert slugify("Hello World & Python 3.10!") == "hello-world-python-310"
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"


def test_table_to_dataframe():
    html_table = """
    <table>
        <thead>
            <tr><th>Name</th><th>Role</th><th>Salary</th></tr>
        </thead>
        <tbody>
            <tr><td>Alice</td><td>Developer</td><td>$120k</td></tr>
            <tr><td>Bob</td><td>Designer</td><td>$95k</td></tr>
        </tbody>
    </table>
    """
    soup = BeautifulSoup(html_table, "html.parser")
    df = table_to_dataframe(soup.find("table"))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["Name", "Role", "Salary"]
    assert df.iloc[0]["Name"] == "Alice"


def test_format_bytes():
    assert format_bytes(500) == "500.0 B"
    assert "KB" in format_bytes(2048)
    assert "MB" in format_bytes(5 * 1024 * 1024)


def test_storage_json_and_csv(temp_storage):
    sample_data = [
        {"id": 1, "name": "Company A", "score": 9.5},
        {"id": 2, "name": "Company B", "score": 8.0},
    ]
    
    json_path = temp_storage.save_json(sample_data, "test_file.json")
    assert os.path.exists(json_path)
    
    csv_path = temp_storage.save_csv(sample_data, "test_file.csv")
    assert os.path.exists(csv_path)


def test_storage_sqlite_crud(temp_storage):
    # Test inserting company
    c_record = {
        "name": "Stripe Inc",
        "domain": "stripe.com",
        "industry": "Fintech",
        "tech_stack": ["Ruby", "AWS"],
        "job_openings_count": 10,
        "description": "Financial infrastructure",
    }
    inserted = temp_storage.save_to_db("companies", c_record)
    assert inserted == 1
    
    df = temp_storage.query_db("SELECT * FROM companies WHERE name = ?", ("Stripe Inc",))
    assert len(df) == 1
    assert df.iloc[0]["domain"] == "stripe.com"


def test_base_scraper_context_manager():
    with BaseScraper(min_delay=0.0, max_delay=0.0) as scraper:
        assert scraper.session is not None
        headers = scraper._get_random_headers()
        assert "User-Agent" in headers


def test_extract_dom_metadata():
    from scrapers.core.utils import extract_dom_metadata, extract_json_ld, tables_from_soup
    html = """
    <html>
        <head>
            <title>Test Portal</title>
            <meta name="description" content="Test description" />
            <script type="application/ld+json">
                {"@context": "https://schema.org", "@type": "Organization", "name": "TestOrg"}
            </script>
        </head>
        <body>
            <h1>Main Title</h1>
            <h2>Subtitle 1</h2>
            <a href="https://example.com/jobs">Jobs</a>
            <img src="logo.png" />
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Users</td><td>1M</td></tr>
            </table>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    meta = extract_dom_metadata(soup)
    assert meta["title"] == "Test Portal"
    assert meta["meta_tags"]["description"] == "Test description"
    assert "Main Title" in meta["headings"]["h1"]
    assert meta["total_links"] == 1
    assert meta["total_tables"] == 1

    json_ld = extract_json_ld(soup)
    assert len(json_ld) == 1
    assert json_ld[0]["name"] == "TestOrg"

    dfs = tables_from_soup(soup)
    assert len(dfs) == 1
    assert isinstance(dfs[0], pd.DataFrame)
    assert dfs[0].iloc[0]["Metric"] == "Users"

