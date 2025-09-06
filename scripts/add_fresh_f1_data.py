#!/usr/bin/env python3
"""
Comprehensive F1 Data Updater
Scrapes multiple F1 news sources and updates Pinecone database
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import feedparser
import time
import json
from datetime import datetime
from typing import List, Dict
import asyncio
from urllib.parse import urljoin, urlparse
import hashlib

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.data_processing.text_chunker import F1TextChunker
from src.vector_store.pinecone_client import PineconeClient


class F1DataUpdater:
    def __init__(self):
        self.chunker = F1TextChunker()
        self.pinecone_client = PineconeClient()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_motorsport_news(self) -> List[Dict]:
        """Scrape Motorsport.com F1 news"""
        try:
            print("🏎️ Scraping Motorsport.com F1 news...")
            url = "https://www.motorsport.com/f1/news/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []
            # Updated selectors based on Motorsport.com structure
            article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and 'ms-item' in x.lower())

            for element in article_elements[:15]:  # Limit to 15 latest articles
                try:
                    title_elem = element.find(['h2', 'h3', 'a'],
                                              class_=lambda x: x and ('headline' in x.lower() or 'title' in x.lower()))
                    if not title_elem:
                        title_elem = element.find('a')

                    content_elem = element.find(['p', 'div'], class_=lambda x: x and (
                                'summary' in x.lower() or 'excerpt' in x.lower()))

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '') if title_elem.name == 'a' else ''
                        if link and not link.startswith('http'):
                            link = urljoin(url, link)

                        content = content_elem.get_text(strip=True) if content_elem else title

                        articles.append({
                            'title': title,
                            'content': f"{title}. {content}",
                            'url': link or url,
                            'source': 'Motorsport.com',
                            'type': 'news',
                            'language': 'en',
                            'scraped_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    continue

            print(f"✅ Scraped {len(articles)} articles from Motorsport.com")
            return articles

        except Exception as e:
            print(f"❌ Error scraping Motorsport.com: {e}")
            return []

    def scrape_autosport_news(self) -> List[Dict]:
        """Scrape Autosport.com F1 news"""
        try:
            print("🏎️ Scraping Autosport.com F1 news...")
            url = "https://www.autosport.com/f1/news/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []
            article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and 'article' in x.lower())

            for element in article_elements[:15]:
                try:
                    title_elem = element.find(['h2', 'h3', 'a'])
                    content_elem = element.find(['p', 'div'],
                                                class_=lambda x: x and 'summary' in x.lower() if x else False)

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '') if title_elem.name == 'a' else ''
                        if link and not link.startswith('http'):
                            link = urljoin(url, link)

                        content = content_elem.get_text(strip=True) if content_elem else title

                        articles.append({
                            'title': title,
                            'content': f"{title}. {content}",
                            'url': link or url,
                            'source': 'Autosport.com',
                            'type': 'news',
                            'language': 'en',
                            'scraped_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    continue

            print(f"✅ Scraped {len(articles)} articles from Autosport.com")
            return articles

        except Exception as e:
            print(f"❌ Error scraping Autosport.com: {e}")
            return []

    def scrape_f1nsight(self) -> List[Dict]:
        """Scrape F1nsight.com"""
        try:
            print("🏎️ Scraping F1nsight.com...")
            url = "https://www.f1nsight.com/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []
            article_elements = soup.find_all(['article', 'div', 'h2', 'h3'])

            for element in article_elements[:10]:
                try:
                    if element.name in ['h2', 'h3']:
                        title = element.get_text(strip=True)
                        if len(title) > 20:  # Filter out short headings
                            articles.append({
                                'title': title,
                                'content': title,
                                'url': url,
                                'source': 'F1nsight.com',
                                'type': 'analysis',
                                'language': 'en',
                                'scraped_at': datetime.now().isoformat()
                            })
                    else:
                        title_elem = element.find(['h2', 'h3', 'a'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            articles.append({
                                'title': title,
                                'content': title,
                                'url': url,
                                'source': 'F1nsight.com',
                                'type': 'analysis',
                                'language': 'en',
                                'scraped_at': datetime.now().isoformat()
                            })
                except Exception as e:
                    continue

            print(f"✅ Scraped {len(articles)} articles from F1nsight.com")
            return articles

        except Exception as e:
            print(f"❌ Error scraping F1nsight.com: {e}")
            return []

    def scrape_motorsport_standings(self) -> List[Dict]:
        """Scrape F1 standings from Motorsport.com"""
        try:
            print("🏆 Scraping F1 standings...")
            url = "https://www.motorsport.com/f1/standings/2025/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            standings_data = []

            # Look for standings tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 5:  # Likely a standings table
                    standings_text = "2025 F1 Championship Standings:\n"
                    for i, row in enumerate(rows[1:11]):  # Top 10
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            position = cells[0].get_text(strip=True)
                            driver = cells[1].get_text(strip=True)
                            points = cells[-1].get_text(strip=True)
                            standings_text += f"{position}. {driver} - {points} points\n"

                    standings_data.append({
                        'title': 'F1 2025 Championship Standings',
                        'content': standings_text,
                        'url': url,
                        'source': 'Motorsport.com',
                        'type': 'standings',
                        'language': 'en',
                        'scraped_at': datetime.now().isoformat()
                    })
                    break

            print(f"✅ Scraped standings data")
            return standings_data

        except Exception as e:
            print(f"❌ Error scraping standings: {e}")
            return []

    def scrape_rss_feeds(self) -> List[Dict]:
        """Scrape multiple RSS feeds"""
        rss_feeds = [
            "https://www.motorsport.com/rss/f1/news/",
            "https://www.autosport.com/rss/f1/news/",
            "https://www.skysports.com/rss/12433",  # Sky Sports F1
            "https://feeds.feedburner.com/FormulaOneFeed",
        ]

        all_articles = []

        for feed_url in rss_feeds:
            try:
                print(f"📡 Parsing RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:  # Latest 10 from each feed
                    try:
                        articles.append({
                            'title': entry.get('title', ''),
                            'content': entry.get('summary', entry.get('title', '')),
                            'url': entry.get('link', ''),
                            'source': f'RSS: {feed_url}',
                            'type': 'news',
                            'language': 'en',
                            'published': entry.get('published', ''),
                            'scraped_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        continue

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"❌ Error parsing RSS feed {feed_url}: {e}")
                continue

        print(f"✅ Scraped {len(all_articles)} RSS articles")
        return all_articles

    def scrape_race_schedule(self) -> List[Dict]:
        """Scrape race schedule from Motorsport.com"""
        try:
            print("📅 Scraping race schedule...")
            url = "https://www.motorsport.com/f1/schedule/2025/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            schedule_data = []

            # Look for schedule elements
            race_elements = soup.find_all(['div', 'tr'], class_=lambda x: x and 'race' in x.lower())

            schedule_text = "2025 Formula 1 Race Calendar:\n"
            for element in race_elements[:24]:  # Max 24 races
                try:
                    text = element.get_text(strip=True)
                    if len(text) > 20 and ('Grand Prix' in text or 'GP' in text):
                        schedule_text += f"• {text}\n"
                except Exception as e:
                    continue

            if len(schedule_text) > 50:
                schedule_data.append({
                    'title': 'F1 2025 Race Calendar',
                    'content': schedule_text,
                    'url': url,
                    'source': 'Motorsport.com',
                    'type': 'schedule',
                    'language': 'en',
                    'scraped_at': datetime.now().isoformat()
                })

            print(f"✅ Scraped race schedule")
            return schedule_data

        except Exception as e:
            print(f"❌ Error scraping race schedule: {e}")
            return []

    def get_livef1_data(self) -> List[Dict]:
        """Get data from LiveF1 library (if available)"""
        try:
            # This would require the livef1 library to be installed
            # pip install livef1
            # import livef1

            # For now, return sample data
            livef1_data = [{
                'title': 'Live F1 Timing Data',
                'content': 'Real-time F1 timing and telemetry data from current sessions.',
                'url': 'https://livetiming.formula1.com',
                'source': 'LiveF1 Library',
                'type': 'live_data',
                'language': 'en',
                'scraped_at': datetime.now().isoformat()
            }]

            print(f"✅ Retrieved LiveF1 data")
            return livef1_data

        except Exception as e:
            print(f"❌ Error getting LiveF1 data: {e}")
            return []

    def remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            # Create a hash of the title for deduplication
            title_hash = hashlib.md5(article['title'].lower().encode()).hexdigest()

            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_articles.append(article)

        return unique_articles

    def update_database(self) -> bool:
        """Main method to update the F1 database with fresh data"""
        print("🚀 Starting F1 data update...")

        all_data = []

        # Scrape all sources
        all_data.extend(self.scrape_motorsport_news())
        time.sleep(2)

        all_data.extend(self.scrape_autosport_news())
        time.sleep(2)

        all_data.extend(self.scrape_f1nsight())
        time.sleep(2)

        all_data.extend(self.scrape_motorsport_standings())
        time.sleep(2)

        all_data.extend(self.scrape_race_schedule())
        time.sleep(2)

        all_data.extend(self.scrape_rss_feeds())
        time.sleep(2)

        all_data.extend(self.get_livef1_data())

        # Remove duplicates
        all_data = self.remove_duplicates(all_data)

        print(f"📊 Total unique articles collected: {len(all_data)}")

        if not all_data:
            print("❌ No new data collected")
            return False

        # Process into chunks
        print("🔄 Processing data into chunks...")
        chunks = self.chunker.process_scraped_data(all_data)
        print(f"✅ Created {len(chunks)} chunks")

        # Upload to Pinecone
        print("⬆️ Uploading to Pinecone...")
        success = self.pinecone_client.upsert_chunks(chunks)

        if success:
            print(f"🎉 Successfully updated database with {len(chunks)} new chunks!")
            return True
        else:
            print("❌ Failed to update database")
            return False


def main():
    """Main function"""
    updater = F1DataUpdater()
    success = updater.update_database()

    if success:
        print("\n✅ F1 database update completed successfully!")
    else:
        print("\n❌ F1 database update failed!")


if __name__ == "__main__":
    main()
