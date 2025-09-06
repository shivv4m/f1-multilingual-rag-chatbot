import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

    # API Keys
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    SPORTSMONKS_API_KEY = os.getenv('SPORTSMONKS_API_KEY')

    # Pinecone
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'f1-multilingual-kb')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')

    # Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')

    # Chunking Configuration
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 512))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 100))

    # RAG Configuration
    TOP_K = 10
    SIMILARITY_THRESHOLD = 0.3

    # Supported Languages
    SUPPORTED_LANGUAGES = ['en', 'hi']
