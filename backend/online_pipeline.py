"""
backend/online_pipeline.py
Online Cloud AI Assistant Pipeline Manager.
Priority order:
  1. Local Transit Graph (deterministic, always fast)
  2. Gemini Flash API (cloud LLM - main brain)
  3. Local Ollama (if available)
  4. Deterministic summarizer (final fallback)
"""

import time
import os
import urllib.request
import json
import re
from typing import Optional, List
from shared.config import settings
from shared.schemas import QueryRequest, OfflineResponse, RouteRecommendation
from shared.logger import logger
from edge_ai.intent_classifier import IntentClassifier
from edge_ai.offline_pipeline import OfflineAIAssistant
from edge_ai.validator import AnswerValidator
from local_llm.llm_engine import FALLBACK_MESSAGE
from backend.scraper_agent import GoogleMapsScraperAgent


SYSTEM_PROMPT_KIOSK = """Bạn là Kiosk thông tin xe buýt thông minh tại trạm xe buýt Hà Nội.
KHÔNG xưng là AI hay trợ lý ảo. Nhiệm vụ duy nhất của bạn là TRẢ LỜI ngắn gọn, chính xác bằng Tiếng Việt.

QUY TẮC BẮT BUỘC:
- CHỈ ƯU TIÊN SỬ DỤNG DỮ LIỆU ĐƯỢC CUNG CẤP DƯỚI ĐÂY (đặc biệt là đề xuất từ Google Maps). Không tự bịa thêm tuyến xe.
- Nếu có câu cảnh báo trong dữ liệu (vd: "Hệ thống AI có thể có sai sót..."), BẮT BUỘC phải đưa cảnh báo đó vào câu trả lời để nhắc nhở hành khách.
- Giọng văn: Thân thiện, súc tích, không dẫn nhập dài dòng. KHÔNG dùng emoji.

DỮ LIỆU ĐÃ TỔNG HỢP (Google Maps + Local DB):
{context}

CÂU HỎI HÀNH KHÁCH: {query}

TRẢ LỜI (Tiếng Việt, ngắn gọn):"""


