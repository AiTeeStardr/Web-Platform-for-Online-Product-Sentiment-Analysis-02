"""
Shopee Scraper - Selenium-based web scraper for Shopee product reviews.
Configured for Render deployment (Linux container).
"""

import time
import logging
from datetime import datetime, timezone

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

from app.services.scraper.base import BaseScraper
from app.config import Config

logger = logging.getLogger(__name__)


class ShopeeScraper(BaseScraper):
    PLATFORM = "shopee"
    BASE_URL = "https://shopee.co.th"

    def __init__(self, headless=None):
        self.headless = headless if headless is not None else Config.SELENIUM_HEADLESS
        self.driver = None

    # -------------------------
    # PUBLIC METHODS
    # -------------------------

    def validate_url(self, url):
        return "shopee.co.th" in url or "shopee.com" in url

    def scrape(self, url, max_pages=3):
        if not HAS_SELENIUM:
            logger.warning("Selenium not installed. Returning demo data.")
            return self._demo_reviews()

        if not self.validate_url(url):
            logger.error(f"Invalid Shopee URL: {url}")
            return []

        reviews = []

        try:
            self._init_driver()
            self.driver.get(url)

            time.sleep(Config.SCRAPE_DELAY)

            self._scroll_to_reviews()

            for page in range(max_pages):
                logger.info(f"Scraping page {page + 1}/{max_pages}")

                page_reviews = self._extract_reviews()
                reviews.extend(page_reviews)

                if not self._go_to_next_page():
                    break

                time.sleep(Config.SCRAPE_DELAY)

        except Exception as e:
            logger.error(f"Scraping error: {e}")

        finally:
            self._close_driver()

        logger.info(f"Scraped {len(reviews)} reviews")
        return reviews

    # -------------------------
    # DRIVER SETUP (RENDER SAFE)
    # -------------------------

    def _init_driver(self):
        options = Options()

        # 🔥 สำคัญมากสำหรับ Render
        options.binary_location = "/usr/bin/google-chrome"

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=th")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        # 🔥 ใช้ chromedriver ที่ติดตั้งใน container
        service = Service("/usr/bin/chromedriver")

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def _close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    # -------------------------
    # SCRAPING LOGIC
    # -------------------------

    def _scroll_to_reviews(self):
        try:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight * 0.6);"
            )
            time.sleep(2)
        except Exception:
            pass

    def _extract_reviews(self):
        reviews = []

        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".shopee-product-rating, [class*='review'], [class*='rating']"
            )

            for element in elements:
                review = self._parse_review_element(element)
                if review and review.get("text"):
                    reviews.append(review)

        except Exception as e:
            logger.warning(f"Extract error: {e}")

        return reviews

    def _parse_review_element(self, element):
        review = {
            "text": "",
            "rating": 0,
            "username": "",
            "date": "",
            "source_platform": self.PLATFORM,
            "scraped_at": datetime.now(timezone.utc),
        }

        try:
            # TEXT
            try:
                text_el = element.find_element(By.CSS_SELECTOR, "[class*='comment']")
                review["text"] = text_el.text.strip()
            except NoSuchElementException:
                pass

            # STARS
            try:
                stars = element.find_elements(
                    By.CSS_SELECTOR, "[class*='star'][class*='full']"
                )
                review["rating"] = len(stars)
            except Exception:
                pass

            # USERNAME
            try:
                user_el = element.find_element(
                    By.CSS_SELECTOR, "[class*='author'], [class*='user']"
                )
                review["username"] = user_el.text.strip()
            except NoSuchElementException:
                pass

        except Exception:
            pass

        return review

    def _go_to_next_page(self):
        try:
            next_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "button.shopee-icon-button--right, [class*='next']"
            )

            if next_btn.is_enabled():
                next_btn.click()
                time.sleep(2)
                return True

        except Exception:
            pass

        return False

    # -------------------------
    # DEMO DATA
    # -------------------------

    def _demo_reviews(self):
        return [
            {
                "text": "สินค้าดีมาก คุณภาพเกินราคา",
                "rating": 5,
                "username": "demo_user_1",
                "source_platform": "shopee",
                "scraped_at": datetime.now(timezone.utc),
            },
            {
                "text": "จัดส่งช้าไปหน่อย",
                "rating": 3,
                "username": "demo_user_2",
                "source_platform": "shopee",
                "scraped_at": datetime.now(timezone.utc),
            },
            {
                "text": "ของเสียหาย ผิดหวังมาก",
                "rating": 1,
                "username": "demo_user_3",
                "source_platform": "shopee",
                "scraped_at": datetime.now(timezone.utc),
            },
        ]