# SOFTWARE ARCHITECTURE: Kiến trúc Phần mềm Nhúng

Tài liệu này bao gồm **Phase 9: Software Architecture** trong lộ trình 20 Phases của dự án. 

---

## PHASE 9: SOFTWARE ARCHITECTURE (Kiến trúc Phần mềm)

### 9.1. Phase Metadata
- **Objective:** Xác định Hệ điều hành (OS), Runtime, và cơ chế Quản lý tiến trình (Process Management) để Kiosk vận hành ổn định trong điều kiện không có sự can thiệp của con người.
- **Input:** Cấu hình phần cứng NVIDIA Jetson (Phase 8).
- **Output:** Software Stack Diagram, OS Configurations.
- **Dependencies:** Phase 8.
- **Deliverables:** Mô tả luồng xử lý phần mềm cấp thấp.
- **Risks:** Ứng dụng AI bị rò rỉ bộ nhớ (Memory Leak), chạy liên tục 3 ngày sẽ làm cạn kiệt 8GB RAM và treo máy (Kernel Panic).
- **Acceptance Criteria:** Bắt buộc có cơ chế Docker Container Limits và Hardware Watchdog Timer (WDT) để tự reboot hệ thống.

### 9.2. Engineering Standard: Lựa chọn Hệ điều hành (OS)

| OS | Vì sao chọn? | Lựa chọn thay thế | Ưu điểm | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **BalenaOS / Ubuntu Core** | **(Lựa chọn chính thức)**. Kiến trúc Immutable OS (Hệ điều hành bất biến). Quản lý mọi thứ dưới dạng Container. Có cơ chế Rollback A/B Partition khi OTA lỗi. | Ubuntu 22.04 LTS (Desktop/Server) | Siêu an toàn. Nếu cập nhật hệ điều hành thất bại do cúp điện, máy tự khởi động lại vào phiên bản cũ (Phân vùng B). Không bao giờ bị "Brick". | Khó dev hơn môi trường Linux thông thường. Hệ thống file Read-Only. | Các dự án Web Backend thông thường (Trên Cloud). |
| **Ubuntu 22.04 LTS** | Bị loại bỏ. OS có quyền Read/Write tự do, dễ bị lỗi hệ thống file khi tắt nóng (Hard Power-off). Dễ dính mã độc nếu bị xâm nhập. | Yocto Linux | Dễ cài đặt, thư viện AI (CUDA, TensorRT) hỗ trợ tốt nhất. | Khi nâng cấp gói `apt update` dễ gây vỡ Dependency, làm hỏng Kiosk. | Không dùng cho thiết bị IoT/Edge không có người trực (Unattended Devices). |

### 9.3. Kiến trúc Container (Container Architecture)
Thay vì chạy app trực tiếp trên OS, hệ thống chạy 4 microservices nội bộ bằng **Docker** (kích hoạt `restart: always` và `oom_kill_disable: false`):
1. **Edge-AI-Core (Port 8000):** Tải Llama-3-8B vào VRAM. Chạy API Server (FastAPI). Giới hạn RAM: 5GB.
2. **Speech-Engine (Port 8001):** Tải Whisper (STT) và Piper (TTS). Chạy TCP Socket siêu nhanh. Giới hạn RAM: 1.5GB.
3. **Kiosk-UI (Port 80):** Trình duyệt Chromium chạy chế độ Kiosk (Fullscreen, no flags). Chứa SPA React. Giới hạn RAM: 500MB.
4. **IoT-Agent (Port 1883):** Daemon viết bằng Rust, giao tiếp GPIO, đọc cảm biến và sync dữ liệu qua MQTT. Giới hạn RAM: 100MB.

### 9.4. Cơ chế Hardware Watchdog
Sử dụng bộ định thời phần cứng (WDT) tích hợp trên bo mạch Jetson. `IoT-Agent` phải ghi một tín hiệu vào tệp `/dev/watchdog` mỗi 10 giây (Quá trình này gọi là "pet the dog" - nựng chó).
- Nếu `IoT-Agent` (hoặc OS) bị treo, nó không ghi tín hiệu kịp.
- Quá 60 giây, Chip điện tử (phần cứng) sẽ tự động cắt nguồn và kích hoạt Reboot nóng. Đảm bảo Kiosk luôn sống lại.

---

## 🔁 SELF REVIEW LOOP (Phase 9)

> [!NOTE]
> **Vai trò: Principal DevOps Engineer**
> - *Điểm mạnh:* Cơ chế Watchdog và Immutable OS (Ubuntu Core) là chuẩn công nghiệp tối cao cho IoT, khắc phục hoàn toàn nỗi ám ảnh "cử nhân viên kỹ thuật lái xe 20km ra trạm để bấm nút Restart".
> - *Rủi ro:* Mặc dù Docker giới hạn RAM, nhưng Disk Space (Dung lượng ổ cứng) có thể bị đầy do Kiosk sinh Log liên tục sau 1 năm hoạt động.
> - *Cải tiến:* Yêu cầu bắt buộc cấu hình Log Rotation (Cắt log) ở cấp độ Docker daemon (`max-size: "10m", max-file: "3"`). Bổ sung `tmpfs` (RAM Disk) cho các thư mục cache tạm thời để tránh làm mòn (Wear-out) bộ nhớ flash eMMC.

> **Trạng thái Phase 9:** ✅ Đã thông qua Quality Gate. 
