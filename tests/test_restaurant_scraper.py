"""
Tests for Restaurant & Menu Intelligence Scraper.
"""

import pytest
from scrapers.restaurant_scraper import RestaurantScraper


@pytest.fixture
def rest_scraper():
    return RestaurantScraper(min_delay=0.1, max_delay=0.2)


def test_search_restaurants(rest_scraper):
    restaurants = rest_scraper.search_restaurants(city="San Francisco, CA", cuisine="Italian", limit=3)
    assert isinstance(restaurants, list)
    assert len(restaurants) > 0
    first = restaurants[0]
    assert "name" in first
    assert "cuisine" in first
    assert "rating" in first
    assert "price_tier" in first
    assert "phone" in first


def test_scrape_restaurant_details_and_menu(rest_scraper):
    details = rest_scraper.scrape_restaurant_details("Trattoria Bella", city="New York, NY")
    assert isinstance(details, dict)
    assert "name" in details
    assert "rating" in details
    assert "menu_items" in details
    assert len(details["menu_items"]) > 0
    
    # Check menu item fields
    item = details["menu_items"][0]
    assert "name" in item
    assert "price" in item
    assert "category" in item
    assert "dietary" in item


def test_restaurant_dietary_options(rest_scraper):
    details = rest_scraper.scrape_restaurant_details("Sakura Sushi", city="Los Angeles, CA")
    assert "dietary_options" in details
    assert "opening_hours" in details
    assert isinstance(details["opening_hours"], dict)
