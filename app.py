from flask import Flask, render_template, request, jsonify
import random
from config import Config
from src.langchain_pipeline.rag_chain import F1RAGChain
from src.scrapers.wikipedia_scraper import WikipediaF1Scraper
from src.scrapers.f1_official_scraper import run_f1_official_scraper
from src.scrapers.openf1_client import OpenF1Client
from src.data_processing.text_chunker import F1TextChunker
from src.vector_store.pinecone_client import PineconeClient
import datetime
app = Flask(__name__)
app.config.from_object(Config)

# Initialize RAG chain
rag_chain = F1RAGChain()

# Example questions for the home page
EXAMPLE_QUESTIONS = {
    'en': [
        "Who is the current Formula 1 world champion?",
        "What are the latest F1 race results?",
        "Which team has the most F1 constructor championships?",
        "When is the next Formula 1 race?",
        "Who holds the record for most F1 wins?",
        "What are the current driver standings?",
        "Tell me about the history of McLaren F1 team",
        "What is DRS in Formula 1?"
    ],
    'hi': [
        "फॉर्मूला 1 के वर्तमान विश्व चैंपियन कौन हैं?",
        "नवीनतम F1 रेस के परिणाम क्या हैं?",
        "किस टीम के पास सबसे अधिक F1 कंस्ट्रक्टर चैंपियनशिप हैं?",
        "अगली फॉर्मूला 1 रेस कब है?",
        "F1 में सबसे अधिक जीत का रिकॉर्ड किसके पास है?",
        "वर्तमान ड्राइवर स्टैंडिंग क्या है?",
        "मैक्लारेन F1 टीम के इतिहास के बारे में बताएं",
        "फॉर्मूला 1 में DRS क्या है?"
    ]
}


def get_random_questions():
    """Get 4 random example questions (2 English, 2 Hindi)"""
    en_questions = random.sample(EXAMPLE_QUESTIONS['en'], 2)
    hi_questions = random.sample(EXAMPLE_QUESTIONS['hi'], 2)

    return {
        'english': en_questions,
        'hindi': hi_questions
    }


@app.route('/')
def index():
    """Main chat interface"""
    example_questions = get_random_questions()
    return render_template('index.html', example_questions=example_questions)


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with multilingual support"""
    try:
        data = request.get_json()
        user_question = data.get('message', '').strip()

        if not user_question:
            return jsonify({
                'error': 'Please provide a question about Formula 1'
            }), 400

        # Process query through RAG chain
        response = rag_chain.query(user_question)

        return jsonify(response)

    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        return jsonify({
            'error': 'An error occurred while processing your question'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'supported_languages': Config.SUPPORTED_LANGUAGES,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/scrape-and-update', methods=['POST'])
def scrape_and_update():
    """Trigger data scraping and vector store update"""
    try:
        print("🚀 Starting comprehensive F1 data scraping...")

        # Initialize components
        chunker = F1TextChunker()
        pinecone_client = PineconeClient()

        all_scraped_data = []

        # 1. Scrape Wikipedia
        print("📖 Scraping Wikipedia F1 content...")
        wiki_scraper = WikipediaF1Scraper()
        wiki_data = wiki_scraper.scrape_all_f1_content()
        all_scraped_data.extend(wiki_data)

        # 2. Scrape F1 Official
        print("🏎️ Scraping F1 Official website...")
        f1_official_data = run_f1_official_scraper()

        # Convert F1 official data format
        for article in f1_official_data.get('news', []):
            all_scraped_data.append({
                'title': article['title'],
                'content': f"{article['title']}. {article['description']}",
                'url': article['url'],
                'source': 'F1 Official',
                'type': 'news',
                'language': 'en'
            })

        # 3. Fetch OpenF1 API data
        print("📡 Fetching OpenF1 API data...")
        openf1_client = OpenF1Client()
        openf1_data = openf1_client.get_comprehensive_f1_data()

        # Convert OpenF1 data format
        if openf1_data.get('drivers'):
            driver_content = "Current F1 Drivers:\n"
            for driver in openf1_data['drivers']:
                driver_content += f"{driver.get('full_name', 'Unknown')} - Team: {driver.get('team_name', 'Unknown')}\n"

            all_scraped_data.append({
                'title': 'F1 Drivers Database 2025',
                'content': driver_content,
                'url': 'https://api.openf1.org',
                'source': 'OpenF1 API',
                'type': 'data',
                'language': 'en'
            })

        # 4. Process and chunk all data
        print("🔄 Processing and chunking scraped data...")
        chunked_data = chunker.process_scraped_data(all_scraped_data)

        # 5. Update Pinecone vector store
        print("📊 Updating Pinecone vector store...")
        success = pinecone_client.upsert_chunks(chunked_data)

        if success:
            return jsonify({
                'message': 'Successfully updated F1 knowledge base',
                'scraped_documents': len(all_scraped_data),
                'created_chunks': len(chunked_data),
                'sources': ['Wikipedia', 'F1 Official', 'OpenF1 API']
            })
        else:
            return jsonify({
                'error': 'Failed to update vector store'
            }), 500

    except Exception as e:
        print(f"❌ Error in scrape and update: {e}")
        return jsonify({
            'error': f'Scraping failed: {str(e)}'
        }), 500


@app.route('/admin/bulk-add-data', methods=['POST'])
def bulk_add_data():
    """Receive bulk F1 data from Node.js Puppeteer scraper"""
    try:
        data = request.get_json()
        articles = data.get('articles', [])

        if not articles:
            return jsonify({'error': 'No articles provided'}), 400

        # Initialize components
        from src.data_processing.text_chunker import F1TextChunker
        from src.vector_store.pinecone_client import PineconeClient

        chunker = F1TextChunker()
        pinecone_client = PineconeClient()

        # Process all articles
        processed_articles = []
        for article in articles:
            processed_articles.append({
                'title': article.get('title', ''),
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'source': article.get('source', 'Motorsport.com'),
                'type': article.get('type', 'news'),
                'language': 'en',
                'year': str(article.get('year', 2025)),
                'scraped_at': article.get('scraped_at', '')
            })

        # Create chunks
        chunks = chunker.process_scraped_data(processed_articles)

        # Upload to Pinecone
        success = pinecone_client.upsert_chunks(chunks)

        if success:
            return jsonify({
                'message': 'Bulk data processed successfully',
                'articles_processed': len(processed_articles),
                'chunks_created': len(chunks)
            })
        else:
            return jsonify({'error': 'Failed to upload to vector database'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
