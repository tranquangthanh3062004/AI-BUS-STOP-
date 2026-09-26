"""
edge_ai/offline_pipeline.py
End-to-End Offline AI Assistant Pipeline Manager.
Coordinates Query Normalizer -> Intent Classifier -> Local Retriever -> Local LLM Engine -> Answer Validator.
Operates 100% offline without Cloud APIs, Google Maps, or external LLMs.
"""

import time
from typing import Optional
from shared.schemas import QueryRequest, OfflineResponse
from edge_ai.intent_classifier import IntentClassifier
from rag.local_retriever import LocalRetriever
from local_llm.llm_engine import LocalLLMEngine, FALLBACK_MESSAGES
from edge_ai.validator import AnswerValidator
from edge_ai.session_manager import SessionManager
from edge_ai.session_resolver import resolve_entities_from_session


class _DummyScraper:
    """Fallback khi Playwright không khả dụng — trả về list rỗng."""
    def scrape_route(self, origin: str, destination: str):
        return []


class OfflineAIAssistant:
    def __init__(self, model_path: Optional[str] = None):
        self.intent_classifier = IntentClassifier()
        self.retriever = LocalRetriever()
        self.llm_engine = LocalLLMEngine(model_path=model_path)
        self.validator = AnswerValidator()
        self.session_manager = SessionManager()
        self._scraper = None  # Lazy-loaded: chỉ khởi tạo khi cần

    @property
    def scraper(self):
        """Lazy-load GoogleMapsScraperAgent để tránh crash nếu Playwright chưa cài."""
        if self._scraper is None:
            try:
                from backend.scraper_agent import GoogleMapsScraperAgent
                self._scraper = GoogleMapsScraperAgent()
            except Exception:
                self._scraper = _DummyScraper()
        return self._scraper

    def process_query(self, request: QueryRequest) -> OfflineResponse:
        start_time = time.perf_counter()

        raw_text = request.raw_text
        if not raw_text or not raw_text.strip():
            return OfflineResponse(
                status="NO_DATA",
                raw_query="",
                normalized_query="",
                intent="UNKNOWN",
                answer_text=FALLBACK_MESSAGES[1],
                recommendations=[],
                execution_time_ms=0.0,
                sources_used=["offline_fallback"]
            )

        # 1. Normalize query and classify intent
        norm_query, intent_res = self.intent_classifier.classify(raw_text)

        # If user location provided, inject as entity origin if not present
        if request.user_location and not intent_res.entities.origin:
            intent_res.entities.origin = request.user_location

        # --- MULTI-TURN DIALOGUE CHECKPOINT ---
        session_id = request.session_id or "default_session"
        intent_res, clarification = resolve_entities_from_session(
            session_id, raw_text, intent_res, self.session_manager, self.intent_classifier
        )
        if clarification:
            return OfflineResponse(
                status="CLARIFICATION",
                raw_query=raw_text,
                normalized_query=norm_query,
                intent=intent_res.intent_label,
                answer_text=clarification,
                recommendations=[],
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
                sources_used=["session_manager"],
                is_offline_mode=True
            )
        # --- END CHECKPOINT ---

        # 2. Retrieve local context (Transit Graph + FAQ Store)
        context = self.retriever.retrieve(intent_res, raw_text)
        sources = []

        if context.structured_routes:
            sources.append("local_transit_db_sqlite")

        # 3. Generate answer using Local LLM / Deterministic Summarizer
        raw_answer = self.llm_engine.generate_answer(norm_query, context)
        if self.llm_engine.ollama_active and raw_answer not in FALLBACK_MESSAGES:
            sources.append("local_ollama_agent_api")
        else:
            sources.append("local_deterministic_summarizer")

        # 4. Validate answer against Anti-Hallucination rules
        is_valid, final_answer = self.validator.validate(raw_answer, context)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "SUCCESS" if (is_valid and final_answer not in FALLBACK_MESSAGES) else "FALLBACK"

        if context.unstructured_chunks:
            sources.append("local_faq_store_json")

        return OfflineResponse(
            status=status,
            raw_query=raw_text,
            normalized_query=norm_query,
            intent=intent_res.intent_label,
            answer_text=final_answer,
            recommendations=context.structured_routes,
            execution_time_ms=elapsed_ms,
            sources_used=sources or ["offline_validator"],
            is_offline_mode=True
        )

    def _build_context_string(self, context) -> str:
        parts = []
        if context.structured_routes:
            parts.append("CÁC TUYẾN XE BUÝT PHÙ HỢP:")
            for r in context.structured_routes[:3]:
                parts.append(f"- {r.route_name}: {r.description}")
        if context.unstructured_chunks:
            parts.append("\nTHÔNG TIN THÊM:")
            for chunk in context.unstructured_chunks[:2]:
                parts.append(f"  {chunk[:300]}")
        return "\n".join(parts) if parts else "Không có dữ liệu tuyến xe phù hợp trong cơ sở dữ liệu cục bộ."

    def _call_ollama_directly(self, query: str, context_str: str) -> str:
        import urllib.request
        import json
        from shared.logger import logger

        prompt = f"""Bạn là Kiosk thông tin xe buýt thông minh tại trạm xe buýt Hà Nội.
KHÔNG xưng là AI hay trợ lý ảo. Nhiệm vụ duy nhất của bạn là TRẢ LỜI ngắn gọn, chính xác bằng Tiếng Việt.

QUY TẮC BẮT BUỘC:
- Chỉ dùng DỮ LIỆU BÊN DƯỚI để trả lời. Không bịa thêm thông tin.
- Nếu hỏi lộ trình và có tuyến trong dữ liệu: Trả lời TÊN TUYẾN, LỘ TRÌNH, GIÁ VÉ.
- Nếu hỏi thông tin chung (giá vé, quy định): Trả lời thẳng vào vấn đề.
- Nếu khách chào hỏi: Hỏi họ muốn đi đâu.
- Giọng văn: Thân thiện, súc tích. KHÔNG dùng emoji.

DỮ LIỆU CỤC BỘ:
{context_str}

CÂU HỎI HÀNH KHÁCH: {query}

TRẢ LỜI (Tiếng Việt, ngắn gọn, không dẫn nhập dài dòng):"""

        url = "http://localhost:11434/api/chat"
        active_model = self.llm_engine.active_ollama_model if hasattr(self.llm_engine, 'active_ollama_model') else "qwen2.5:3b"
        data = {
            "model": active_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1}
        }
        try:
            req_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as res:
                if res.status == 200:
                    resp = json.loads(res.read().decode("utf-8"))
                    if "message" in resp:
                        return resp["message"].get("content", "").strip()
        except Exception as e:
            logger.info(f"Ollama direct call failed: {e}")
        return ""
