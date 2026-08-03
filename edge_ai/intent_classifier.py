"""
edge_ai/intent_classifier.py
Query Normalizer and Flexible Rule-based Fast Intent & Entity Classifier for Offline AI Assistant.
Parses conversational Vietnamese queries ("tôi muốn đi từ X đến Y", "BRT 01", "từ X về Y đi xe nào", etc.)
"""

import re
import unicodedata
from typing import Tuple
from shared.schemas import IntentResult, EntityExtract


def norm_str(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text.lower().strip())


class QueryNormalizer:
    def __init__(self):
        self.replacements = [
            (r"\bbrt\s*0?1\b", "brt01"),
            (r"\bbx\b", "bến xe"),
            (r"\bđh\b", "đại học"),
            (r"\bcv\b", "công viên"),
            (r"\bbv\b", "bệnh viện"),
            (r"\btttm\b", "trung tâm thương mại"),
            (r"\bkđt\b", "khu đô thị"),
            (r"\bbxbk\b", "bến xe đến bách khoa"),
            (r"\bbk\b", "bách khoa"),
            (r"\bsb\b", "sân bay"),
            (r"\bhn\b", "hà nội"),
            (r"\btphcm\b", "thành phố hồ chí minh"),
            (r"\bhcm\b", "hồ chí minh"),
        ]

    def normalize(self, text: str) -> str:
        text = norm_str(text)
        for pattern, replacement in self.replacements:
            text = re.sub(pattern, replacement, text)
        return text


