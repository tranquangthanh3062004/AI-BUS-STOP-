"""
tests/benchmark/test_offline_audit.py
Kiểm toán ngoại tuyến: Đảm bảo khi ngắt mạng hoàn toàn,
hệ thống vẫn có thể phân tích ý định và trả lời nhờ SQLite + Local LLM Fallback.
"""
import os
import sys
import unittest
from unittest.mock import patch
import socket

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from edge_ai.offline_pipeline import OfflineAIAssistant
from shared.schemas import QueryRequest

# Fake socket để chặn mọi kết nối Internet
class BlockedSocket:
    def __init__(self, *args, **kwargs):
        raise socket.error("Network is unreachable (Offline Audit Mode)")

class TestOfflineAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assistant = OfflineAIAssistant()

    @patch('socket.socket', new=BlockedSocket)
    def test_offline_fare_query(self):
        req = QueryRequest(raw_text="Giá vé xe buýt Hà Nội là bao nhiêu?")
        res = self.assistant.process_query(req)
        self.assertIn(res.status, ["success", "fallback"])
        self.assertEqual(res.intent, "FARE_QUERY")
        self.assertGreater(len(res.answer_text), 10)

    @patch('socket.socket', new=BlockedSocket)
    def test_offline_route_query(self):
        req = QueryRequest(raw_text="Tuyến 32 chạy từ đâu đến đâu?")
        res = self.assistant.process_query(req)
        self.assertIn(res.status, ["success", "fallback"])
        self.assertEqual(res.intent, "ROUTE_QUERY")
        self.assertTrue(len(res.answer_text) > 10)

if __name__ == "__main__":
    unittest.main()
