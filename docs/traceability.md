# Ma Trận Truy Vết Yêu Cầu (Traceability Matrix)

Ma trận này ánh xạ các yêu cầu thiết kế hệ thống từ đồ án với các mô-đun mã nguồn thực tế và test case tương ứng để đảm bảo tính toàn vẹn của thiết kế.

| Yêu Cầu (Requirement) | Mô-đun Triển Khai (Module) | Test Case Ánh Xạ | Trạng Thái |
|----------------------|---------------------------|-------------------|------------|
| REQ-01: Hệ thống hoạt động hoàn toàn ngoại tuyến khi mất Internet | `edge_ai/offline_pipeline.py`, `backend/main.py` | `test_offline_audit.py`, `test_offline_mode.py` | ✅ Hoàn thành |
| REQ-02: Phân loại ý định người dùng thành các danh mục cố định | `edge_ai/intent_classifier.py` | `tests/benchmark/run_benchmark.py` | ✅ Hoàn thành |
| REQ-03: Tìm kiếm ngữ nghĩa với Vector RAG / FTS5 | `rag/local_retriever.py`, `rag/chroma_store.py` | `tests/evaluate_rag.py` | ✅ Hoàn thành |
| REQ-04: Ngăn chặn ảo giác thông tin (Hallucination) cho các query nhạy cảm | `edge_ai/validator.py` | `tests/benchmark/run_benchmark.py` (Fare/Schedule check) | ✅ Hoàn thành |
| REQ-05: Giao diện Kiosk hiển thị bản đồ mà không cần Internet | `kiosk_ui/index.html` (Local tiles fallback) | Kiểm tra thủ công ngắt mạng | ✅ Hoàn thành |
| REQ-06: Phát hiện sự cố mạng và chuyển đổi mô hình (Failover) | `sync_service/network_monitor.py` | `backend/main.py` (/api/toggle-network) | ✅ Hoàn thành |
| REQ-07: Bảo mật hệ thống chống lại Prompt Injection & SQL Injection | `shared/security.py` | `tests/test_e2e_production.py` (Security tests) | ✅ Hoàn thành |
| REQ-08: Quản lý ngữ cảnh phiên hội thoại người dùng (Multi-turn) | `edge_ai/session_manager.py` | `tests/test_offline_mode.py` | ✅ Hoàn thành |
| REQ-09: Dashboard hiển thị tham số hệ thống theo thời gian thực | `admin_ui/index.html`, `/api/status` | Kiểm tra thủ công | ✅ Hoàn thành |