class IntentClassifier:
    def __init__(self):
        self.normalizer = QueryNormalizer()

    def _clean_entity_text(self, text: str) -> str:
        if not text:
            return ""
        # Strip common prefix noise
        text = re.sub(r"^(?:đi\s+|đón\s+xe\s+|bắt\s+xe\s+|từ\s+)+", "", text, flags=re.IGNORECASE)
        # Strip common trailing query suffixes
        text = re.sub(r"\s*(?:bằng\s+)?(?:xe|tuyến|bus)(?:\s+buýt)?(?:\s+nào|\s+gì)?\??$", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*(?:đi\s+)?(?:xe|tuyến|bus)(?:\s+nào|\s+gì)?\??$", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*(?:thế|nhỉ|với|bạn|ơi|\n|\?)+$", "", text, flags=re.IGNORECASE)
        cleaned = text.strip()
        if cleaned.lower() in ["đâu", "nào", "gì", "mấy"]:
            return ""
        return cleaned

    def classify(self, raw_query: str) -> Tuple[str, IntentResult]:
        normalized = self.normalizer.normalize(raw_query)
        entities = EntityExtract()

        # Strip conversational leading phrases
        cleaned_query = re.sub(r"^(?:tôi\s+muốn\s+|cho\s+(?:tôi\s+)?hỏi\s+|bây\s+giờ\s+|làm\s+sao\s+(?:để\s+)?|cho\s+hỏi\s+|mình\s+muốn\s+|hãy\s+chỉ\s+giúp\s+)", "", normalized, flags=re.IGNORECASE).strip()

        # Standalone specific route ID extraction (e.g. e03, brt01, 32)
        if not entities.route_id:
            specific_route_match = re.search(r"\b(e0[1-9]|brt0?1|[0-9]{1,3}[a-z]?)\b", cleaned_query, flags=re.IGNORECASE)
            if specific_route_match and "đi" in normalized:
                entities.route_id = specific_route_match.group(1).upper()
            elif specific_route_match and re.search(r"\b(e0[1-9]|brt0?1)\b", cleaned_query, flags=re.IGNORECASE):
                # E-bus or BRT usually implies a route even without "đi"
                entities.route_id = specific_route_match.group(1).upper()
        
        # Check for BRT or specific route ID
        brt_match = re.search(r"\bbrt0?1\b", normalized)
        if brt_match:
            entities.route_id = "BRT01"

        # Check for route ID
        if not entities.route_id:
            route_match = re.search(r"(?:tuyến(?: xe buýt)?\s*số|xe buýt\s*số|tuyến|xe|bus|số)\s*(e?[0-9]{1,3}[a-z]*)", cleaned_query, flags=re.IGNORECASE)
            if route_match:
                entities.route_id = route_match.group(1).upper()

        # Extract Origin & Destination with multiple flexible patterns
        from_to_match = re.search(r"từ\s+(.+?)\s+(?:đến|về|sang|tới|qua|đi)\s+(.+)", cleaned_query)
        if from_to_match:
            o_cand = self._clean_entity_text(from_to_match.group(1))
            d_cand = self._clean_entity_text(from_to_match.group(2))
            if o_cand and d_cand:
                entities.origin = o_cand
                entities.destination = d_cand
        
        if not entities.origin or not entities.destination:
            dir_to_match = re.search(r"(?:đi|đón\s+xe|bắt\s+xe)\s+(.+?)\s+(?:đến|về|sang|tới|qua)\s+(.+)", cleaned_query)
            if dir_to_match:
                o_cand = self._clean_entity_text(dir_to_match.group(1))
                d_cand = self._clean_entity_text(dir_to_match.group(2))
                if o_cand and d_cand:
                    entities.origin = o_cand
                    entities.destination = d_cand

        if not entities.origin and not entities.destination and not entities.location_keyword:
            via_match = re.search(r"(?:xe|tuyến|bus)(?:\s+buýt)?\s+nào\s+(?:đi\s+qua|đến|tới)\s+(.+)", cleaned_query)
            if via_match:
                entities.location_keyword = self._clean_entity_text(via_match.group(1))

        if not entities.origin and not entities.destination and not entities.location_keyword:
            qua_match = re.search(r"(?:qua|đến|tới)\s+(.+)", cleaned_query)
            if qua_match:
                entities.location_keyword = self._clean_entity_text(qua_match.group(1))

        # Intent Decision Rules
        intent_label = "UNKNOWN"
        confidence = 0.95

        if any(w in normalized for w in ["mất đồ", "quên đồ", "thất lạc", "tổng đài", "hotline", "1900"]):
            intent_label = "LOST_FOUND_QUERY"
        elif any(w in normalized for w in ["app", "ứng dụng", "thanh toán", "timbus", "vneid", "quẹt thẻ", "mã qr", "nạp tiền", "thẻ ngân hàng"]):
            intent_label = "APP_QUERY"
        elif any(w in normalized for w in ["tham quan", "du lịch", "danh lam thắng cảnh", "tourist"]):
            intent_label = "TOURIST_QUERY"
        elif any(w in normalized for w in ["bến xe", "điểm trung chuyển"]) and any(w in normalized for w in ["ở đâu", "chỗ nào", "nằm ở", "địa chỉ"]):
            intent_label = "STATION_QUERY"
        elif any(w in normalized for w in ["metro", "tàu điện", "cát linh", "nhổn", "ga trên cao", "suối tiên"]):
            intent_label = "METRO_QUERY"
        elif any(w in normalized for w in ["giá vé", "bao nhiêu tiền", "vé tháng", "vé lượt", "miễn phí", "ưu đãi", "sinh viên"]):
            intent_label = "FARE_QUERY"
        elif any(w in normalized for w in ["buổi tối", "mấy giờ", "giờ chạy", "hoạt động", "tần suất", "chuyến cuối", "tết", "cuối tuần", "ngày lễ"]):
            intent_label = "SCHEDULE_QUERY"
        elif any(w in normalized for w in ["quy định", "hành lý", "trẻ em", "người cao tuổi", "pháp luật", "chó mèo", "thú cưng", "xe đạp"]):
            intent_label = "RULE_QUERY"
        elif entities.origin or entities.destination or entities.route_id:
            intent_label = "ROUTE_QUERY"
        elif entities.location_keyword:
            if any(phrase in normalized for phrase in [
                "đi qua", "tuyến nào", "xe nào", "gần nhất", "đến", "tới",
                "bắt xe", "lên xe", "chuyển tuyến"
            ]):
                intent_label = "ROUTE_QUERY"
        elif any(phrase in normalized for phrase in [
            "tuyến nào", "xe buýt nào", "đi từ", "từ ", "bắt xe",
            "chuyến xe", "chuyển tuyến", "tuyến xe"
        ]):
            intent_label = "ROUTE_QUERY"

        intent_res = IntentResult(
            intent_label=intent_label,
            confidence=confidence,
            entities=entities
        )
        return normalized, intent_res
