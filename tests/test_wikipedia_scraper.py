"""
Tests for Wikipedia Deep-Detail Knowledge Scraper.
"""

import pytest
from scrapers.wikipedia_scraper import WikipediaScraper


@pytest.fixture
def wiki_scraper():
    return WikipediaScraper(language="en", min_delay=0.1, max_delay=0.2)


def test_wikipedia_search(wiki_scraper):
    results = wiki_scraper.search("Quantum computing", limit=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "title" in results[0]
    assert "url" in results[0]


def test_scrape_wikipedia_article_details(wiki_scraper):
    article = wiki_scraper.scrape_article("Python_(programming_language)")
    assert isinstance(article, dict)
    assert "Python" in article["title"]
    assert len(article["summary"]) > 50
    assert "infobox" in article
    assert isinstance(article["infobox"], dict)
    assert len(article["infobox"]) > 0
    assert "sections" in article
    assert len(article["sections"]) > 0
    assert "categories" in article
    assert len(article["categories"]) > 0


def test_scrape_random_article(wiki_scraper):
    article = wiki_scraper.get_random_article()
    assert isinstance(article, dict)
    assert "title" in article
    assert "url" in article
    assert "summary" in article
