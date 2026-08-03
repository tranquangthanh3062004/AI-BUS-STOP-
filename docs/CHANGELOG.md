# CHANGELOG - AI Smart Bus Stop Assistant

Tất cả những thay đổi quan trọng đối với dự án **AI Smart Bus Stop Assistant** sẽ được ghi nhận tại đây.

---

## [2.0.0-production] - 2026-07-25

### 🚀 Nâng cấp & Tính năng mới (Added)
- **Online Cloud AI Pipeline (`backend/online_pipeline.py`)**: Đã xây dựng hoàn chỉnh luồng xử lý Online Cloud tuân thủ chuẩn: *Intent Classifier $\rightarrow$ Google Maps / Transit API $\rightarrow$ Cloud RAG $\rightarrow$ Cloud LLM $\rightarrow$ Answer Validator $\rightarrow$ Formatter*. Hỗ trợ tự động fallback mượt mà về Offline Pipeline khi rớt mạng hoặc thiếu API key.
- **Local Semantic Vector Index (`vector_db/local_vector_index.py`)**: Xây dựng engine tìm kiếm chỉ mục Vector / BM25 cục bộ không phụ thuộc thư viện bên ngoài, lưu trữ chỉ mục tại `vector_db/local_index.json`.
- **Background Network Monitor (`sync_service/network_monitor.py`)**: Tích hợp dịch vụ chạy ngầm tự động kiểm tra kết nối Internet (TCP Socket Ping `8.8.8.8`) để thực hiện Auto Failover giữa Online và Offline mode.
- **Quản lý Prompt Tập trung (`prompts/`)**: Đã tách toàn bộ Prompt mã hóa cứng ra các file mẫu `prompts/system_prompt_kiosk.txt` và `prompts/system_prompt_online.txt`.
- **Hệ thống Toast Notification & Offline Fallback cho Kiosk UI (`kiosk_ui/index.html`)**: Thêm giao diện thông báo Toast, hiển thị thông báo bản đồ ngoại tuyến khi không tải được Tile Leaflet.

### 🛠️ Sửa lỗi & Tối ưu hóa (Fixed & Refactored)
- **Sửa triệt để lỗi tra cứu tuyến buýt theo địa danh (Hồ Gươm)**: Nâng cấp `LocalTransitGraph.search_routes_by_keyword()` trong `edge_ai/transit_graph.py` kết hợp truy vấn bảng `route_stops` và mở rộng từ khóa alias.
- **Tối ưu hóa Lớp kiểm duyệt Chống Ảo giác (`edge_ai/validator.py`)**: Nâng cấp `AnswerValidator` trích xuất và kiểm tra tất cả mã số tuyến xe xuất hiện trong văn bản trả lời do LLM sinh ra, loại bỏ nguy cơ LLM bịa đặt mã tuyến.
- **Khắc phục 100% Cảnh báo Deprecated**:
  - Chuyển `shared/config.py` sang Pydantic v2 `pydantic_settings.SettingsConfigDict`.
  - Thay thế `@app.on_event("startup")` trong `backend/main.py` bằng async `lifespan` handler.
- **Mở rộng Test Suite (`tests/`)**: Bổ sung `test_online_mode.py` và `test_vector_db.py`, nâng số lượng test case tự động từ 12 lên 16 bài test với tỷ lệ đạt 100%.

---
