import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from shared.config import settings
from rag.chroma_store import ChromaVectorStore
from shared.logger import logger

def build_vector_index():
    logger.info("Starting Vector Index Build with Gemini Embedding API...")
    
    if not settings.vector_rag_enabled or not settings.gemini_api_key:
        logger.error("Vector RAG is disabled or GEMINI_API_KEY is not set.")
        return
        
    faq_path = settings.faq_path
    if not os.path.exists(faq_path):
        logger.error(f"FAQ file not found: {faq_path}")
        return
        
    with open(faq_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)
        
    documents = []
    for i, faq in enumerate(faqs):
        doc = {
            "id": f"faq_{i}",
            "title": faq.get("question", ""),
            "content": f"Q: {faq.get('question', '')}\nA: {faq.get('answer', '')}",
            "category": faq.get("category", "General")
        }
        documents.append(doc)
        
    logger.info(f"Loaded {len(documents)} FAQs. Initializing ChromaStore...")
    
    store = ChromaVectorStore()
    if store.embedder.enabled:
        store.build_index(documents)
    else:
        logger.error("Gemini Embedder is not enabled.")

if __name__ == "__main__":
    build_vector_index()
