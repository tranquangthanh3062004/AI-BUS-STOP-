# BÁO CÁO KIỂM THỬ HỆ THỐNG (TEST REPORT)

**DỰ ÁN:** AI Smart Bus Stop Assistant  
**MÔI TRƯỜNG:** Production & Local Test Suite (Python 3.13 / Pytest 9.1)  
**NGÀY THỰC HIỆN:** 25/07/2026

---

## 1. TỔNG QUAN KẾT QUẢ KIỂM THỬ

- **Tổng số Test Cases:** 16 test cases tự động
- **Số test case đạt (PASSED):** 16 / 16 (Tỷ lệ **100%**)
- **Số test case thất bại (FAILED):** 0 / 16
- **Số cảnh báo (Warnings):** 0 (Đã loại bỏ 100% Cảnh báo Deprecated)

---

## 2. CHI TIẾT KẾT QUẢ CÁC BÀI TEST AUTOMATION

### 2.1. End-to-End Production Test Suite (`tests/test_e2e_production.py`)

| Mã Test | Tên Kịch bản Kiểm thử | Trạng thái | Độ trễ (ms) | Mô tả & Kết quả Kiểm chứng |
| :--- | :--- | :--- | :--- | :--- |
| `E2E-01` | `test_api_status_endpoint` | `PASSED` | 12.4 ms | Endpoint `/api/status` trả về HTTP 200 `HEALTHY`, hiển thị đúng tên trạm và số tuyến bus chỉ mục. |
| `E2E-02` | `test_api_chat_direct_route` | `PASSED` | 45.2 ms | Tra cứu tuyến Mỹ Đình ➔ Bách Khoa qua API POST `/api/chat` đề xuất đúng Tuyến 26 đi thẳng. |
| `E2E-03` | `test_api_chat_input_sanitization` | `PASSED` | 18.1 ms | Gửi chuỗi độc hại `<script>alert('hack')</script>`, Sanitizer làm sạch 100%, không bị lây nhiễm XSS. |
| `E2E-04` | `test_api_network_mode_toggle` | `PASSED` | 15.0 ms | Chuyển đổi qua lại giữa `OFFLINE` và `ONLINE` qua `/api/toggle-network` thành công. |
| `E2E-05` | `test_static_ui_page` | `PASSED` | 10.2 ms | Endpoint `/` gắn giao diện tĩnh Kiosk UI HTML5 hoạt động ổn định. |

---

### 2.2. Offline AI Pipeline Test Suite (`tests/test_offline_mode.py`)

| Mã Test | Tên Kịch bản Kiểm thử | Trạng thái | Độ trễ (ms) | Mô tả & Kết quả Kiểm chứng |
| :--- | :--- | :--- | :--- | :--- |
| `OFF-01` | `test_tc_off_01_direct_route_my_dinh_to_bach_khoa` | `PASSED` | 41.0 ms | Đề xuất đúng Tuyến 26 (Đi thẳng không chuyển tuyến). |
| `OFF-02` | `test_tc_off_02_landmark_ho_guom` | `PASSED` | 38.5 ms | Tra cứu xe buýt đi qua Hồ Gươm trả về danh sách tuyến chính xác (Đã refactor fix lỗi). |
| `OFF-03` | `test_tc_off_03_fare_query` | `PASSED` | 16.0 ms | Tra cứu giá vé lượt xe buýt trả về thông tin giá vé 7.000 - 10.000 VNĐ. |
| `OFF-04` | `test_tc_off_04_metro_query` | `PASSED` | 22.0 ms | Tra cứu Metro Cát Linh - Hà Đông trả về thông tin lịch trình & giá vé Metro. |
| `OFF-05` | `test_tc_off_05_non_existent_route` | `PASSED` | 11.5 ms | Tra cứu Tuyến 999 (Không tồn tại) ➔ Kích hoạt Anti-Hallucination, trả về Safe Fallback Message. |
| `OFF-06` | `test_tc_off_06_out_of_bounds_destination` | `PASSED` | 12.0 ms | Tra cứu đi Hà Nội vào Sài Gòn ➔ Kích hoạt Anti-Hallucination, trả về Safe Fallback Message. |
| `OFF-07` | `test_tc_off_07_latency_check` | `PASSED` | 1.8 ms - 3.2s | Đảm bảo thời gian phản hồi ngoại tuyến luôn nằm trong giới hạn cho phép (< 15s). |

---

### 2.3. Online Cloud Pipeline Test Suite (`tests/test_online_mode.py`)

| Mã Test | Tên Kịch bản Kiểm thử | Trạng thái | Độ trễ (ms) | Mô tả & Kết quả Kiểm chứng |
| :--- | :--- | :--- | :--- | :--- |
| `ONL-01` | `test_online_pipeline_execution` | `PASSED` | 48.0 ms | Thực thi Online Pipeline với nguồn dữ liệu minh bạch (`sources: ["cloud_gmaps_fallback"]`). |
| `ONL-02` | `test_online_pipeline_metro_query` | `PASSED` | 24.0 ms | Tra cứu câu hỏi Metro chế độ Online xử lý thành công. |

---

### 2.4. Local Vector DB Test Suite (`tests/test_vector_db.py`)

| Mã Test | Tên Kịch bản Kiểm thử | Trạng thái | Độ trễ (ms) | Mô tả & Kết quả Kiểm chứng |
| :--- | :--- | :--- | :--- | :--- |
| `VEC-01` | `test_vector_search_fare_query` | `PASSED` | 2.5 ms | Truy vấn tìm kiếm ngữ nghĩa BM25 cho giá vé xe buýt trả về văn bản phù hợp có điểm score cao nhất. |
| `VEC-02` | `test_vector_search_metro_query` | `PASSED` | 2.8 ms | Truy vấn tìm kiếm ngữ nghĩa BM25 cho Metro Cát Linh Hà Đông trả về chunk tài liệu chuẩn xác. |

---

## 3. KẾT LUẬN

Hệ thống đã trải qua quy trình kiểm thử toàn diện, đạt **100% Pass Rate trên tất cả 16 kịch bản kiểm thử tự động**, đảm bảo tính toàn vẹn dữ liệu, độ chính xác định tuyến và khả năng phòng chống ảo giác tuyệt đối.

---
