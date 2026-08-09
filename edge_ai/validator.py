"""
edge_ai/validator.py
Anti-Hallucination Answer Validator for Offline AI Assistant.
Verifies that generated LLM responses do NOT contain fake route numbers or non-existent stops.
Normalizes spaces and route symbols (e.g. 'BRT 01' matches 'BRT01').
"""

import re
import unicodedata
from typing import List, Tuple
from shared.schemas import RetrievedContext
from shared.logger import logger
from local_llm.llm_engine import FALLBACK_MESSAGES

HARD_FAIL_MSG = "Hệ thống bị trục trặc bạn có thể tra cứu thông tin trên google map hoặc timbus.vn"

def norm_str(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text.lower().strip())


def normalize_route_id(r_id: str) -> str:
    """Normalize bus route IDs (e.g. '01' -> '1', 'BRT 01' -> 'BRT01', 'E03' -> 'E03')"""
    if not r_id: return ""
    r_id = str(r_id).upper().replace(" ", "")
    if r_id.isdigit():
        return str(int(r_id))
    if r_id.startswith("BRT") and r_id[-1].isdigit():
        num = int(re.search(r'\d+', r_id).group())
        return f"BRT{num:02d}"
    return r_id


class AnswerValidator:
    def validate(self, answer_text: str, context: RetrievedContext) -> Tuple[bool, str]:
        intent_label = context.intent.intent_label
        valid_route_ids = context.valid_route_ids

        if not answer_text or answer_text.strip() in FALLBACK_MESSAGES:
            return True, answer_text.strip() if answer_text else FALLBACK_MESSAGES[1]
            
        # Kiểm tra ký tự Tiếng Trung / Ký tự lạ
        if re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u30ff\u31f0-\u31ff]', answer_text):
            logger.warning("Anti-Hallucination Triggered! LLM generated Chinese/Japanese/Korean characters.")
            return False, HARD_FAIL_MSG

        if len(answer_text) > 500:
            logger.warning(f"Anti-Hallucination Triggered! Output too long ({len(answer_text)} chars). Falling back to avoid runaway generation.")
            return False, HARD_FAIL_MSG

        ans_compact = answer_text.replace(" ", "").upper()

        if intent_label == "ROUTE_QUERY":
            # 1. Clean out time, distance, and money contexts to avoid false positives on numbers
            # Clean ranges like 10-15 phút or formatted numbers like 10.000 đ
            clean_text = re.sub(r'\b\d+(?:[.,]\d+)*\s*-\s*\d+(?:[.,]\d+)*\s*(?:phút|p|giờ|h|tiếng|km|m|mét|đ|vnd|đồng|k|nghìn|ngàn)\b', '', answer_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\b\d+(?:[.,]\d+)*\s*(?:phút|p|giờ|h|tiếng|km|m|mét|đ|vnd|đồng|k|nghìn|ngàn)\b', '', clean_text, flags=re.IGNORECASE)
            # Remove typical counting words
            clean_text = re.sub(r'\b(?:cách|bước|phương án|tuyến đường thứ)\s*\d+\b', '', clean_text, flags=re.IGNORECASE)

            # 2. Extract potential bus IDs: matches E01, BRT01, 14CT, or standalone 1-3 digits
            potential_routes = re.findall(r"\b(BRT\s*0?1|E0[1-9]|E10|[0-9]{1,3}[A-Z]{1,2}|[0-9]{1,3})\b", clean_text, flags=re.IGNORECASE)
            
            # 3. Explicit prefix check
            explicit_routes = re.findall(r"(?:Tuyến|Xe|Bus|Số)\s*([0-9]{1,3}[A-Za-z]{0,3})", answer_text, flags=re.IGNORECASE)
            
            mentioned_routes = list(set([normalize_route_id(r) for r in potential_routes + explicit_routes]))
            explicit_norm = [normalize_route_id(r) for r in explicit_routes]
            
            final_mentioned_routes = []
            for r in mentioned_routes:
                # Filter out single digits 1-9 if they were not explicitly prefixed, to avoid blocking normal language (like "1 trạm")
                if r.isdigit() and int(r) < 10 and r not in explicit_norm:
                    if re.search(r'\b' + r + r'\s+(?:trạm|chuyến|lần|điểm)\b', answer_text, re.IGNORECASE):
                        continue
                final_mentioned_routes.append(r)

            if not valid_route_ids:
                if explicit_routes: # Only trigger on explicit if no valid routes
                    logger.warning(f"Anti-Hallucination Triggered! LLM generated routes {explicit_routes} but NO valid routes in context. Output: {answer_text[:100]}")
                    return False, HARD_FAIL_MSG
                return True, answer_text

            valid_clean_ids = [normalize_route_id(v) for v in valid_route_ids]

            for m_clean in final_mentioned_routes:
                if m_clean not in valid_clean_ids:
                    if m_clean.isdigit() and int(m_clean) < 10 and m_clean not in explicit_norm:
                        continue # Allow 1-9 to pass if they aren't explicitly prefixed
                    logger.warning(f"Anti-Hallucination Triggered! LLM generated fake route '{m_clean}' not in context ({valid_clean_ids}). Output: {answer_text[:100]}")
                    return False, HARD_FAIL_MSG

            is_valid = False
            for v_id in valid_clean_ids:
                if v_id in ans_compact:
                    is_valid = True
                    break

            if not is_valid:
                logger.warning(f"Anti-Hallucination Triggered! LLM output missing required valid route ({valid_clean_ids}). Output: {answer_text[:100]}")
                return False, HARD_FAIL_MSG
                
        elif intent_label == "FARE_QUERY":
            # Validate generated prices against standard Hanoi bus fares
            valid_prices = ["3000", "7000", "8000", "9000", "10000", "15000", "20000", "45000", "50000", "55000", "70000", "100000", "140000", "200000"]
            
            # Find all prices in text like: 12.000, 12000, 12k
            mentioned_prices = re.findall(r"([0-9]{1,3}(?:[\.,][0-9]{3})*|[0-9]{4,6})(?:\s*(?:VNĐ|đồng|đ|k))", answer_text, flags=re.IGNORECASE)
            
            for p in mentioned_prices:
                p_clean = p.replace(".", "").replace(",", "")
                if p_clean.isdigit() and int(p_clean) > 2000 and p_clean not in valid_prices:
                    logger.warning(f"Anti-Hallucination Triggered! LLM generated invalid fare price: {p}. Output: {answer_text[:100]}")
                    return False, FALLBACK_MESSAGES[1]
                    
        return True, answer_text

