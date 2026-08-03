# SYSTEM ARCHITECTURE: Kiến trúc Tổng thể & Lựa chọn Công nghệ

Tài liệu này bao gồm **Phase 4: System Architecture** và **Phase 7: Technology Selection** trong lộ trình 20 Phases của dự án. 

---

## PHASE 4: SYSTEM ARCHITECTURE (Thiết kế Kiến trúc Tổng thể)

### 4.1. Phase Metadata
- **Objective:** Xác định mô hình kiến trúc High-Level phân bổ vai trò rõ ràng giữa thiết bị ngoại vi tại trạm (Edge Device) và Đám mây trung tâm (Cloud Platform).
- **Input:** Ma trận yêu cầu từ Phase 2 (Ranh giới Online/Offline, Độ trễ < 1.5s).
- **Output:** Sơ đồ luồng dữ liệu kiến trúc Microservices lai (Hybrid Microservices).
- **Dependencies:** Báo cáo từ Phase 2.
- **Deliverables:** Mô hình kiến trúc phần mềm phân tán.
- **Risks:** Nghẽn cổ chai (Bottleneck) khi chuyển đổi trạng thái giữa Online và Offline do Timeout từ Cloud.
- **Acceptance Criteria:** Cơ chế chuyển đổi (Failover) từ Online xuống Offline phải xảy ra trong vòng < 0.5 giây.

### 4.2. Khối Kiến trúc cốt lõi (Core Architecture Blocks)

1. **Edge Intelligence Layer (Lớp Biên):**
   - Đóng vai trò là "Bộ não cục bộ". Kiosk chạy 4 container chính: `Kiosk-UI`, `Local-STT-TTS`, `Local-LLM-Inference`, `Sync-Agent`.
   - **Cơ chế Failover:** `Sync-Agent` định kỳ PING lên Cloud (mỗi 5 giây). Nếu 2 lần PING thất bại, lập tức set cờ `OFFLINE_MODE = TRUE` vào Redis nội bộ. UI sẽ ngay lập tức vô hiệu hóa các nút gọi Cloud.

2. **Network Layer (Lớp Mạng truyền tải):**
   - Sử dụng **MQTT (Message Queuing Telemetry Transport)** thay vì HTTP cho việc truyền tải thông số (Telemetry) và nhận lệnh từ Cloud. MQTT với cờ `QoS=1` đảm bảo tin nhắn không bị mất khi sóng 4G chập chờn.

3. **Cloud Control Plane (Lớp Điều khiển Đám mây):**
   - Kế thừa hệ thống `AI Transportation Assistant` hiện hành. Nơi đây đóng vai trò là "Global Knowledge" và "Device Manager".

---

## PHASE 7: TECHNOLOGY SELECTION (Lựa chọn Stack Công nghệ)

### 7.1. Phase Metadata
- **Objective:** Quyết định chính xác các công cụ, Framework, Ngôn ngữ lập trình được sử dụng để hiện thực hóa Kiến trúc.
- **Input:** Kiến trúc từ Phase 4, Hạn chế phần cứng.
- **Output:** Danh sách Technology Stack chốt hạ.
- **Dependencies:** Phase 4.
- **Deliverables:** Ma trận so sánh công nghệ và Lý do lựa chọn (Engineering Standard).

### 7.2. Engineering Standard: Ma trận Lựa chọn Công nghệ

| Thành phần | Lựa chọn (Được chọn) | Lựa chọn thay thế | Vì sao chọn? (Ưu điểm) | Hạn chế | Khi nào Không nên dùng? |
|---|---|---|---|---|---|
| **Local LLM Engine** | **llama.cpp** | Ollama, vLLM | Viết bằng C/C++, biên dịch trực tiếp không qua máy ảo, tối ưu hoá cực mạnh cho CPU/NPU thiết bị nhúng. | Khó cấu hình hơn Ollama. API server đi kèm khá cơ bản. | Khi có Server GPU công suất lớn (Nên dùng vLLM). |
| **Local RAG VectorDB** | **ChromaDB** | FAISS, Pinecone (Cloud) | Hỗ trợ lưu trữ trực tiếp bằng file SQLite. Dễ dàng copy/paste file SQLite này từ Cloud xuống Edge để đồng bộ (Zero-downtime update). | Khả năng scale hàng tỷ vector kém hơn FAISS. | Hệ thống RAG cấp quốc gia. Nhưng với bán kính 5km của Kiosk thì Chroma là hoàn hảo. |
| **Giao thức đồng bộ** | **MQTT** | HTTP REST, gRPC | Trọng lượng gói tin siêu nhẹ (chỉ vài byte header). Tiết kiệm tối đa dung lượng SIM 4G. | Yêu cầu phải cài đặt MQTT Broker (Mosquitto) trên Cloud. | Truyền tải file lớn (File nén Database thì phải dùng HTTPS). |
| **Ngôn ngữ lõi (Edge)** | **Python & C++** | Go, Rust | Tích hợp hoàn hảo với hệ sinh thái AI (LangChain, llama.cpp python bindings). C++ dùng cho STT/TTS để ép độ trễ. | Python tốn RAM hơn Rust/Go. Cần tối ưu kỹ Garbage Collector. | Làm các Service Network thuần túy thì nên dùng Go. |

---

## 🔁 SELF REVIEW LOOP (Phase 4 & 7)

> [!NOTE]
> **Vai trò: Principal Software Architect**
> - *Điểm mạnh:* Việc chọn ChromaDB để lưu dưới dạng file SQLite và Sync qua HTTPS, trong khi telemetry Sync qua MQTT là sự phân chia rành mạch giữa dữ liệu tĩnh và dữ liệu động.
> - *Rủi ro:* Kiosk PING mỗi 5 giây qua HTTPS sẽ làm tốn Pin và dung lượng data rất lớn sau 1 tháng.
> - *Cải tiến:* Đã loại bỏ PING HTTP. Sử dụng cơ chế `Keep-Alive` của kết nối MQTT. Nếu MQTT Disconnected thì kích hoạt `OFFLINE_MODE`. 

> [!NOTE]
> **Vai trò: Principal AI Engineer**
> - *Điểm mạnh:* Lựa chọn `llama.cpp` là chính xác tuyệt đối cho thiết bị nghèo nàn tài nguyên như Edge Device.
> - *Rủi ro:* llama.cpp chạy mô hình Tiếng Việt có thể bị lỗi font chữ hoặc sai tokenization nếu không cài đặt đúng bộ mã UTF-8.
> - *Cải tiến:* Yêu cầu đưa tham số cấu hình Tokenizer vào thiết kế phần mềm ở Phase 9 để giải quyết triệt để lỗi này.

> **Trạng thái Phase 4 & 7:** ✅ Đã thông qua Quality Gate. Sẵn sàng tích hợp sang tài liệu cấu trúc thư mục.
