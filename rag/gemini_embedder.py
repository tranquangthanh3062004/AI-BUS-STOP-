import os
from typing import List
from shared.config import settings
from shared.logger import logger

class GeminiEmbedder:
    def __init__(self):
        self.api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.enabled = False
        
        # Disabled Gemini Embedder due to 100% local requirement
        logger.warning("Gemini Embedder is permanently disabled (running in  Local AI mode).")

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
