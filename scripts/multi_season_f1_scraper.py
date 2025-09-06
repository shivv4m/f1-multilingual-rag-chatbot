#!/usr/bin/env python3
"""
Multi-Season F1 Data Scraper
Scrapes Motorsport.com and other sites across multiple years/seasons
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin
import concurrent.futures
import threading

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.data_processing.text_chunker import F1TextChunker
from src.vector_store.pinecone_client import PineconeClient


class MultiSeasonF1Scraper:
    def __init__(self):
        self.chunker = F1TextChunker()
        self.pinecone_client = PineconeClient()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.lock = threading.Lock()  # For thread-safe operations

    def generate_seasonal_urls(self, base_urls: Dict[str, str], start_year: int = 2018, end_year: int = 2025) -> Dict[
        str, List[str]]:
        """Generate URLs for multiple seasons across different sites"""
        seasonal_urls = {}

        for site_name, base_url in base_urls.items():
            urls = []
            for year in range(start_year, end_year + 1):
                # Different URL patterns for different sites
                if 'motorsport.com' in base_url:
                    urls.append(f"{base_url}/{year}")
                elif 'autosport.com' in base_url:
                    urls.append(f"{base_url}/{year}")
                elif 'schedule' in base_url:
                    urls.append(f"{base_url.replace('2025', str(year))}")
                elif 'standings' in base_url:
                    urls.append(f"{base_url.replace('2025', str(year))}")
                elif 'results' in base_url:
                    urls.append(f"{base_url.replace('2025', str(year))}")
                else:
                    urls.append(f"{base_url}/{year}")

            seasonal_urls[site_name] = urls

        return seasonal_urls

    def scrape_motorsport_season(self, url: str, year: int) -> List[Dict]:
        """Scrape Motorsport.com for a specific season"""
        try:
            print(f"📅 Scraping Motorsport.com {year}...")
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []

            # Look for articles with various selectors
            selectors = [
                'article',
                '[class*="news"]',
                '[class*="article"]',
                '[class*="item"]',
                'div[class*="ms-"]'
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"Found {len(elements)} elements with {selector}")

                    for element in elements[:15]:  # Limit per selector
                        try:
                            # Try to find title in various ways
                            title_elem = (
                                    element.select_one('h1, h2, h3, h4') or
                                    element.select_one('a[href*="/news/"]') or
                                    element.select_one('a')
                            )

                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                if len(title) > 15:  # Filter short titles

                                    # Get link
                                    link = ''
                                    if title_elem.name == 'a':
                                        link = title_elem.get('href', '')
                                    else:
                                        link_elem = element.select_one('a')
                                        if link_elem:
                                            link = link_elem.get('href', '')

                                    if link and not link.startswith('http'):
                                        link = urljoin(url, link)

                                    # Get content/summary
                                    content_elem = element.select_one('p, [class*="summary"], [class*="excerpt"]')
                                    content = content_elem.get_text(strip=True) if content_elem else title

                                    articles.append({
                                        'title': title,
                                        'content': f"{title}. {content}",
                                        'url': link or url,
                                        'source': f'Motorsport.com {year}',
                                        'type': 'news',
                                        'language': 'en',
                                        'year': str(year),
                                        'scraped_at': datetime.now().isoformat()
                                    })
                        except Exception as e:
                            continue

                    if articles:  # If we found articles, no need to try other selectors
                        break

            print(f"✅ Motorsport {year}: {len(articles)} articles")
            return articles

        except Exception as e:
            print(f"❌ Error scraping Motorsport {year}: {e}")
            return []

    def scrape_season_standings(self, base_url: str, year: int) -> List[Dict]:
        """Scrape season standings for a specific year"""
        try:
            url = base_url.replace('2025', str(year))
            print(f"🏆 Scraping {year} standings...")

            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            standings_data = []

            # Look for tables or standings data
            tables = soup.find_all(['table', 'div'],
                                   class_=lambda x: x and ('standing' in x.lower() or 'result' in x.lower()))

            for table in tables:
                rows = table.find_all(['tr', 'div'])
                if len(rows) > 5:  # Likely standings
                    standings_text = f"{year} F1 Championship Standings:\n"

                    for i, row in enumerate(rows[1:11]):  # Top 10
                        try:
                            text = row.get_text(strip=True)
                            if text and len(text) > 10:
                                standings_text += f"{text}\n"
                        except:
                            continue

                    if len(standings_text) > 100:  # Has meaningful content
                        standings_data.append({
                            'title': f'F1 {year} Championship Standings',
                            'content': standings_text,
                            'url': url,
                            'source': f'Standings {year}',
                            'type': 'standings',
                            'language': 'en',
                            'year': str(year),
                            'scraped_at': datetime.now().isoformat()
                        })
                        break

            print(f"✅ {year} standings: {len(standings_data)} entries")
            return standings_data

        except Exception as e:
            print(f"❌ Error scraping {year} standings: {e}")
            return []

    def scrape_season_schedule(self, base_url: str, year: int) -> List[Dict]:
        """Scrape race schedule for a specific year"""
        try:
            url = base_url.replace('2025', str(year))
            print(f"📅 Scraping {year} schedule...")

            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            schedule_data = []

            # Look for race information
            race_elements = soup.find_all(['div', 'tr', 'li'],
                                          class_=lambda x: x and ('race' in x.lower() or 'grand' in x.lower()))

            schedule_text = f"{year} Formula 1 Race Calendar:\n"
            race_count = 0

            for element in race_elements:
                try:
                    text = element.get_text(strip=True)
                    if 'Grand Prix' in text or 'GP' in text and len(text) > 20:
                        schedule_text += f"• {text}\n"
                        race_count += 1
                        if race_count >= 20:  # Max races per season
                            break
                except:
                    continue

            if race_count > 3:  # Has meaningful schedule data
                schedule_data.append({
                    'title': f'F1 {year} Race Calendar',
                    'content': schedule_text,
                    'url': url,
                    'source': f'Schedule {year}',
                    'type': 'schedule',
                    'language': 'en',
                    'year': str(year),
                    'scraped_at': datetime.now().isoformat()
                })

            print(f"✅ {year} schedule: {len(schedule_data)} entries")
            return schedule_data

        except Exception as e:
            print(f"❌ Error scraping {year} schedule: {e}")
            return []

    def scrape_year_parallel(self, args) -> List[Dict]:
        """Scrape a single year in parallel"""
        year, base_urls = args
        year_articles = []

        # Scrape different types of content for this year
        if 'motorsport_news' in base_urls:
            url = base_urls['motorsport_news'].replace('YEAR', str(year))
            articles = self.scrape_motorsport_season(url, year)
            year_articles.extend(articles)
            time.sleep(1)  # Rate limiting

        if 'standings' in base_urls:
            standings = self.scrape_season_standings(base_urls['standings'], year)
            year_articles.extend(standings)
            time.sleep(1)

        if 'schedule' in base_urls:
            schedule = self.scrape_season_schedule(base_urls['schedule'], year)
            year_articles.extend(schedule)
            time.sleep(1)

        return year_articles

    def comprehensive_multi_season_scrape(self, start_year: int = 2020, end_year: int = 2025,
                                          max_workers: int = 3) -> bool:
        """Scrape F1 data across multiple seasons"""
        print(f"🚀 Starting multi-season F1 scrape ({start_year}-{end_year})...")

        # Define base URLs for different content types
        base_urls = {
            'motorsport_news': 'https://www.motorsport.com/f1/news/YEAR',
            'autosport_news': 'https://www.autosport.com/f1/news/YEAR',
            'standings': 'https://www.motorsport.com/f1/standings/2025/',
            'schedule': 'https://www.motorsport.com/f1/schedule/2025/',
        }

        all_articles = []

        # Create year range
        years = list(range(start_year, end_year + 1))

        # Prepare arguments for parallel processing
        year_args = [(year, base_urls) for year in years]

        # Use ThreadPoolExecutor for parallel scraping (but limited to avoid overloading)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            print(f"⚡ Using {max_workers} parallel workers...")

            # Submit all year scraping tasks
            future_to_year = {executor.submit(self.scrape_year_parallel, args): args[0] for args in year_args}

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_year):
                year = future_to_year[future]
                try:
                    year_articles = future.result()
                    all_articles.extend(year_articles)
                    print(f"✅ Completed {year}: {len(year_articles)} articles")
                except Exception as e:
                    print(f"❌ Failed {year}: {e}")

        # Remove duplicates
        all_articles = self.remove_duplicates(all_articles)

        print(f"📊 Total articles across all seasons: {len(all_articles)}")

        if len(all_articles) < 10:
            print("⚠️ Low article count, adding guaranteed content...")
            all_articles.extend(self.get_historical_f1_content())

        # Process and upload
        chunks = self.chunker.process_scraped_data(all_articles)
        print(f"✅ Created {len(chunks)} chunks")

        if chunks:
            success = self.pinecone_client.upsert_chunks(chunks)
            if success:
                print(f"🎉 Successfully uploaded {len(chunks)} chunks from {end_year - start_year + 1} seasons!")
                return True

        print("❌ Multi-season update failed")
        return False

    def remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            title_key = f"{article['title'].lower()}_{article.get('year', '')}"
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)

        return unique_articles

    def get_historical_f1_content(self) -> List[Dict]:
        """Get guaranteed historical F1 content"""
        historical_content = [
            {
                'title': 'Lewis Hamilton Championship Years',
                'content': 'Lewis Hamilton won Formula 1 World Championships in 2008, 2014, 2015, 2017, 2018, 2019, and 2020, making him one of the most successful drivers in F1 history.',
                'source': 'Historical F1 Data',
                'type': 'historical',
                'year': 'multiple'
            },
            {
                'title': 'Sebastian Vettel Red Bull Era',
                'content': 'Sebastian Vettel dominated Formula 1 from 2010-2013, winning four consecutive championships with Red Bull Racing during their most successful period.',
                'source': 'Historical F1 Data',
                'type': 'historical',
                'year': 'multiple'
            },
            # Add more historical content...
        ]

        formatted_content = []
        for content in historical_content:
            formatted_content.append({
                'title': content['title'],
                'content': content['content'],
                'url': 'historical_data',
                'source': content['source'],
                'type': content['type'],
                'language': 'en',
                'year': content['year'],
                'scraped_at': datetime.now().isoformat()
            })

        return formatted_content


def main():
    """Main execution function"""
    scraper = MultiSeasonF1Scraper()

    print("Choose scraping option:")
    print("1. Recent seasons (2020-2025) - Fast")
    print("2. Extended range (2015-2025) - Comprehensive")
    print("3. Full historical (2010-2025) - Complete")

    choice = input("Enter choice (1-3): ").strip()

    if choice == '1':
        success = scraper.comprehensive_multi_season_scrape(2020, 2025, max_workers=3)
    elif choice == '2':
        success = scraper.comprehensive_multi_season_scrape(2015, 2025, max_workers=2)
    elif choice == '3':
        success = scraper.comprehensive_multi_season_scrape(2010, 2025, max_workers=2)
    else:
        print("Invalid choice, using default (2020-2025)")
        success = scraper.comprehensive_multi_season_scrape(2020, 2025, max_workers=3)

    if success:
        print("\n✅ Multi-season F1 data scraping completed!")
    else:
        print("\n❌ Multi-season F1 data scraping failed!")


if __name__ == "__main__":
    main()
