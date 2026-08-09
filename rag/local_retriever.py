"""
rag/local_retriever.py
Hybrid Retriever combining Local Transit Graph (structured route recommendations)
and Local FAQ & GTCC Knowledge Store (unstructured rules/fares/VNeID).
"""

import os
import sqlite3
import unicodedata
import contextlib
from functools import lru_cache
from typing import List
from shared.schemas import IntentResult, RetrievedContext, RouteRecommendation
from edge_ai.transit_graph import LocalTransitGraph
from shared.config import settings
from shared.logger import logger
try:
    from rag.chroma_store import ChromaVectorStore
except ImportError:
    ChromaVectorStore = None

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "local_transit.db")

def norm_str(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text.lower().strip())

class LocalRetriever:
    def __init__(self, db_path: str = DB_PATH):
        self.transit_graph = LocalTransitGraph(db_path)
        self.db_path = db_path
        
        self.use_chroma = settings.vector_rag_enabled and ChromaVectorStore is not None
        if self.use_chroma:
            self.chroma_store = ChromaVectorStore()
            if not self.chroma_store.embedder.enabled:
                self.use_chroma = False
        else:
            self.chroma_store = None

    def _preferred_faq_categories(self, intent_label: str) -> List[str]:
        return {
            "FARE_QUERY": ["Fare"],
            "RULE_QUERY": ["Rules", "General Rules"],
            "APP_QUERY": ["App Guide"],
            "TOURIST_QUERY": ["Tourist"],
            "STATION_QUERY": ["Station"],
            "LOST_FOUND_QUERY": ["Q&A", "General Rules"],
            "SCHEDULE_QUERY": ["Schedule", "Q&A"],
        }.get(intent_label, [])

    @lru_cache(maxsize=128)
    def _fetch_faq_chunks_cached(self, intent_label: str, query_text: str) -> tuple:
        preferred_categories = self._preferred_faq_categories(intent_label)

        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            if preferred_categories:
                placeholders = ",".join("?" for _ in preferred_categories)
                cursor.execute(
                    f"""
                    SELECT content
                    FROM faqs
                    WHERE category IN ({placeholders})
                    ORDER BY LENGTH(content) DESC
                    LIMIT 3
                    """,
                    preferred_categories,
                )
                category_rows = [row[0] for row in cursor.fetchall()]
                if category_rows:
                    return tuple(category_rows)

            import re
            # Lọc bỏ tất cả ký tự đặc biệt để chống SQL Injection & Syntax Error trong FTS5
            safe_query = re.sub(r'[^\w\s]', '', query_text)
            fts_query = " OR ".join([f'"{q}"' for q in safe_query.split() if len(q) > 2])
            if not fts_query:
                fts_query = f'"{safe_query}"'


            cursor.execute(
                "SELECT category, content FROM faqs_fts WHERE faqs_fts MATCH ? LIMIT 20",
                (fts_query,),
            )
            rows = cursor.fetchall()

            if preferred_categories:
                preferred = [content for category, content in rows if category in preferred_categories]
                if preferred:
                    return tuple(preferred[:3])

            return tuple(content for _, content in rows[:3])

    def retrieve(self, intent_res: IntentResult, raw_query: str = "") -> RetrievedContext:
        intent_label = intent_res.intent_label
        entities = intent_res.entities
        
        structured_routes: List[RouteRecommendation] = []
        unstructured_chunks: List[str] = []
        valid_route_ids = []
        valid_stop_names = []

        # 1. Handle Route Query with Optimal Pathfinding Engine
        if intent_label == "ROUTE_QUERY":
            if entities.origin and entities.destination:
                structured_routes = self.transit_graph.find_optimal_route(entities.origin, entities.destination)
            elif entities.route_id:
                structured_routes = self.transit_graph.search_routes_by_keyword(entities.route_id)
            elif entities.location_keyword:
                structured_routes = self.transit_graph.search_routes_by_keyword(entities.location_keyword)

        for r in structured_routes:
            valid_route_ids.append(r.route_name)
            valid_stop_names.extend([r.board_stop, r.alight_stop])
            if r.transfer_stop:
                valid_stop_names.append(r.transfer_stop)

        # 2. Vector DB BM25 + Keyword Rule Hybrid Retrieval
        query_text = entities.location_keyword or entities.origin or entities.destination or entities.route_id
        if not query_text:
            query_text = raw_query if raw_query else intent_label
        if intent_label == "FARE_QUERY":
            query_text = "giá vé xe buýt vé tháng vé lượt bảng giá"
        elif intent_label == "RULE_QUERY":
            query_text = "quy định hành lý trẻ em người cao tuổi miễn phí vé pháp luật"
        elif intent_label == "APP_QUERY":
            query_text = "ứng dụng timbus thanh toán điện tử vneid thẻ ic mã qr nạp tiền"
        elif intent_label == "TOURIST_QUERY":
            query_text = "tourist guide tham quan du lịch danh lam thắng cảnh"
        elif intent_label == "STATION_QUERY":
            query_text = "bến xe điểm trung chuyển mỹ đình giáp bát yên nghĩa gia lâm"
        elif intent_label == "LOST_FOUND_QUERY":
            query_text = "mất đồ quên đồ thất lạc tổng đài hotline 1900"

        # Search FAQs via FTS5 or ChromaDB
        unstructured_chunks = []
        if self.use_chroma:
            try:
                results = self.chroma_store.search(query_text, top_k=3)
                unstructured_chunks = [res[1]["content"] for res in results]
                logger.info(f"Retrieved {len(unstructured_chunks)} chunks from ChromaDB")
            except Exception as e:
                logger.error(f"ChromaDB search failed: {e}")
                self.use_chroma = False  # Fallback to FTS5 next time

        if not unstructured_chunks:
            try:
                unstructured_chunks = list(self._fetch_faq_chunks_cached(intent_label, query_text))
                logger.info(f"Retrieved {len(unstructured_chunks)} chunks from SQLite FTS5 (cached)")
            except Exception as e:
                pass

        # Fallback for schedule if no chunks matched
        if intent_label == "SCHEDULE_QUERY" and not unstructured_chunks:
            if structured_routes:
                top_r = structured_routes[0]
                unstructured_chunks.append(f"{top_r.route_name} chạy trong khung giờ: {top_r.operating_hours}.")
            else:
                unstructured_chunks.append("Thời gian hoạt động chung của hệ thống xe buýt Việt Nam thường từ 05:00 - 21:00 (hoặc đến 22:30 đối với một số tuyến chính).")

        # Extract valid route IDs for validation
        for r in structured_routes:
            ids = r.route_id.replace("->", " ").replace("HCM_", "").split()
            valid_route_ids.extend([i.strip() for i in ids if i.strip()])

        return RetrievedContext(
            intent=intent_res,
            structured_routes=structured_routes,
            unstructured_chunks=unstructured_chunks[:3],
            valid_route_ids=list(set(valid_route_ids)),
            valid_stop_names=valid_stop_names
        )
