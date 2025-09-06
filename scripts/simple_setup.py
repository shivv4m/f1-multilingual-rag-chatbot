#!/usr/bin/env python3
"""
Simplified F1 RAG system setup script
"""

import sys
import os

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def create_sample_data():
    """Create sample F1 data for testing"""
    sample_data = [
        {
            'id': 'f1_sample_1',
            'content': 'Max Verstappen is a Dutch Formula 1 racing driver who currently competes for Red Bull Racing. He won the Formula 1 World Drivers Championship in 2021, 2022, and 2023.',
            'metadata': {
                'title': 'Max Verstappen Profile',
                'source': 'Sample Data',
                'type': 'driver_profile',
                'language': 'en'
            }
        },
        {
            'id': 'f1_sample_2',
            'content': 'The 2025 Formula 1 World Championship features 24 races across different continents. The season includes classic circuits like Monaco, Silverstone, and Spa-Francorchamps.',
            'metadata': {
                'title': '2025 F1 Season',
                'source': 'Sample Data',
                'type': 'season_info',
                'language': 'en'
            }
        },
        {
            'id': 'f1_sample_3',
            'content': 'Lewis Hamilton is a British Formula 1 driver who has won seven World Championships. He currently drives for Mercedes and holds multiple F1 records.',
            'metadata': {
                'title': 'Lewis Hamilton Profile',
                'source': 'Sample Data',
                'type': 'driver_profile',
                'language': 'en'
            }
        }
    ]

    return sample_data


def main():
    print("🏎️ Setting up Simple F1 RAG System...")

    try:
        # Import after adding to path
        from src.vector_store.pinecone_client import PineconeClient

        print("📊 Initializing Pinecone client...")
        pinecone_client = PineconeClient()

        print("📝 Creating sample F1 data...")
        sample_chunks = create_sample_data()

        print("⬆️ Uploading to Pinecone...")
        success = pinecone_client.upsert_chunks(sample_chunks)

        if success:
            print("🎉 Simple setup completed successfully!")
            print(f"📈 Uploaded {len(sample_chunks)} sample documents")

            # Test search
            print("🔍 Testing search functionality...")
            results = pinecone_client.search("Max Verstappen", k=2)
            print(f"✅ Search test returned {len(results)} results")

        else:
            print("❌ Setup failed during upload")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure all required packages are installed and the directory structure is correct")
    except Exception as e:
        print(f"❌ Setup error: {e}")


if __name__ == "__main__":
    main()
