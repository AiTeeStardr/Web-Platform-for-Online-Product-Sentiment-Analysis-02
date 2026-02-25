"""
Base Scraper - Abstract interface for web scrapers
"""
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for platform-specific scrapers."""

    @abstractmethod
    def scrape(self, url, max_pages=5):
        """
        Scrape reviews from a product URL.

        Args:
            url: Product page URL
            max_pages: Maximum number of review pages to scrape

        Returns:
            List[dict]: Raw review data
                [{text, rating, username, date, ...}]
        """
        pass

    @abstractmethod
    def validate_url(self, url):
        """Validate that the URL is from the expected platform."""
        pass
