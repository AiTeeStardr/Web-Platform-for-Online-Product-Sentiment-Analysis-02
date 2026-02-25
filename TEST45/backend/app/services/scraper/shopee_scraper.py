"""
Shopee Scraper - Selenium-based web scraper for Shopee product reviews.
Handles Dynamic Content loading via headless Chrome.
"""
import time
import logging
from datetime import datetime, timezone

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False

from app.services.scraper.base import BaseScraper
from app.config import Config

logger = logging.getLogger(__name__)


class ShopeeScraper(BaseScraper):
    """
    Scraper for Shopee product reviews using Selenium.

    Handles:
    - Dynamic content loading (lazy load)
    - Review pagination
    - Rating extraction
    - PDPA-ready data extraction (usernames captured for anonymization)
    """

    PLATFORM = 'shopee'
    BASE_URL = 'https://shopee.co.th'

    def __init__(self, headless=None):
        self.headless = headless if headless is not None else Config.SELENIUM_HEADLESS
        self.driver = None

    def validate_url(self, url):
        """Validate Shopee URL format."""
        return 'shopee.co.th' in url or 'shopee.com' in url

    def scrape(self, url, max_pages=5):
        """
        Scrape reviews from a Shopee product page.

        Args:
            url: Shopee product URL
            max_pages: Maximum review pages to scrape

        Returns:
            List[dict]: Raw review data
        """
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

            # Wait for page load
            time.sleep(Config.SCRAPE_DELAY)

            # Scroll to reviews section
            self._scroll_to_reviews()

            for page in range(max_pages):
                logger.info(f"Scraping page {page + 1}/{max_pages}")

                # Extract reviews on current page
                page_reviews = self._extract_reviews()
                reviews.extend(page_reviews)

                # Navigate to next page
                if not self._go_to_next_page():
                    break

                time.sleep(Config.SCRAPE_DELAY)

        except Exception as e:
            logger.error(f"Scraping error: {e}")
        finally:
            self._close_driver()

        logger.info(f"Scraped {len(reviews)} reviews from Shopee")
        return reviews

    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=th')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/120.0.0.0 Safari/537.36')

        if HAS_WDM:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(10)

    def _close_driver(self):
        """Safely close WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def _scroll_to_reviews(self):
        """Scroll down to the review section."""
        try:
            # Try to scroll to the rating section
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6)")
            time.sleep(1)
        except Exception:
            pass

    def _extract_reviews(self):
        """Extract reviews from the current page."""
        reviews = []
        try:
            # Shopee review selectors (may need updating)
            review_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.shopee-product-rating, [class*="product-rating"], [class*="review"]'
            )

            for element in review_elements:
                review = self._parse_review_element(element)
                if review and review.get('text'):
                    reviews.append(review)

        except Exception as e:
            logger.warning(f"Error extracting reviews: {e}")

        return reviews

    def _parse_review_element(self, element):
        """Parse a single review element."""
        review = {
            'text': '',
            'rating': 0,
            'username': '',
            'date': '',
            'source_platform': self.PLATFORM,
            'scraped_at': datetime.now(timezone.utc)
        }

        try:
            # Try multiple selectors for review text
            text_selectors = [
                '[class*="comment"]',
                '[class*="review-text"]',
                '.shopee-product-rating__main-comment',
                'p', 'div.content'
            ]
            for selector in text_selectors:
                try:
                    text_el = element.find_element(By.CSS_SELECTOR, selector)
                    if text_el.text.strip():
                        review['text'] = text_el.text.strip()
                        break
                except NoSuchElementException:
                    continue

            # Try to extract rating (star count)
            try:
                stars = element.find_elements(By.CSS_SELECTOR, '[class*="star"][class*="full"], .icon-rating-solid')
                review['rating'] = len(stars) if stars else 0
            except Exception:
                pass

            # Extract username (will be anonymized later)
            try:
                user_el = element.find_element(By.CSS_SELECTOR, '[class*="author"], [class*="user"]')
                review['username'] = user_el.text.strip()
            except NoSuchElementException:
                pass

        except Exception as e:
            logger.debug(f"Error parsing review element: {e}")

        return review

    def _go_to_next_page(self):
        """Navigate to the next review page."""
        try:
            next_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                'button.shopee-icon-button--right, [class*="next"]'
            )
            if next_btn.is_enabled():
                next_btn.click()
                time.sleep(1)
                return True
        except (NoSuchElementException, Exception):
            pass
        return False

    def _demo_reviews(self):
        """Return demo review data for testing without Selenium."""
        return [
            {'text': 'กล้องถ่ายรูปสวยมาก คมชัดทุกมุม ชอบมาก ๆ เลย', 'rating': 5,
             'username': 'user_demo_1', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'แบตหมดเร็วมาก ใช้ไม่ถึงครึ่งวัน ต้องชาร์จตลอด', 'rating': 2,
             'username': 'user_demo_2', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'จอ AMOLED สีสดใส ดูหนังดูซีรีส์สนุกมาก', 'rating': 5,
             'username': 'user_demo_3', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'ราคาแพงไปหน่อย แต่คุณภาพดี ใช้งานลื่นไม่มีสะดุด', 'rating': 4,
             'username': 'user_demo_4', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'ส่งมาบุบ กล่องพัง ผิดหวังมากกับการจัดส่ง 😡', 'rating': 1,
             'username': 'user_demo_5', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'ดีไซน์สวย สีพรีเมียม ถือออกไปข้างนอกได้ภูมิใจ ✨', 'rating': 5,
             'username': 'user_demo_6', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'ประสิทธิภาพแรง ชิปเร็วมาก เล่นเกมลื่น 🔥', 'rating': 5,
             'username': 'user_demo_7', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'กล้องถ่ายรูปตอนกลางคืนไม่ค่อยดี เม็ดเยอะ', 'rating': 3,
             'username': 'user_demo_8', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'ชาร์จเร็วมาก 30 นาทีได้ 70% 👍 แบตอึดด้วย', 'rating': 5,
             'username': 'user_demo_9', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'หน้าจอแตกง่ายมาก ตกครั้งเดียวร้าว 😭 ไม่คุ้มเลย', 'rating': 1,
             'username': 'user_demo_10', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'ใช้งานได้ปกติ ไม่มีอะไรพิเศษ ก็โอเค', 'rating': 3,
             'username': 'user_demo_11', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
            {'text': 'บริการหลังการขายดีมาก เคลมง่าย พนักงานน่ารัก', 'rating': 5,
             'username': 'user_demo_12', 'source_platform': 'shopee',
             'scraped_at': datetime.now(timezone.utc)},
        ]
