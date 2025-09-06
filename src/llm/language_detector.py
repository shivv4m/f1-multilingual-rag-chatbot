from langdetect import detect
from googletrans import Translator
from typing import Dict, Tuple


class LanguageHandler:
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = ['en', 'hi']

    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            detected_lang = detect(text)

            # Map some common detections
            if detected_lang in ['hi', 'hindi']:
                return 'hi'
            elif detected_lang in ['en', 'english']:
                return 'en'
            else:
                # Default to English for unsupported languages
                return 'en'

        except Exception as e:
            print(f"❌ Language detection error: {e}")
            return 'en'  # Default to English

    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text to English for processing"""
        try:
            if source_lang == 'en':
                return text

            result = self.translator.translate(text, src=source_lang, dest='en')
            return result.text

        except Exception as e:
            print(f"❌ Translation error: {e}")
            return text

    def translate_response(self, text: str, target_lang: str) -> str:
        """Translate response to target language"""
        try:
            if target_lang == 'en':
                return text

            result = self.translator.translate(text, src='en', dest=target_lang)
            return result.text

        except Exception as e:
            print(f"❌ Response translation error: {e}")
            return text

    def get_language_specific_prompt(self, language: str) -> str:
        """Get language-specific system prompts"""
        prompts = {
            'en': """You are an expert Formula 1 assistant. Provide accurate, comprehensive answers about F1 using the given context. 
                     Be factual, cite specific information from the context, and maintain an enthusiastic but professional tone.""",

            'hi': """आप एक फॉर्मूला 1 विशेषज्ञ सहायक हैं। दिए गए संदर्भ का उपयोग करके F1 के बारे में सटीक, विस्तृत उत्तर प्रदान करें। 
                     तथ्यपरक रहें, संदर्भ से विशिष्ट जानकारी का हवाला दें, और उत्साही लेकिन पेशेवर टोन बनाए रखें।"""
        }

        return prompts.get(language, prompts['en'])
