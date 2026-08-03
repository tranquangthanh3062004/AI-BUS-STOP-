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
from local_llm.llm_engine import LocalLLMEngine, FALLBACK_MESSAGE
from edge_ai.validator import AnswerValidator
from edge_ai.session_manager import SessionManager
from edge_ai.session_resolver import resolve_entities_from_session


class OfflineAIAssistant:
    def __init__(self, model_path: Optional[str] = None):
        self.intent_classifier = IntentClassifier()
        self.retriever = LocalRetriever()
        self.llm_engine = LocalLLMEngine(model_path=model_path)
        from edge_ai.validator import AnswerValidator
        from edge_ai.session_manager import SessionManager
        from backend.scraper_agent import GoogleMapsScraperAgent

        self.validator = AnswerValidator()
        self.session_manager = SessionManager()
        self.scraper = GoogleMapsScraperAgent()

    def process_query(self, request: QueryRequest) -> OfflineResponse:
        start_time = time.perf_counter()

        raw_text = request.raw_text
        if not raw_text or not raw_text.strip():
            return OfflineResponse(
                status="NO_DATA",
                raw_query="",
                normalized_query="",
                intent="UNKNOWN",
                answer_text=FALLBACK_MESSAGE,
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
        
        # 2.5. Hybrid Scraping for ROUTE_QUERY
        scraped_routes = []
        if intent_res.intent_label == "ROUTE_QUERY" and intent_res.entities.origin and intent_res.entities.destination:
            scraped_routes = self.scraper.scrape_route(intent_res.entities.origin, intent_res.entities.destination)
            if scraped_routes:
                sources.append("google_maps_scraper")
                verified_routes = []
                new_valid_ids = []
                from edge_ai.validator import normalize_route_id
                
                cache_keys = [normalize_route_id(k) for k in self.retriever.transit_graph._routes_cache.keys()]
                
                for route in scraped_routes:
                    route_nums = route.route_id.split(" -> ")
                    db_exists = True
                    for num in route_nums:
                        num = normalize_route_id(num)
                        if num not in cache_keys:
                            db_exists = False
                            break
                            
                    if db_exists:
                        new_valid_ids.append(route.route_name)
                        ids = route.route_id.replace("->", " ").replace("HCM_", "").split()
                        new_valid_ids.extend([normalize_route_id(i) for i in ids if i.strip()])
                    else:
                        route.description += " (Lưu ý hệ thống: Tuyến xe này có thể đã thay đổi lộ trình hoặc tạm ngừng)"
                    verified_routes.append(route)
                
                context.valid_route_ids = list(set(context.valid_route_ids + new_valid_ids))
                context.structured_routes = verified_routes

        # 3. Generate answer using Local LLM / Summarizer
        if scraped_routes:
            context_str = self._build_context_string(context)
            raw_answer = self._call_ollama_directly(norm_query, context_str)
            if not raw_answer:
                raw_answer = self.llm_engine.generate_answer(norm_query, context)
                sources.append("local_deterministic_summarizer")
            else:
                sources.append("local_ollama_agent_api")
        else:
            raw_answer = self.llm_engine.generate_answer(norm_query, context)
            if context.structured_routes:
                sources.append("local_transit_db_sqlite")

        # 4. Validate answer against Anti-Hallucination rules
        is_valid, final_answer = self.validator.validate(raw_answer, context)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "SUCCESS" if (is_valid and final_answer != FALLBACK_MESSAGE) else "FALLBACK"

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
