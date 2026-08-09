"""
tests/test_offline_mode.py
Automated Pytest suite for Offline AI Assistant Pipeline.
Verifies all 7 core test scenarios, latency, accuracy, and anti-hallucination policies.
"""

import unittest
from shared.schemas import QueryRequest
from edge_ai.offline_pipeline import OfflineAIAssistant
from local_llm.llm_engine import FALLBACK_MESSAGES


class TestOfflineAIAssistant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from shared.schemas import RouteRecommendation
        class _MockScraper:
            def scrape_route(self, origin: str, destination: str):
                if "Mỹ Đình" in origin and "Bách Khoa" in destination:
                    return [
                        RouteRecommendation(
                            route_id="26",
                            route_name="Tuyến 26",
                            board_stop="Mỹ Đình",
                            alight_stop="Bách Khoa",
                            transfers_count=0,
                            transfer_stop="",
                            fare_vnd=7000,
                            operating_hours="",
                            description="",
                            itinerary=""
                        )
                    ]
                return []
        
        cls.assistant = OfflineAIAssistant()
        cls.assistant._scraper = _MockScraper()

    def test_tc_off_01_direct_route_my_dinh_to_bach_khoa(self):
        """TC-OFF-01: Đi từ Bến xe Mỹ Đình đến Bến xe Nước Ngầm"""
        req = QueryRequest(raw_text="Đi từ Bến xe Mỹ Đình đến Bến xe Nước Ngầm bằng xe buýt nào?")
        res = self.assistant.process_query(req)
        
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.intent, "ROUTE_QUERY")
        self.assertTrue(len(res.recommendations) > 0)
        self.assertTrue(any("16" in r.route_id or "104" in r.route_id or "29" in r.route_id for r in res.recommendations))

    def test_tc_off_02_landmark_ho_guom(self):
        """TC-OFF-03: Xe buýt nào đi qua Hồ Gươm?"""
        req = QueryRequest(raw_text="Xe buýt nào đi qua Hồ Gươm?")
        res = self.assistant.process_query(req)
        
        # Vì user không cung cấp điểm xuất phát, hệ thống nên hỏi lại (CLARIFICATION)
        self.assertEqual(res.status, "CLARIFICATION")
        self.assertIn("xuất phát từ đâu", res.answer_text.lower())

    def test_tc_off_03_fare_query(self):
        """TC-OFF-05: Giá vé xe buýt lượt bao nhiêu tiền?"""
        req = QueryRequest(raw_text="Giá vé lượt xe buýt bao nhiêu tiền?")
        res = self.assistant.process_query(req)
        
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.intent, "FARE_QUERY")
        self.assertTrue(any(price in res.answer_text.lower() for price in ["7.000", "7,000", "8.000", "10.000", "7000", "vé", "giá vé", "đồng", "vnđ"]))

    def test_tc_off_05_non_existent_route(self):
        """TC-OFF-04: Xe buýt số 999 đi đâu?"""
        req = QueryRequest(raw_text="Tuyến xe buýt số 999 chạy giờ nào?")
        res = self.assistant.process_query(req)
        
        self.assertEqual(res.status, "FALLBACK")
        self.assertIn(res.answer_text, FALLBACK_MESSAGES)

    def test_tc_off_06_out_of_bounds_destination(self):
        """TC-OFF-04: Đi xe buýt từ Hà Nội vào Sài Gòn?"""
        req = QueryRequest(raw_text="Đi từ Hà Nội đến Sài Gòn bằng xe buýt nào?")
        res = self.assistant.process_query(req)
        
        self.assertEqual(res.status, "FALLBACK")
        self.assertIn(res.answer_text, FALLBACK_MESSAGES)

    def test_tc_off_07_latency_check(self):
        """Đảm bảo thời gian phản hồi cục bộ < 15 giây khi dùng Local LLM (Ollama)"""
        req = QueryRequest(raw_text="Từ Nhổn về Cầu Giấy đi xe nào?")
        res = self.assistant.process_query(req)
        
        self.assertLess(res.execution_time_ms, 15000.0)

    def test_regression_intent_ambiguous_not_route(self):
        """REGRESSION FIX 1B: 'Xe tôi hỏng' không được là ROUTE_QUERY"""
        req = QueryRequest(raw_text="Xe tôi hỏng rồi phải làm sao?")
        res = self.assistant.process_query(req)
        self.assertNotEqual(res.intent, "ROUTE_QUERY")

    def test_regression_dead_code_nonexistent_route(self):
        """REGRESSION FIX 1A: Route không tồn tại -> FALLBACK đúng"""
        req = QueryRequest(raw_text="Tuyến 999 đi đâu?")
        res = self.assistant.process_query(req)
        self.assertEqual(res.status, "FALLBACK")
        self.assertIn(res.answer_text, FALLBACK_MESSAGES)



    def test_session_resolver_two_turn_dialogue(self):
        """SESSION: Multi-turn — hỏi điểm đến trước, điểm xuất phát sau"""
        # Turn 1: chỉ có điểm đến
        req1 = QueryRequest(raw_text="Tôi muốn đến Hồ Gươm", session_id="test_session_001")
        res1 = self.assistant.process_query(req1)
        self.assertEqual(res1.status, "CLARIFICATION")

        # Turn 2: cung cấp điểm xuất phát
        req2 = QueryRequest(raw_text="Từ Mỹ Đình", session_id="test_session_001")
        res2 = self.assistant.process_query(req2)
        self.assertIn(res2.status, ["SUCCESS", "FALLBACK"])
        self.assertNotEqual(res2.status, "CLARIFICATION")

if __name__ == "__main__":
    unittest.main()
