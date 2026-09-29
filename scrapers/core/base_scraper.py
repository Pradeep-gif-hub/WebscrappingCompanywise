"""
Base scraper providing polite HTTP session management, rotating headers,
retries with backoff, asynchronous requests, and HTML/JSON parsers.
"""

import time
import random
import logging
from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import httpx

# Configure module logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


class BaseScraper:
    """Robust Base Scraper with retries, rotating User-Agents, rate limiting, and parsers."""

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    ]

    def __init__(
        self,
        min_delay: float = 0.5,
        max_delay: float = 1.5,
        retries: int = 3,
        backoff_factor: float = 1.0,
        timeout: int = 15,
        proxy: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.proxy = proxy
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup Synchronous Requests Session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

        self.custom_headers = custom_headers or {}
        self.last_request_time: float = 0.0

    def _get_random_headers(self) -> Dict[str, str]:
        """Generate realistic browser headers with randomized User-Agent."""
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "DNT": "1",
        }
        headers.update(self.custom_headers)
        return headers

    def _polite_delay(self) -> None:
        """Enforce respectful rate-limiting delay between requests."""
        if self.min_delay > 0:
            elapsed = time.time() - self.last_request_time
            sleep_duration = random.uniform(self.min_delay, self.max_delay)
            if elapsed < sleep_duration:
                time.sleep(sleep_duration - elapsed)
        self.last_request_time = time.time()

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """Send GET request with polite rate limiting and retry protection."""
        self._polite_delay()
        req_headers = self._get_random_headers()
        if headers:
            req_headers.update(headers)
            
        self.logger.debug(f"GET Request -> {url} (params: {params})")
        resp = self.session.get(
            url,
            params=params,
            headers=req_headers,
            timeout=timeout or self.timeout,
        )
        resp.raise_for_status()
        if resp.encoding and resp.encoding.lower() in ["iso-8859-1", "ascii"]:
            resp.encoding = resp.apparent_encoding or "utf-8"
        return resp

    def get_soup(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        parser: str = "lxml",
    ) -> BeautifulSoup:
        """Fetch URL and parse directly into BeautifulSoup."""
        resp = self.get(url, params=params, headers=headers)
        try:
            return BeautifulSoup(resp.text, parser)
        except Exception:
            return BeautifulSoup(resp.text, "html.parser")

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Fetch URL and parse JSON payload."""
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)
        resp = self.get(url, params=params, headers=req_headers)
        return resp.json()

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Send POST request."""
        self._polite_delay()
        req_headers = self._get_random_headers()
        if headers:
            req_headers.update(headers)
        resp = self.session.post(
            url,
            data=data,
            json=json_data,
            headers=req_headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp

    async def async_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Asynchronous HTTP GET using httpx for concurrent scraping."""
        req_headers = self._get_random_headers()
        if headers:
            req_headers.update(headers)
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=req_headers)
            resp.raise_for_status()
            return resp

    async def async_get_soup(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        parser: str = "lxml",
    ) -> BeautifulSoup:
        """Asynchronously fetch and parse HTML."""
        resp = await self.async_get(url, params=params, headers=headers)
        try:
            return BeautifulSoup(resp.text, parser)
        except Exception:
            return BeautifulSoup(resp.text, "html.parser")

    def close(self) -> None:
        """Close the requests session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
