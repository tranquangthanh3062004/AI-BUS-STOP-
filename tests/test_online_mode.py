"""
tests/test_online_mode.py
Automated test suite for Online AI Pipeline & Network Switch Mode.
"""

import unittest
from shared.schemas import QueryRequest
from backend.online_pipeline import OnlineAIAssistant
from edge_ai.offline_pipeline import OfflineAIAssistant


class TestOnlineAIAssistant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.offline = OfflineAIAssistant()
        cls.online = OnlineAIAssistant(offline_assistant=cls.offline)

    def test_online_pipeline_execution(self):
        """Test Online Pipeline execution with fallback handling"""
        req = QueryRequest(raw_text="Đi từ Bến xe Mỹ Đình đến Đại học Bách Khoa bằng xe buýt nào?")
        res = self.online.process_query(req)
        
        self.assertEqual(res.status, "SUCCESS")
        self.assertFalse(res.is_offline_mode)
        self.assertTrue(any(r in res.answer_text for r in ["26", "16", "E03", "21B", "21", "32"]))

    def test_online_pipeline_metro_query(self):
        """Test Online Pipeline for Metro Query"""
        req = QueryRequest(raw_text="Tuyến Metro Cát Linh Hà Đông giá vé thế nào?")
        res = self.online.process_query(req)
        
        self.assertIn(res.status, ["SUCCESS", "FALLBACK"])
        self.assertFalse(res.is_offline_mode)


if __name__ == "__main__":
    unittest.main()
