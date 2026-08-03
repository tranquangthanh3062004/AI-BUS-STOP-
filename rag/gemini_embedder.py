import os
import google.generativeai as genai
from typing import List
from shared.config import settings
from shared.logger import logger

class GeminiEmbedder:
    def __init__(self):
        self.api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.enabled = False
        
        if self.api_key and settings.vector_rag_enabled:
            try:
                genai.configure(api_key=self.api_key)
                self.model = 'models/text-embedding-004'
                self.enabled = True
                logger.info("Gemini Embedder initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Embedder: {e}")
        else:
            logger.warning("Gemini API key not found or vector_rag_enabled is False. Embedding disabled.")

    def embed_query(self, text: str) -> List[float]:
        if not self.enabled:
            return []
            
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_query",
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.enabled or not texts:
            return []
            
        try:
            result = genai.embed_content(
                model=self.model,
                content=texts,
                task_type="retrieval_document",
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            return []
