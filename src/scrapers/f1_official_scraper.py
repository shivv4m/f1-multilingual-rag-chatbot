from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict
import time


class F1OfficialScraper:
    def __init__(self):
        self.driver = None

    def init_browser(self):
        """Initialize Selenium Chrome browser with better options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)  # Set implicit wait

    def scrape_news(self) -> List[Dict]:
        """Scrape F1 news with improved error handling"""
        try:
            self.init_browser()

            # Try multiple URLs
            urls = [
                'https://www.formula1.com/en/latest',
                'https://www.formula1.com/en/latest/all.html'
            ]

            for url in urls:
                try:
                    print(f"Trying URL: {url}")
                    self.driver.get(url)

                    # Scroll to load dynamic content
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)

                    # Try multiple selectors
                    selectors = [
                        '.f1-latest-listing--item',
                        '.listing-item',
                        '.news-item',
                        'article',
                        '.card'
                    ]

                    articles = []
                    wait = WebDriverWait(self.driver, 20)

                    for selector in selectors:
                        try:
                            print(f"Trying selector: {selector}")
                            elements = wait.until(EC.presence_of_all_elements_located(
                                (By.CSS_SELECTOR, selector)
                            ))

                            if elements:
                                print(f"Found {len(elements)} elements with selector: {selector}")

                                for i, element in enumerate(elements[:10]):
                                    try:
                                        # Try multiple ways to get title and link
                                        title = self._extract_text(element, [
                                            '.f1-latest-listing--item-title',
                                            '.listing-item--title',
                                            'h3', 'h2', '.title'
                                        ])

                                        link = self._extract_link(element, ['a'])

                                        desc = self._extract_text(element, [
                                            '.f1-latest-listing--item-summary',
                                            '.listing-item--summary',
                                            '.summary', 'p'
                                        ])

                                        if title:
                                            articles.append({
                                                'title': title,
                                                'description': desc or title,
                                                'url': link or url,
                                                'source': 'F1 Official'
                                            })

                                    except Exception as e:
                                        print(f"Error processing element {i}: {e}")
                                        continue

                                if articles:
                                    return articles

                        except TimeoutException:
                            print(f"Timeout for selector: {selector}")
                            continue

                except Exception as e:
                    print(f"Error with URL {url}: {e}")
                    continue

            # Fallback: return sample data
            print("Using fallback sample data")
            return self.get_sample_news()

        except Exception as e:
            print(f"Critical error in scrape_news: {e}")
            return self.get_sample_news()
        finally:
            if self.driver:
                self.driver.quit()

    def _extract_text(self, element, selectors: List[str]) -> str:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                text_element = element.find_element(By.CSS_SELECTOR, selector)
                text = text_element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue

        # Fallback to element text
        try:
            return element.text.strip()
        except:
            return ""

    def _extract_link(self, element, selectors: List[str]) -> str:
        """Try to extract link"""
        for selector in selectors:
            try:
                link_element = element.find_element(By.CSS_SELECTOR, selector)
                href = link_element.get_attribute('href')
                if href and not href.startswith('http'):
                    href = 'https://www.formula1.com' + href
                return href
            except NoSuchElementException:
                continue
        return ""

    def get_sample_news(self) -> List[Dict]:
        """Fallback sample news data"""
        return [
            {
                'title': 'Formula 1 Latest News Update',
                'description': 'Stay updated with the latest Formula 1 news, race results, and driver standings.',
                'url': 'https://www.formula1.com',
                'source': 'F1 Official (Sample)'
            },
            {
                'title': 'F1 Championship Update',
                'description': 'Current championship standings and recent race highlights from the Formula 1 season.',
                'url': 'https://www.formula1.com',
                'source': 'F1 Official (Sample)'
            }
        ]

    def close(self):
        if self.driver:
            self.driver.quit()


# Synchronous wrapper
def run_f1_official_scraper():
    scraper = F1OfficialScraper()
    try:
        news = scraper.scrape_news()
        return {'news': news}
    finally:
        scraper.close()
