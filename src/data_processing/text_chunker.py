import tiktoken
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import Config


class F1TextChunker:
    def __init__(self):
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._tiktoken_len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )

    def _tiktoken_len(self, text: str) -> int:
        """Count tokens using tiktoken"""
        tokens = self.encoding.encode(text)
        return len(tokens)

    def chunk_document(self, document: Dict) -> List[Dict]:
        """Chunk a single document into smaller pieces"""
        try:
            content = document.get('content', '')
            title = document.get('title', '')

            # Prepare text for chunking
            full_text = f"Title: {title}\n\n{content}"

            # Split text into chunks
            chunks = self.text_splitter.split_text(full_text)

            chunked_docs = []
            for i, chunk in enumerate(chunks):
                chunk_doc = {
                    'id': f"{document.get('url', 'unknown')}_{i}",
                    'content': chunk,
                    'metadata': {
                        'source': document.get('source', 'Unknown'),
                        'url': document.get('url', ''),
                        'title': title,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'type': document.get('type', 'text'),
                        'language': document.get('language', 'en'),
                        'section': document.get('section', ''),
                        'token_count': self._tiktoken_len(chunk)
                    }
                }
                chunked_docs.append(chunk_doc)

            return chunked_docs

        except Exception as e:
            print(f"❌ Error chunking document: {e}")
            return []

    def chunk_wikipedia_sections(self, wikipedia_doc: Dict) -> List[Dict]:
        """Special chunking for Wikipedia documents with sections"""
        try:
            chunked_docs = []
            title = wikipedia_doc.get('title', '')
            base_url = wikipedia_doc.get('url', '')

            # Chunk main summary
            if wikipedia_doc.get('summary'):
                summary_text = f"Title: {title}\n\nSummary: {wikipedia_doc['summary']}"
                summary_chunks = self.text_splitter.split_text(summary_text)

                for i, chunk in enumerate(summary_chunks):
                    chunk_doc = {
                        'id': f"{base_url}_summary_{i}",
                        'content': chunk,
                        'metadata': {
                            'source': wikipedia_doc.get('source', 'Wikipedia'),
                            'url': base_url,
                            'title': title,
                            'chunk_index': i,
                            'type': 'encyclopedia_summary',
                            'language': 'en',
                            'section': 'Summary',
                            'token_count': self._tiktoken_len(chunk)
                        }
                    }
                    chunked_docs.append(chunk_doc)

            # Chunk individual sections
            sections = wikipedia_doc.get('sections', [])
            for section_idx, section in enumerate(sections):
                section_name = section.get('section', f'Section_{section_idx}')
                section_content = section.get('content', '')

                if section_content:
                    section_text = f"Title: {title}\nSection: {section_name}\n\n{section_content}"
                    section_chunks = self.text_splitter.split_text(section_text)

                    for i, chunk in enumerate(section_chunks):
                        chunk_doc = {
                            'id': f"{base_url}_section_{section_idx}_{i}",
                            'content': chunk,
                            'metadata': {
                                'source': wikipedia_doc.get('source', 'Wikipedia'),
                                'url': base_url,
                                'title': title,
                                'chunk_index': i,
                                'type': 'encyclopedia_section',
                                'language': 'en',
                                'section': section_name,
                                'token_count': self._tiktoken_len(chunk)
                            }
                        }
                        chunked_docs.append(chunk_doc)

            return chunked_docs

        except Exception as e:
            print(f"❌ Error chunking Wikipedia document: {e}")
            return []

    def process_scraped_data(self, scraped_data: List[Dict]) -> List[Dict]:
        """Process all scraped data into chunks"""
        all_chunks = []

        for doc in scraped_data:
            try:
                if doc.get('source') == 'Wikipedia' and doc.get('sections'):
                    # Special handling for Wikipedia with sections
                    chunks = self.chunk_wikipedia_sections(doc)
                else:
                    # Regular chunking for other documents
                    chunks = self.chunk_document(doc)

                all_chunks.extend(chunks)

            except Exception as e:
                print(f"❌ Error processing document {doc.get('title', 'Unknown')}: {e}")
                continue

        print(f"📄 Created {len(all_chunks)} chunks from {len(scraped_data)} documents")
        return all_chunks
