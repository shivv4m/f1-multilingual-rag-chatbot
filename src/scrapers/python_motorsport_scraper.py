import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime


class MotorsportPlaywrightScraper:
    def __init__(self):
        self.scraped_data = []

    async def scrape_all_motorsport(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Generate URLs
            base_routes = [
                'https://www.motorsport.com/f1/news',
                'https://www.motorsport.com/f1/results',
                'https://www.motorsport.com/f1/standings',
                'https://www.motorsport.com/f1/schedule'
            ]

            years = range(2020, 2026)  # 2020-2025

            tasks = []
            for base_url in base_routes:
                for year in years:
                    url = f"{base_url}/{year}"
                    tasks.append(self.scrape_page(browser, url, year))

            # Run all scraping tasks
            await asyncio.gather(*tasks)

            await browser.close()

            print(f"✅ Scraped {len(self.scraped_data)} total articles")
            return self.scraped_data

    async def scrape_page(self, browser, url, year):
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle')

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Extract articles using multiple selectors
            selectors = ['article', '[class*="news"]', '[class*="item"]']

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for elem in elements[:20]:  # Limit per page
                        title_elem = elem.find(['h1', 'h2', 'h3', 'a'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if len(title) > 10:
                                self.scraped_data.append({
                                    'title': title,
                                    'content': title,
                                    'url': url,
                                    'source': 'Motorsport.com',
                                    'year': str(year),
                                    'scraped_at': datetime.now().isoformat()
                                })
                    break

            await page.close()
            print(f"✅ Scraped {url}")

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")


# Usage
async def main():
    scraper = MotorsportPlaywrightScraper()
    data = await scraper.scrape_all_motorsport()

    # Save to JSON
    with open('motorsport_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"💾 Saved {len(data)} articles to motorsport_data.json")


if __name__ == "__main__":
    asyncio.run(main())
