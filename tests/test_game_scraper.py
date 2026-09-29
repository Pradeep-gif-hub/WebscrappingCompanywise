"""
Tests for Video Games and Steam Platform Scraper.
"""

import pytest
from scrapers.game_scraper import GameScraper


@pytest.fixture
def game_scraper():
    return GameScraper(min_delay=0.1, max_delay=0.2)


def test_search_steam_games(game_scraper):
    results = game_scraper.search_steam_games(query="Elden Ring", limit=3)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert "title" in first
    assert "price" in first
    assert "platforms" in first


def test_scrape_game_details_steam_api(game_scraper):
    # App ID 1091500 is Cyberpunk 2077
    game = game_scraper.scrape_game_details("1091500")
    assert isinstance(game, dict)
    assert "Cyberpunk" in game.get("title", "") or "game" in game.get("type", "")
    assert "developers" in game
    assert "price" in game
    assert "genres" in game
    assert "system_requirements" in game


def test_scrape_top_free_games(game_scraper):
    free_games = game_scraper.scrape_top_free_games(category="shooter", limit=3)
    assert isinstance(free_games, list)
    assert len(free_games) > 0
    first = free_games[0]
    assert "title" in first
    assert "is_free" in first
    assert first["is_free"] is True
