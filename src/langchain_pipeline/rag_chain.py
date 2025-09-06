from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import SentenceTransformerEmbeddings
from src.llm.language_detector import LanguageHandler
from config import Config
from typing import Dict
import os


class F1RAGChain:
    def __init__(self):
        # Initialize language handler
        self.language_handler = LanguageHandler()

        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=Config.EMBEDDING_MODEL
        )

        # Initialize Groq LLM
        self.llm = ChatGroq(
            groq_api_key=Config.GROQ_API_KEY,
            model_name=Config.GROQ_MODEL,
            temperature=0.7
        )

        # Initialize Pinecone vector store
        self.vector_store = PineconeVectorStore(
            index_name=Config.PINECONE_INDEX_NAME,
            embedding=self.embeddings
        )

        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={'k': Config.TOP_K}
        )

        self.setup_prompt_templates()

    def setup_prompt_templates(self):
        """Setup concise multilingual prompt templates"""
        self.prompt_templates = {
            'en': PromptTemplate(
                template="""You are a Formula 1 expert assistant. Provide SHORT, direct answers (2-3 sentences maximum).

    Context: {context}
    Question: {question}

    Instructions:
    - Give BRIEF, factual answers only
    - Use bullet points for multiple items
    - Start with the direct answer, then add 1-2 supporting details if needed
    - Keep responses under 100 words
    - Be precise and to the point

    Answer:""",
                input_variables=["context", "question"]
            ),

            'hi': PromptTemplate(
                template="""आप एक फॉर्मूला 1 विशेषज्ञ सहायक हैं। संक्षिप्त, सीधे उत्तर दें (अधिकतम 2-3 वाक्य)।

    संदर्भ: {context}
    प्रश्न: {question}

    निर्देश:
    - केवल संक्षिप्त, तथ्यपरक उत्तर दें
    - कई बिंदुओं के लिए बुलेट पॉइंट का उपयोग करें
    - पहले सीधा उत्तर दें, फिर 1-2 सहायक विवरण जोड़ें
    - उत्तर 100 शब्दों से कम रखें
    - सटीक और मुद्दे पर रहें

    उत्तर:""",
                input_variables=["context", "question"]
            )
        }

    def _post_process_response(self, response: str) -> str:
        """Make responses shorter and more concise"""
        # Split into sentences
        sentences = response.split('. ')

        # Keep only first 2-3 sentences for short answers
        if len(sentences) > 3:
            short_response = '. '.join(sentences[:3]) + '.'
        else:
            short_response = response

        # Remove excessive details
        keywords_to_trim = [
            "However, I can provide more",
            "Additionally,",
            "Furthermore,",
            "As per the provided context,",
            "Unfortunately, the context doesn't provide"
        ]

        for keyword in keywords_to_trim:
            if keyword in short_response:
                # Cut off at the keyword
                short_response = short_response.split(keyword)[0].strip()
                if not short_response.endswith('.'):
                    short_response += '.'

        return short_response
    def query(self, question: str) -> Dict:
        """Process multilingual query and return response"""
        try:
            # Detect language
            detected_language = self.language_handler.detect_language(question)
            print(f"🌍 Detected language: {detected_language}")

            # Translate to English for processing if needed
            english_question = self.language_handler.translate_to_english(
                question, detected_language
            )

            # Get appropriate prompt template
            prompt_template = self.prompt_templates.get(
                detected_language, self.prompt_templates['en']
            )

            # Create QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                chain_type_kwargs={
                    "prompt": prompt_template,
                    "verbose": True
                },
                return_source_documents=True
            )

            # Get response

            if detected_language == 'en':
                result = qa_chain({"query": question})
            else:
                # Process in English and translate back
                result = qa_chain({"query": english_question})
                result["result"] = self.language_handler.translate_response(
                    result["result"], detected_language
                )

            result["result"] = self._post_process_response(result["result"])
            # Process source documents
            source_docs = result.get("source_documents", [])
            sources = []

            for doc in source_docs[:5]:  # Limit to top 5 sources
                metadata = doc.metadata
                sources.append({
                    'title': metadata.get('title', 'Unknown'),
                    'source': metadata.get('source', 'Unknown'),
                    'url': metadata.get('url', ''),
                    'section': metadata.get('section', ''),
                    'type': metadata.get('type', 'text')
                })

            return {
                'answer': result["result"],
                'sources': sources,
                'language': detected_language,
                'original_question': question,
                'english_question': english_question,
                'retrieved_docs': len(source_docs)
            }

        except Exception as e:
            print(f"❌ Error in RAG chain: {e}")

            # Return error message in appropriate language
            error_messages = {
                'en': "I'm sorry, I encountered an error while processing your question. Please try again.",
                'hi': "क्षमा करें, आपके प्रश्न को संसाधित करते समय मुझे एक त्रुटि का सामना करना पड़ा। कृपया पुनः प्रयास करें।"
            }

            detected_language = self.language_handler.detect_language(question)
            error_message = error_messages.get(detected_language, error_messages['en'])

            return {
                'answer': error_message,
                'sources': [],
                'language': detected_language,
                'original_question': question,
                'english_question': question,
                'retrieved_docs': 0,
                'error': str(e)
            }
