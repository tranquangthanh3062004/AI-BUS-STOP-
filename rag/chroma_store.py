import os
import chromadb
from typing import List, Dict, Any, Tuple
from shared.config import settings
from shared.logger import logger
from rag.gemini_embedder import GeminiEmbedder

class ChromaVectorStore:
    def __init__(self, collection_name: str = "transit_faqs"):
        self.db_path = settings.chroma_db_path
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection_name = collection_name
        self.embedder = GeminiEmbedder()
        
        try:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            logger.error(f"Failed to init ChromaDB collection: {e}")
            self.collection = None

    def build_index(self, documents: List[Dict[str, str]]):
        """Build vector index from list of docs (with id, content, metadata)"""
        if not self.collection or not self.embedder.enabled:
            logger.warning("Cannot build index: ChromaDB or Embedder not ready.")
            return

        texts = [doc["content"] for doc in documents]
        ids = [doc.get("id", str(i)) for i, doc in enumerate(documents)]
        metadatas = [{"title": doc.get("title", ""), "category": doc.get("category", "")} for doc in documents]

        logger.info(f"Embedding {len(texts)} documents using Gemini...")
        embeddings = self.embedder.embed_documents(texts)
        
        if not embeddings:
            logger.error("Failed to generate embeddings. Index build aborted.")
            return

        logger.info("Upserting documents to ChromaDB...")
        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Vector index build complete.")

    def search(self, query: str, top_k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
        if not self.collection or not self.embedder.enabled:
            return []

        query_embedding = self.embedder.embed_query(query)
        if not query_embedding:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metadatas, distances):
                formatted_results.append((
                    1.0 / (1.0 + dist),  # Convert distance to similarity score
                    {"content": doc, "title": meta.get("title", ""), "category": meta.get("category", "")}
                ))
        return formatted_results
