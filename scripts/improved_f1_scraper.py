#!/usr/bin/env python3
"""
Enhanced F1 Data Scraper with Updated Selectors and Better Coverage
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
from urllib.parse import urljoin
import hashlib

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.data_processing.text_chunker import F1TextChunker
from src.vector_store.pinecone_client import PineconeClient


class EnhancedF1Scraper:
    def __init__(self):
        self.chunker = F1TextChunker()
        self.pinecone_client = PineconeClient()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_motorsport_enhanced(self) -> List[Dict]:
        """Enhanced Motorsport.com scraper with multiple selectors"""
        try:
            print("🏎️ Enhanced Motorsport.com scraping...")
            url = "https://www.motorsport.com/f1/news/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []

            # Try multiple selector strategies
            selectors = [
                # Modern selectors
                {'container': 'article', 'title': 'h1, h2, h3', 'content': 'p'},
                {'container': '[class*="news"]', 'title': '[class*="headline"], [class*="title"]',
                 'content': '[class*="summary"], [class*="excerpt"]'},
                {'container': '[class*="item"]', 'title': 'a', 'content': 'p'},
                # Fallback selectors
                {'container': 'div', 'title': 'a[href*="/f1/news/"]', 'content': 'p'},
            ]

            for selector_set in selectors:
                containers = soup.select(selector_set['container'])
                print(f"Found {len(containers)} containers with selector: {selector_set['container']}")

                for container in containers[:20]:  # Process up to 20
                    try:
                        title_elem = container.select_one(selector_set['title'])
                        content_elem = container.select_one(selector_set['content'])

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if len(title) > 10:  # Filter very short titles
                                link = title_elem.get('href', '') if title_elem.name == 'a' else ''
                                if link and not link.startswith('http'):
                                    link = urljoin(url, link)

                                content = content_elem.get_text(strip=True) if content_elem else title

                                articles.append({
                                    'title': title,
                                    'content': f"{title}. {content}",
                                    'url': link or url,
                                    'source': 'Motorsport.com Enhanced',
                                    'type': 'news',
                                    'language': 'en',
                                    'scraped_at': datetime.now().isoformat()
                                })
                    except Exception as e:
                        continue

                if articles:  # If we found articles, break
                    break

            print(f"✅ Enhanced Motorsport: {len(articles)} articles")
            return articles

        except Exception as e:
            print(f"❌ Enhanced Motorsport error: {e}")
            return []

    def scrape_autosport_enhanced(self) -> List[Dict]:
        """Enhanced Autosport.com scraper"""
        try:
            print("🏎️ Enhanced Autosport scraping...")
            url = "https://www.autosport.com/f1/news/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            articles = []

            # Look for any elements containing F1 news
            potential_articles = soup.find_all(['div', 'article', 'section'])

            for element in potential_articles:
                try:
                    # Look for links that might be article titles
                    links = element.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if '/f1/' in href or '/news/' in href:
                            title = link.get_text(strip=True)
                            if len(title) > 15:  # Reasonable title length
                                full_url = urljoin(url, href)

                                articles.append({
                                    'title': title,
                                    'content': title,
                                    'url': full_url,
                                    'source': 'Autosport.com Enhanced',
                                    'type': 'news',
                                    'language': 'en',
                                    'scraped_at': datetime.now().isoformat()
                                })
                except Exception as e:
                    continue

            # Remove duplicates based on title
            seen_titles = set()
            unique_articles = []
            for article in articles:
                title_lower = article['title'].lower()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    unique_articles.append(article)

            print(f"✅ Enhanced Autosport: {len(unique_articles)} unique articles")
            return unique_articles[:15]  # Limit to 15

        except Exception as e:
            print(f"❌ Enhanced Autosport error: {e}")
            return []

    def scrape_working_rss_feeds(self) -> List[Dict]:
        """Scrape verified working RSS feeds"""
        working_feeds = [
            "https://www.skysports.com/rss/12433",  # Sky Sports F1
            "https://www.bbc.com/sport/formula1/rss.xml",  # BBC F1
            "https://feeds.feedburner.com/f1fanatic",  # F1 Fanatic
        ]

        articles = []

        for feed_url in working_feeds:
            try:
                print(f"📡 Parsing RSS: {feed_url}")
                feed = feedparser.parse(feed_url)

                if hasattr(feed, 'entries') and feed.entries:
                    for entry in feed.entries[:8]:  # Top 8 from each
                        try:
                            title = entry.get('title', '').strip()
                            if title:
                                articles.append({
                                    'title': title,
                                    'content': entry.get('summary', title)[:500],  # Limit content
                                    'url': entry.get('link', ''),
                                    'source': f'RSS: {feed_url}',
                                    'type': 'news',
                                    'language': 'en',
                                    'published': entry.get('published', ''),
                                    'scraped_at': datetime.now().isoformat()
                                })
                        except Exception as e:
                            continue

                    print(f"✅ RSS {feed_url}: {len(feed.entries)} entries found")
                else:
                    print(f"⚠️ RSS {feed_url}: No entries found")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"❌ RSS {feed_url} failed: {e}")
                continue

        print(f"✅ Total RSS articles: {len(articles)}")
        return articles

    def scrape_additional_sources(self) -> List[Dict]:
        """Scrape additional F1 sources"""
        additional_articles = []

        # Add F1 Wikipedia current events
        try:
            wiki_url = "https://en.wikipedia.org/wiki/2025_Formula_One_World_Championship"
            response = self.session.get(wiki_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract race results or current info
            paragraphs = soup.find_all('p')
            content_chunks = []

            for p in paragraphs[:10]:
                text = p.get_text(strip=True)
                if len(text) > 50 and 'Formula One' in text:
                    content_chunks.append(text)

            if content_chunks:
                combined_content = ' '.join(content_chunks[:3])
                additional_articles.append({
                    'title': '2025 Formula One World Championship Update',
                    'content': combined_content,
                    'url': wiki_url,
                    'source': 'Wikipedia Current',
                    'type': 'championship_info',
                    'language': 'en',
                    'scraped_at': datetime.now().isoformat()
                })

        except Exception as e:
            print(f"❌ Wikipedia scraping failed: {e}")

        # Add manual F1 content for guaranteed results
        manual_content = [
            {
                'title': 'F1 2025 Season Technical Regulations Update',
                'content': 'The 2025 Formula 1 season continues with ground effect aerodynamics, hybrid power units, and strict cost cap regulations. Teams are focusing on aerodynamic efficiency and weight optimization.',
                'source': 'Manual F1 Update',
                'type': 'regulations'
            },
            {
                'title': 'Current F1 Driver Market Analysis',
                'content': 'The F1 driver market remains active with potential moves for 2026. Key drivers like Max Verstappen, Lewis Hamilton, and Charles Leclerc continue to be focal points for team strategies.',
                'source': 'Manual F1 Update',
                'type': 'driver_market'
            },
            {
                'title': 'F1 Sprint Format Races 2025',
                'content': 'The 2025 Formula 1 season features sprint format weekends at select circuits. These shorter races provide additional points and excitement for both drivers and fans.',
                'source': 'Manual F1 Update',
                'type': 'race_format'
            }
        ]

        for content in manual_content:
            additional_articles.append({
                'title': content['title'],
                'content': content['content'],
                'url': 'manual_entry',
                'source': content['source'],
                'type': content['type'],
                'language': 'en',
                'scraped_at': datetime.now().isoformat()
            })

        print(f"✅ Additional sources: {len(additional_articles)} articles")
        return additional_articles

    def comprehensive_update(self) -> bool:
        """Run comprehensive F1 data update"""
        print("🚀 Starting comprehensive F1 data update...")

        all_articles = []

        # Scrape all sources
        all_articles.extend(self.scrape_motorsport_enhanced())
        time.sleep(2)

        all_articles.extend(self.scrape_autosport_enhanced())
        time.sleep(2)

        all_articles.extend(self.scrape_working_rss_feeds())
        time.sleep(2)

        all_articles.extend(self.scrape_additional_sources())

        # Remove duplicates
        all_articles = self.remove_duplicates(all_articles)

        print(f"📊 Total unique articles: {len(all_articles)}")

        if len(all_articles) < 5:
            print("⚠️ Low article count, adding more manual content...")
            # Add more guaranteed content
            all_articles.extend(self.get_guaranteed_f1_content())

        # Process and upload
        chunks = self.chunker.process_scraped_data(all_articles)
        print(f"✅ Created {len(chunks)} chunks")

        if chunks:
            success = self.pinecone_client.upsert_chunks(chunks)
            if success:
                print(f"🎉 Successfully uploaded {len(chunks)} chunks!")
                return True

        print("❌ Update failed")
        return False

    def remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles"""
        seen = set()
        unique = []

        for article in articles:
            # Create hash of title
            title_hash = hashlib.md5(article['title'].lower().encode()).hexdigest()
            if title_hash not in seen:
                seen.add(title_hash)
                unique.append(article)

        return unique

    def get_guaranteed_f1_content(self) -> List[Dict]:
        """Get guaranteed F1 content to ensure minimum data"""
        return [
            {
                'title': 'Formula 1 Aerodynamics Explained',
                'content': 'Modern F1 cars use ground effect aerodynamics to generate downforce. The floor design creates low pressure underneath the car, sucking it to the track for better grip and cornering speeds.',
                'url': 'guaranteed_content',
                'source': 'F1 Technical Guide',
                'type': 'technical',
                'language': 'en',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'title': 'F1 Hybrid Power Unit Technology',
                'content': 'F1 hybrid power units combine a 1.6L V6 turbo engine with MGU-H and MGU-K energy recovery systems. These systems harvest energy from exhaust heat and braking to provide additional power.',
                'url': 'guaranteed_content',
                'source': 'F1 Technical Guide',
                'type': 'technical',
                'language': 'en',
                'scraped_at': datetime.now().isoformat()
            }
        ]


def main():
    scraper = EnhancedF1Scraper()
    success = scraper.comprehensive_update()

    if success:
        print("\n✅ Enhanced F1 data update completed!")
    else:
        print("\n❌ Enhanced F1 data update failed!")


if __name__ == "__main__":
    main()
