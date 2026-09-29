"""
Universal Web Scraping Toolkit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A modular, resilient, and feature-complete web scraping suite covering:
1. Companies & Tech Stack Scraper
2. Restaurant & Menu Scraper
3. Video Games & Steam Intelligence Scraper
4. Wikipedia Deep-Detail Article & Infobox Scraper
5. E-Commerce & Product Catalog Scraper
"""

from scrapers.company_scraper import CompanyScraper
from scrapers.restaurant_scraper import RestaurantScraper
from scrapers.game_scraper import GameScraper
from scrapers.wikipedia_scraper import WikipediaScraper
from scrapers.ecommerce_scraper import EcommerceScraper

__all__ = [
    "CompanyScraper",
    "RestaurantScraper",
    "GameScraper",
    "WikipediaScraper",
    "EcommerceScraper",
]

__version__ = "1.0.0"
