"""
local_llm/llm_engine.py
Local LLM Handler & Optimal Route Context Summarizer Engine.
Connects directly to local Ollama API (qwen2.5:3b / llama3:latest), llama.cpp GGUF,
and local deterministic summarization fallback.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from shared.schemas import RetrievedContext
from shared.logger import logger
from shared.config import settings

FALLBACK_MESSAGE = "Tôi không tìm thấy thông tin này trong cơ sở dữ liệu cục bộ hiện có."


class LocalLLMEngine:
    def __init__(self, model_path: Optional[str] = None, ollama_url: str = "http://localhost:11434"):
        self.model_path = model_path
        self.ollama_url = ollama_url
        self.llama = None
        self.ollama_active = False
        self.active_ollama_model = None

        # 1. Test local Ollama service connection
        self._check_ollama_connection()

        # 2. Test llama.cpp local file if provided
        if not self.ollama_active and model_path and os.path.exists(model_path):
            try:
                from llama_cpp import Llama
                logger.info(f"Loading GGUF model from {model_path}...")
                self.llama = Llama(model_path=model_path, n_ctx=2048, verbose=False)
            except Exception as e:
                logger.warning(f"Could not load llama.cpp GGUF model ({e}). Using Local Summarizer.")

    def _check_ollama_connection(self):
        """Kiểm tra kết nối tới dịch vụ Ollama cục bộ (http://localhost:11434)."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode('utf-8'))
                    models = [m.get('name') for m in data.get('models', [])]
                    logger.info(f"Connected to Local Ollama Service! Installed models: {models}")
                    
                    priority_list = ["qwen2.5:3b", "qwen2.5", "qwen:latest", "llama3:latest", "phi3:mini"]
                    for m_name in priority_list:
                        for model_item in models:
                            if m_name in model_item:
                                self.active_ollama_model = model_item
                                self.ollama_active = True
                                break
                        if self.ollama_active:
                            break

                    if not self.active_ollama_model and models:
                        self.active_ollama_model = models[0]
                        self.ollama_active = True

                    logger.info(f"Selected Active Local Ollama Model: '{self.active_ollama_model}'")
        except Exception as e:
            logger.info(f"Local Ollama service on {self.ollama_url} not active ({e}). Falling back to Local Summarizer.")

    def generate_answer(self, raw_query: str, context: RetrievedContext) -> str:
        intent_label = context.intent.intent_label

        # Route answers must be deterministic: the route IDs, transfers and fares
        # come from SQLite, not from a generative model.
        if intent_label == "ROUTE_QUERY":
            if not context.structured_routes:
                return FALLBACK_MESSAGE
            return self._format_with_local_summarizer(raw_query, context)

        # FAQ intents with clear templates -> no LLM needed
        structured_intents = {"FARE_QUERY", "SCHEDULE_QUERY", "METRO_QUERY", "RULE_QUERY"}
        if intent_label in structured_intents and context.unstructured_chunks:
            template_answer = self._format_with_local_summarizer(raw_query, context)
            if template_answer and template_answer != FALLBACK_MESSAGE:
                return template_answer

        # 1. Primary: Run inference via Local Ollama API (Qwen2.5:3B)
        if self.ollama_active and self.active_ollama_model:
            ollama_ans = self._generate_with_ollama(raw_query, context)
            if ollama_ans and ollama_ans != FALLBACK_MESSAGE:
                return ollama_ans

        # 2. Secondary: Run inference via llama.cpp GGUF binding
        if self.llama:
            return self._generate_with_llama(raw_query, context)

        # 3. Fallback: Fast Local Deterministic Summarizer
        return self._format_with_local_summarizer(raw_query, context)

    def _get_prompt_template(self) -> str:
        prompt_file = os.path.join(settings.prompts_dir, "system_prompt_kiosk.txt")
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return (
            "[SYSTEM] Bạn là máy đọc văn bản thông minh của Trạm xe buýt.\n"
            "NHIỆM VỤ DUY NHẤT: Tóm tắt thông tin bên dưới thành 2-3 câu tiếng Việt ngắn gọn.\n"
            "TUYỆT ĐỐI không đưa ra thông tin ngoài dữ liệu bên dưới.\n"
            "Nếu không có thông tin: trả lời '{FALLBACK_MESSAGE}'\n\n"
            "DỮ LIỆU:\n{context}\n\n"
            "CÂU HỎI: {query}\n\n"
            "TRẢ LỜI (ngắn gọn, tiếng Việt):"
        )

    def _generate_with_ollama(self, raw_query: str, context: RetrievedContext) -> str:
        """Gửi prompt tới mô hình LLM cục bộ chạy qua Ollama (Qwen2.5:3B)."""
        formatted_context = ""
        for idx, r in enumerate(context.structured_routes, 1):
            formatted_context += f"Phương án {idx} ({'TỐI ƯU NHẤT - Đi thẳng' if r.transfers_count == 0 else 'Chuyển tuyến'}): {r.description}\n"
        for c in context.unstructured_chunks:
            formatted_context += f"- {c[:350]}\n"

        template = self._get_prompt_template()
        system_prompt = template.format(context=formatted_context, query=raw_query)

        payload = {
            "model": self.active_ollama_model,
            "prompt": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 250
            }
        }

        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status == 200:
                    ans_data = json.loads(res.read().decode('utf-8'))
                    response_text = ans_data.get("response", "").strip()
                    logger.info(f"Successfully generated answer with Ollama model '{self.active_ollama_model}'")
                    return response_text
        except Exception as e:
            logger.warning(f"Ollama API call error: {e}. Falling back to local summarizer.")

        return self._format_with_local_summarizer(raw_query, context)

    def _generate_with_llama(self, raw_query: str, context: RetrievedContext) -> str:
        formatted_context = ""
        for r in context.structured_routes:
            formatted_context += f"- {r.description}\n"
        for c in context.unstructured_chunks:
            formatted_context += f"- {c[:300]}\n"

        system_prompt = (
            "[SYSTEM] Bạn là máy đọc văn bản thông minh của Trạm xe buýt.\n"
            "NHIỆM VỤ DUY NHẤT: Tóm tắt thông tin bên dưới thành 2-3 câu tiếng Việt ngắn gọn.\n"
            "TUYỆT ĐỐI không đưa ra thông tin ngoài dữ liệu bên dưới.\n"
            "Nếu không có thông tin: trả lời '{FALLBACK_MESSAGE}'\n\n"
            f"DỮ LIỆU:\n{formatted_context}\n\n"
            f"CÂU HỎI: {raw_query}\n\n"
            "TRẢ LỜI (ngắn gọn, tiếng Việt):"
        )

        output = self.llama(system_prompt, max_tokens=256, temperature=0.1, stop=["\n\n", "CÂU HỎI:"])
        return output["choices"][0]["text"].strip()

    def _format_with_local_summarizer(self, raw_query: str, context: RetrievedContext) -> str:
        intent_label = context.intent.intent_label
        routes = context.structured_routes
        chunks = context.unstructured_chunks

        if intent_label == "ROUTE_QUERY" and routes:
            top_route = routes[0]
            lines = [f"Để đi từ {top_route.board_stop} đến {top_route.alight_stop}, tuyến xe buýt phù hợp nhất là **{top_route.route_name}**."]
            lines.append(f"Chuyến xe hoạt động trong khung giờ {top_route.operating_hours}, với giá vé là {top_route.fare_vnd:,} VNĐ.")
            
            if top_route.transfers_count == 0:
                lines.append("Bạn có thể đi thẳng mà không cần chuyển tuyến.")
            else:
                lines.append(f"Lưu ý: Bạn sẽ cần đổi xe tại trạm **{top_route.transfer_stop}**.")

            other_routes = routes[1:]
            if other_routes:
                lines.append(f"Ngoài ra, bạn cũng có thể chọn {other_routes[0].route_name} làm phương án dự phòng.")

            return " ".join(lines)

        elif intent_label == "METRO_QUERY" and chunks:
            return "Thông tin Tuyến Metro:\n" + chunks[0][:450]

        elif intent_label in ["FARE_QUERY", "RULE_QUERY"] and chunks:
            return "Thông tin Vé và Quy định xe buýt:\n" + chunks[0][:400] + "..."

        elif intent_label == "SCHEDULE_QUERY":
            if routes:
                r = routes[0]
                return f"{r.route_name} hoạt động trong khung giờ: {r.operating_hours}. Tần suất khoảng 10 - 15 phút/chuyến."
            elif chunks:
                return chunks[0][:400]

        return FALLBACK_MESSAGE
