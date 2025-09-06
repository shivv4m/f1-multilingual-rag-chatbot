#!/usr/bin/env python3
"""
Complete F1 RAG system setup script
"""

import sys
import os

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now import the modules
from src.scrapers.wikipedia_scraper import WikipediaF1Scraper
from src.scrapers.f1_official_scraper import run_f1_official_scraper
from src.scrapers.openf1_client import OpenF1Client
from src.data_processing.text_chunker import F1TextChunker
from src.vector_store.pinecone_client import PineconeClient


def main():
    print("🏎️ Setting up Complete F1 RAG System...")

    # Initialize components
    chunker = F1TextChunker()
    pinecone_client = PineconeClient()

    all_data = []

    # Step 1: Wikipedia (with error handling)
    print("📖 Step 1: Scraping Wikipedia F1 content...")
    try:
        wiki_scraper = WikipediaF1Scraper()
        wiki_data = wiki_scraper.scrape_all_f1_content()
        all_data.extend(wiki_data)
        print(f"✅ Scraped {len(wiki_data)} Wikipedia articles")
    except Exception as e:
        print(f"⚠️ Wikipedia scraping failed: {e}")

    # Step 2: F1 Official (with error handling)
    print("🏎️ Step 2: Scraping F1 Official website...")
    try:
        f1_official_data = run_f1_official_scraper()

        for article in f1_official_data.get('news', []):
            all_data.append({
                'title': article['title'],
                'content': f"{article['title']}. {article['description']}",
                'url': article['url'],
                'source': 'F1 Official',
                'type': 'news',
                'language': 'en'
            })
        print(f"✅ Scraped {len(f1_official_data.get('news', []))} F1 official articles")

    except Exception as e:
        print(f"⚠️ F1 Official scraping failed: {e}")
        # Add sample data to continue
        all_data.append({
            'title': 'F1 Sample News',
            'content': 'Formula 1 sample content for testing the RAG system.',
            'url': 'https://formula1.com',
            'source': 'Sample Data',
            'type': 'news',
            'language': 'en'
        })

    # Step 3: OpenF1 API (more reliable)
    print("📡 Step 3: Fetching OpenF1 API data...")
    try:
        from src.scrapers.openf1_client import OpenF1Client
        openf1_client = OpenF1Client()
        openf1_data = openf1_client.get_comprehensive_f1_data()
        openf1_formatted = openf1_client.format_for_rag(openf1_data)
        all_data.extend(openf1_formatted)
        print(f"✅ Retrieved {len(openf1_formatted)} OpenF1 documents")
    except Exception as e:
        print(f"⚠️ OpenF1 API failed: {e}")

    # Continue with processing...
    print("🔄 Step 4: Chunking all data...")
    if all_data:
        chunks = chunker.process_scraped_data(all_data)
        print(f"✅ Created {len(chunks)} chunks")

        print("📊 Step 5: Uploading to Pinecone...")
        success = pinecone_client.upsert_chunks(chunks)

        if success:
            print("🎉 Setup completed successfully!")
            print(f"📈 Total documents: {len(all_data)}")
            print(f"📈 Total chunks: {len(chunks)}")
        else:
            print("❌ Setup failed during vector upload")
    else:
        print("❌ No data was scraped successfully")


if __name__ == "__main__":
    main()