class OnlineAIAssistant:
    def __init__(self, offline_assistant: Optional[OfflineAIAssistant] = None):
        self.intent_classifier = IntentClassifier()
        self.offline_assistant = offline_assistant or OfflineAIAssistant()
        self.validator = AnswerValidator()
        self.scraper = GoogleMapsScraperAgent()
        # Get Gemini API key from env
        self.gemini_api_key = (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("CLOUD_LLM_API_KEY")
            or settings.gemini_api_key
            or settings.cloud_llm_api_key
        )

    def process_query(self, request: QueryRequest) -> OfflineResponse:
        start_time = time.perf_counter()
        raw_text = request.raw_text

        # 1. Normalize query and classify intent
        norm_query, intent_res = self.intent_classifier.classify(raw_text)

        # 2. Session Management & Completeness Check
        session_id = request.session_id
        session_manager = self.offline_assistant.session_manager
        session_data = session_manager.get_session(session_id)

        if request.user_location and not intent_res.entities.origin:
            intent_res.entities.origin = request.user_location

        if session_data.get("intent") == "ROUTE_QUERY":
            if intent_res.intent_label in ("UNKNOWN", "ROUTE_QUERY") and not intent_res.entities.route_id:
                intent_res.intent_label = "ROUTE_QUERY"
                if not intent_res.entities.origin and session_data.get("origin"):
                    intent_res.entities.origin = session_data["origin"]
                if not intent_res.entities.destination and session_data.get("destination"):
                    intent_res.entities.destination = session_data["destination"]

                raw_clean = raw_text.strip()
                input_val = intent_res.entities.location_keyword or self.intent_classifier._clean_entity_text(raw_clean) or raw_clean
                if input_val and input_val.lower() not in ["xe buýt", "xe bus", "đi", "xe", "tuyến", "đến", "tôi muốn đi"]:
                    if intent_res.entities.origin and not intent_res.entities.destination:
                        intent_res.entities.destination = input_val
                    elif intent_res.entities.destination and not intent_res.entities.origin:
                        intent_res.entities.origin = input_val
                    elif not intent_res.entities.origin and not intent_res.entities.destination:
                        intent_res.entities.destination = input_val

        if intent_res.intent_label == "ROUTE_QUERY":
            if intent_res.entities.location_keyword and not intent_res.entities.destination:
                intent_res.entities.destination = intent_res.entities.location_keyword

            missing_origin = not intent_res.entities.origin and not intent_res.entities.route_id
            missing_dest = not intent_res.entities.destination and not intent_res.entities.route_id

            if missing_origin or missing_dest:
                session_manager.update_session(
                    session_id,
                    intent="ROUTE_QUERY",
                    origin=intent_res.entities.origin,
                    destination=intent_res.entities.destination
                )
                if missing_origin and missing_dest:
                    clarify_text = "Bạn muốn đi từ đâu đến đâu?"
                elif missing_origin:
                    clarify_text = f"Bạn muốn đi đến {intent_res.entities.destination}, vậy bạn xuất phát từ đâu?"
                else:
                    clarify_text = f"Bạn xuất phát từ {intent_res.entities.origin}, vậy bạn muốn đi đến đâu?"

                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return OfflineResponse(
                    status="CLARIFICATION",
                    raw_query=raw_text,
                    normalized_query=norm_query,
                    intent="ROUTE_QUERY",
                    answer_text=clarify_text,
                    recommendations=[],
                    execution_time_ms=elapsed_ms,
                    sources_used=["session_manager"],
                    is_offline_mode=False
                )
        else:
            session_manager.clear_session(session_id)

        # 3. Retrieve Context from Local RAG & Transit Graph
        context = self.offline_assistant.retriever.retrieve(intent_res, raw_text)
        sources = []

        recommendations = []
        if intent_res.intent_label == "ROUTE_QUERY" and intent_res.entities.origin and intent_res.entities.destination:
            scraped_routes = self.scraper.scrape_route(intent_res.entities.origin, intent_res.entities.destination)
            if scraped_routes:
                sources.append("google_maps_scraper")
                # Cross-check with Local SQLite DB
                verified_routes = []
                new_valid_ids = []
                from edge_ai.validator import normalize_route_id
                
                cache_keys = [normalize_route_id(k) for k in self.offline_assistant.retriever.transit_graph._routes_cache.keys()]
                
                for route in scraped_routes:
                    route_nums = route.route_id.split(" -> ")
                    db_exists = all(normalize_route_id(num) in cache_keys for num in route_nums)
                    
                    route_valid = db_exists and all(
                        self._deep_cross_check(normalize_route_id(num), intent_res.entities.origin, intent_res.entities.destination)
                        for num in route_nums
                    )
                            
                    if route_valid:
                        new_valid_ids.append(route.route_name)
                        ids = route.route_id.replace("->", " ").replace("HCM_", "").split()
                        new_valid_ids.extend([normalize_route_id(i) for i in ids if i.strip()])
                        route.description += " (Đã xác minh qua CSDL nội bộ)"
                    else:
                        route.description += " (Lưu ý: Hệ thống AI có thể có sai sót, bạn vui lòng xem lại qua Google Maps hoặc timbus.vn để có thông tin chính xác nhất)"
                    verified_routes.append(route)
                
                context.valid_route_ids = list(set(context.valid_route_ids + new_valid_ids))
                context.structured_routes = verified_routes
                recommendations = verified_routes
            else:
                # Fallback to local if scraper failed or found nothing
                recommendations = context.structured_routes
                if context.structured_routes:
                    sources.append("local_transit_db_sqlite")
        else:
            recommendations = context.structured_routes
            if context.structured_routes:
                sources.append("local_transit_db_sqlite")

        if context.unstructured_chunks:
            sources.append("local_faq_store_json")

        # 4. Build context string for LLM
        context_str = self._build_context_string(context)

        # 5. Hybrid approach: Use Gemini -> Ollama -> Deterministic Summarizer
        logger.info("Using Gemini/Ollama with Google Maps + SQLite Hybrid context...")
        answer_text = None
        status = "FALLBACK"
        
        gemini_answer = self._call_gemini_api(norm_query, context_str)
        if gemini_answer:
            is_valid, validated_gemini = self.validator.validate(gemini_answer, context)
            if is_valid:
                answer_text = validated_gemini
                sources.append("gemini_flash_api")
                status = "SUCCESS"
            else:
                logger.warning("Gemini answer failed validation. Falling back to Ollama.")

        if not answer_text:
            ollama_answer = self._call_ollama_agent_api(norm_query, context_str)
            if ollama_answer:
                is_valid, validated_ollama = self.validator.validate(ollama_answer, context)
                if is_valid:
                    answer_text = validated_ollama
                    sources.append("local_ollama_agent_api")
                    status = "SUCCESS"
                else:
                    logger.warning("Ollama answer failed validation (Hallucination detected).")

        if not answer_text:
            # 6. Final fallback: deterministic summarizer (always works)
            logger.warning("All LLMs unavailable or failed validation. Using deterministic summarizer.")
            local_answer = self.offline_assistant.llm_engine.generate_answer(norm_query, context)
            _, answer_text = self.validator.validate(local_answer, context)
            sources.append("local_deterministic_summarizer")
            status = "SUCCESS" if answer_text != FALLBACK_MESSAGE else "FALLBACK"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"Online pipeline finished in {elapsed_ms}ms | sources: {sources}")

        return OfflineResponse(
            status=status,
            raw_query=raw_text,
            normalized_query=norm_query,
            intent=intent_res.intent_label,
            answer_text=answer_text,
            recommendations=recommendations,
            execution_time_ms=elapsed_ms,
            sources_used=sources,
            is_offline_mode=False
        )

    def _deep_cross_check(self, route_id: str, origin: str, destination: str) -> bool:
        """Kiểm tra tuyến có thực sự đi qua cả origin và destination không."""
        from edge_ai.transit_graph import norm_str
        
        route_info = self.offline_assistant.retriever.transit_graph._routes_cache.get(route_id)
        if not route_info:
            return False
        
        # Lấy toàn bộ lộ trình chiều đi + chiều về
        all_text = norm_str(
            f"{route_info.get('outbound_itinerary', '')} "
            f"{route_info.get('inbound_itinerary', '')} "
            f"{route_info.get('start_stop', '')} "
            f"{route_info.get('end_stop', '')}"
        )
        
        origin_aliases = self.offline_assistant.retriever.transit_graph._normalize_location(origin)
        dest_aliases = self.offline_assistant.retriever.transit_graph._normalize_location(destination)
        
        origin_match = any(alias in all_text for alias in origin_aliases)
        dest_match = any(alias in all_text for alias in dest_aliases)
        
        return origin_match and dest_match

    def _build_context_string(self, context) -> str:
        """Build a clean context string for LLM consumption."""
        parts = []
        if context.structured_routes:
            parts.append("CÁC TUYẾN XE BUÝT PHÙ HỢP (Ưu tiên phương án đầu tiên):")
            for i, r in enumerate(context.structured_routes[:3]):
                verified = "(✓ Đã xác minh)" if "Đã xác minh" in r.description else "(⚠ Chưa xác minh)"
                parts.append(f"Phương án {i+1} {verified}: {r.route_name} - {r.description}")
        if context.unstructured_chunks:
            parts.append("\nTHÔNG TIN THÊM:")
            for chunk in context.unstructured_chunks[:2]:
                parts.append(f"  {chunk[:300]}")
        return "\n".join(parts) if parts else "Không có dữ liệu tuyến xe phù hợp trong cơ sở dữ liệu cục bộ."

    def _call_gemini_api(self, query: str, context_str: str) -> Optional[str]:
        """Call Gemini Flash 2.0 API using REST (no SDK needed)."""
        if not self.gemini_api_key:
            return None

        prompt = SYSTEM_PROMPT_KIOSK.format(context=context_str, query=query)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.15,
                "maxOutputTokens": 512,
                "candidateCount": 1
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        if text:
                            logger.info(f"Gemini Flash responded successfully ({len(text)} chars)")
                            return text
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"Gemini API HTTPError {e.code}: {body[:200]}")
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
        return None

    def _call_ollama_agent_api(self, query: str, context_str: str) -> Optional[str]:
        """Call local Ollama as fallback LLM."""
        ollama_url = "http://localhost:11434"
        active_model = None
        if self.offline_assistant and self.offline_assistant.llm_engine:
            active_model = self.offline_assistant.llm_engine.active_ollama_model
        if not active_model:
            active_model = "qwen2.5:3b"

        prompt = SYSTEM_PROMPT_KIOSK.format(context=context_str, query=query)
        url = f"{ollama_url}/api/chat"
        messages = [{"role": "user", "content": prompt}]
        data = {
            "model": active_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1}
        }

        try:
            req_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as res:
                if res.status == 200:
                    resp = json.loads(res.read().decode("utf-8"))
                    if "message" in resp:
                        return resp["message"].get("content", "").strip()
        except Exception as e:
            logger.info(f"Ollama not available: {e}")
        return None

    def _http_request_with_retry(self, req: urllib.request.Request, retries: int = 3, backoff_factor: float = 1.5, timeout: int = 10) -> Optional[dict]:
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as res:
                    if res.status == 200:
                        return json.loads(res.read().decode('utf-8'))
            except Exception as e:
                logger.warning(f"Request attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(backoff_factor ** attempt)
        return None
