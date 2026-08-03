# Yêu Cầu Hệ Thống & Môi Trường (System Requirements)

Tài liệu này mô tả cấu hình phần cứng tối thiểu và môi trường phần mềm cần thiết để triển khai hệ thống **AI Smart Bus Stop Assistant** tại Kiosk trạm dừng xe buýt, dựa trên kiến trúc Offline RAG và Local LLM.

## 1. Yêu Cầu Phần Cứng (Hardware Requirements)

Vì hệ thống cần chạy mô hình ngôn ngữ lớn (LLM) cục bộ để đảm bảo hoạt động khi mất mạng, phần cứng yêu cầu phải có khả năng xử lý AI cơ bản.

### 1.1. Cấu Hình Tối Thiểu (Chỉ chạy mô hình nhỏ như Llama-3 8B lượng tử hóa)
*   **CPU:** Intel Core i5 (thế hệ 10+) hoặc AMD Ryzen 5.
*   **RAM:** Tối thiểu 16GB (Khuyến nghị 24GB nếu không có GPU).
*   **GPU:** Không bắt buộc, nhưng nếu có sẽ tăng tốc độ phản hồi (NVIDIA GTX 1660 6GB VRAM hoặc tương đương).
*   **Storage:** 256GB SSD (để lưu trữ OS, DB cục bộ, và file weights của mô hình).
*   **Audio:** Microphone đa hướng chống ồn (để bắt giọng nói) & Loa phát thanh.
*   **Display:** Màn hình cảm ứng cường lực chống chói ngoài trời (Outdoor Kiosk Display).

### 1.2. Cấu Hình Khuyến Nghị (Chạy mượt mà, độ trễ thấp <2s)
*   **CPU:** Intel Core i7 hoặc AMD Ryzen 7.
*   **RAM:** 32GB DDR4/DDR5.
*   **GPU:** NVIDIA RTX 3060 12GB VRAM hoặc RTX 4060 8GB VRAM (để tải toàn bộ model vào VRAM).
*   **Storage:** 512GB NVMe SSD.

## 2. Môi Trường Phần Mềm (Software Environment)

*   **Hệ Điều Hành (OS):** Ubuntu 22.04 LTS hoặc Windows 11/10 IoT Enterprise. (Khuyến nghị Ubuntu để tối ưu hiệu năng AI).
*   **Python:** Python 3.11.x (Yêu cầu phiên bản >=3.10).
*   **Trình Điều Khiển (Drivers):** NVIDIA CUDA Toolkit 11.8+ (Nếu sử dụng GPU NVIDIA).
*   **LLM Runtime:** Ollama (được cài đặt như một service chạy nền hệ thống).
*   **Vector Database:** ChromaDB (được nhúng qua thư viện Python).
*   **Trình Duyệt Kiosk:** Google Chrome hoặc Chromium chạy ở chế độ Kiosk mode (`--kiosk`).

## 3. Kiến Trúc Triển Khai (Deployment Architecture)

*   Hệ thống Backend (FastAPI) sẽ chạy như một Service Systemd (trên Linux) hoặc Windows Service.
*   Trạm sẽ kết nối Internet qua 4G/LTE Router. Trong trường hợp mất sóng, Backend sẽ tự động chuyển đổi sang Local LLM và Local Database.
*   Việc cập nhật (OTA Updates) cho cơ sở dữ liệu vé, lộ trình (SQLite) và VectorDB (ChromaDB) được thực hiện ngầm vào ban đêm (01:00 AM - 04:00 AM) khi có kết nối mạng.
