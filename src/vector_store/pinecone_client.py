from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import SentenceTransformerEmbeddings
from typing import List, Dict
from config import Config
import time


class PineconeClient:
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.PINECONE_INDEX_NAME

        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=Config.EMBEDDING_MODEL
        )

        # Create or connect to index
        self._setup_index()

        # Initialize vector store
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )

    def _setup_index(self):
        """Create Pinecone index if it doesn't exist"""
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]

            if self.index_name not in existing_indexes:
                print(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                time.sleep(30)  # Wait for index to be ready
                print("✅ Index created successfully")
            else:
                print(f"✅ Using existing index: {self.index_name}")

        except Exception as e:
            print(f"❌ Error setting up index: {e}")
            raise

    def upsert_chunks(self, chunks: List[Dict]) -> bool:
        """Upload document chunks to Pinecone"""
        try:
            print(f"📊 Uploading {len(chunks)} chunks to Pinecone...")

            # Convert chunks to format expected by LangChain
            documents = []
            metadatas = []
            ids = []

            for chunk in chunks:
                documents.append(chunk['content'])
                metadatas.append(chunk['metadata'])
                ids.append(str(chunk['id']))

            # Add documents to vector store
            self.vector_store.add_texts(
                texts=documents,
                metadatas=metadatas,
                ids=ids
            )

            print("✅ Successfully uploaded chunks to Pinecone")
            return True

        except Exception as e:
            print(f"❌ Error uploading chunks: {e}")
            return False

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)

            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                })

            return formatted_results

        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get index statistics"""
        try:
            index = self.pc.Index(self.index_name)
            return index.describe_index_stats()
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
