import wikipedia
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time


class WikipediaF1Scraper:
    def __init__(self):
        wikipedia.set_lang("en")

    def get_f1_related_pages(self) -> List[str]:
        """Fixed F1 topics with correct spellings"""
        f1_topics = [
            "Formula One",  # Fixed from "Formulate One"
            "Formula One drivers",
            "Formula One constructors",
            "2024 Formula One World Championship",  # 2024 exists, 2025 doesn't yet
            "List of Formula One World Drivers' Champions",
            "List of Formula One circuits",
            "Formula One regulations",
            "Formula One car",
            "Max Verstappen",
            "Lewis Hamilton",
            "Charles Leclerc",  # Fixed from "Charle Leclerc"
            "Lando Norris",  # Fixed from "Landor Norris"
            "Oscar Piastri",
            "Red Bull Racing",
            "Mercedes-AMG Petronas Formula One Team",
            "Scuderia Ferrari",
            "McLaren",  # Fixed from "MC Lauren"
            "Monaco Grand Prix",
            "British Grand Prix",
            "Italian Grand Prix",
            "Formula One safety",
            "DRS (Formula One)",
            "Energy Recovery System",  # Instead of KERS
            "Turbo-hybrid"
        ]
        return f1_topics

    # ... rest of the methods remain the same

    def scrape_page_content(self, page_title: str) -> Dict:
        """Scrape content from a Wikipedia page"""
        try:
            print(f"📖 Scraping Wikipedia: {page_title}")

            page = wikipedia.page(page_title)

            content_data = {
                'title': page.title,
                'content': page.content,
                'url': page.url,
                'summary': page.summary,
                'source': 'Wikipedia',
                'type': 'encyclopedia',
                'language': 'en'
            }

            # Add sections for better chunking
            sections = []
            current_section = ""
            current_content = ""

            lines = page.content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('='):
                    current_content += line + " "
                elif line.startswith('=') and current_content:
                    if current_section:
                        sections.append({
                            'section': current_section,
                            'content': current_content.strip()
                        })
                    current_section = line.strip('= ')
                    current_content = ""

            if current_content and current_section:
                sections.append({
                    'section': current_section,
                    'content': current_content.strip()
                })

            content_data['sections'] = sections

            time.sleep(1)  # Rate limiting
            return content_data

        except wikipedia.exceptions.DisambiguationError as e:
            # Try the first option
            try:
                page = wikipedia.page(e.options[0])
                return self.scrape_page_content(e.options[0])
            except:
                print(f"❌ Could not resolve disambiguation for {page_title}")
                return None
        except Exception as e:
            print(f"❌ Error scraping {page_title}: {e}")
            return None

    def scrape_all_f1_content(self) -> List[Dict]:
        """Scrape all F1-related Wikipedia content"""
        f1_pages = self.get_f1_related_pages()
        scraped_content = []

        for page_title in f1_pages:
            content = self.scrape_page_content(page_title)
            if content:
                scraped_content.append(content)

        print(f"✅ Scraped {len(scraped_content)} Wikipedia pages")
        return scraped_content
