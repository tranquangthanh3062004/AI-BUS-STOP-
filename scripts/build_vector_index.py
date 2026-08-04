import os
import sys
import json
import sqlite3
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
        
    db_path = settings.db_path
    if not os.path.exists(db_path):
        logger.error(f"SQLite DB not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, category, title, content FROM faqs")
        rows = cursor.fetchall()
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.close()
        return
    conn.close()
        
    documents = []
    for row in rows:
        faq_id, category, title, content = row
        doc = {
            "id": f"faq_{faq_id}",
            "title": title or "",
            "content": f"Q: {title}\nA: {content}",
            "category": category or "General"
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
