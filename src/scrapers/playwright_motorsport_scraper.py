import asyncio
from playwright.async_api import async_playwright
import json
import sys
import os
from datetime import datetime

# Add your project path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.data_processing.text_chunker import F1TextChunker
from src.vector_store.pinecone_client import PineconeClient


async def scrape_and_store_motorsport():
    """Scrape Motorsport.com and store in vector database"""

    # Initialize components
    chunker = F1TextChunker()
    pinecone_client = PineconeClient()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        base_routes = [
            'https://www.motorsport.com/f1/news',
            'https://www.motorsport.com/f1/results',
            'https://www.motorsport.com/f1/standings'
        ]
        years = [2023, 2024, 2025]

        all_articles = []

        for base_url in base_routes:
            for year in years:
                url = f"{base_url}/{year}"

                try:
                    page = await browser.new_page()
                    await page.goto(url, wait_until='domcontentloaded')
                    await page.wait_for_timeout(2000)

                    # Enhanced extraction with better selectors
                    articles = await page.evaluate('''() => {
                        const elements = document.querySelectorAll(`
                            article,
                            [class*="news-item"],
                            [class*="article"],
                            [class*="listing"],
                            .ms-item,
                            h1, h2, h3
                        `);

                        const results = [];
                        elements.forEach((el, index) => {
                            if (index < 20) {  // Limit per page
                                const title = el.innerText?.trim() || el.textContent?.trim();
                                if (title && title.length > 15) {  // Filter short titles
                                    results.push({
                                        title: title.substring(0, 200),
                                        content: title.substring(0, 500),
                                        url: window.location.href
                                    });
                                }
                            }
                        });
                        return results;
                    }''')

                    # Format for your pipeline
                    for article in articles:
                        all_articles.append({
                            'title': article['title'],
                            'content': article['content'],
                            'url': article['url'],
                            'source': 'Motorsport.com Playwright',
                            'type': 'news' if '/news/' in url else ('results' if '/results/' in url else 'standings'),
                            'language': 'en',
                            'year': str(year),
                            'scraped_at': datetime.now().isoformat()
                        })

                    print(f"✅ Scraped {len(articles)} from {url}")
                    await page.close()

                except Exception as e:
                    print(f"❌ Error scraping {url}: {e}")

        await browser.close()

        print(f"📊 Total scraped: {len(all_articles)} articles")

        if all_articles:
            # Process into chunks
            print("🔄 Processing into chunks...")
            chunks = chunker.process_scraped_data(all_articles)
            print(f"✅ Created {len(chunks)} chunks")

            # Upload to Pinecone
            print("⬆️ Uploading to Pinecone vector database...")
            success = pinecone_client.upsert_chunks(chunks)

            if success:
                print(f"🎉 Successfully stored {len(chunks)} chunks in vector database!")
                return len(chunks)
            else:
                print("❌ Failed to upload to vector database")
                return 0
        else:
            print("❌ No articles scraped")
            return 0


# Run it
if __name__ == "__main__":
    chunks_stored = asyncio.run(scrape_and_store_motorsport())
    print(f"\n📈 Final Result: {chunks_stored} chunks stored in vector database")
