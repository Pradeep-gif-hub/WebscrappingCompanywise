"""
Tests for E-Commerce and Product Catalog Scraper.
"""

import pytest
from scrapers.ecommerce_scraper import EcommerceScraper


@pytest.fixture
def ecom_scraper():
    return EcommerceScraper(min_delay=0.1, max_delay=0.2)


def test_scrape_categories(ecom_scraper):
    categories = ecom_scraper.scrape_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert "category" in categories[0]
    assert "url" in categories[0]


def test_scrape_category_products(ecom_scraper):
    products = ecom_scraper.scrape_category_products(category_name="Mystery", max_pages=1)
    assert isinstance(products, list)
    assert len(products) > 0
    p = products[0]
    assert "title" in p
    assert "price" in p
    assert "rating" in p
    assert "availability" in p
    assert "url" in p


def test_scrape_product_details(ecom_scraper):
    # Test details on live book
    products = ecom_scraper.scrape_category_products(category_name="Mystery", max_pages=1)
    target_url = products[0]["url"] if products else "https://books.toscrape.com/catalogue/sharp-objects_997/index.html"
    
    details = ecom_scraper.scrape_product_details(target_url)
    assert isinstance(details, dict)
    assert "title" in details
    assert "upc" in details
    assert "price" in details
    assert "rating" in details
    assert "stock_quantity" in details
